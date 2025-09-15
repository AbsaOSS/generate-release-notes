#
# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This module contains the DefaultRecordFactory class which is responsible for generating
"""

import logging
from typing import cast, Optional

from github import Github
from github.Issue import Issue, SubIssue
from github.Label import Label
from github.PullRequest import PullRequest

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.model.record import Record
from release_notes_generator.record.factory.default_record_factory import DefaultRecordFactory

from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.pull_request_utils import get_issues_for_pr, extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


# TODO - code review - check if it beneficial to inherit from DefaultRecordFactory
class IssueHierarchyRecordFactory(DefaultRecordFactory):
    """
    A class used to generate records for release notes.
    """

    def generate(self, github: Github, data: MinedData) -> dict[int | str, Record]:
        """
        Generate records for release notes.
        Parameters:
            github (GitHub): The GitHub instance to generate records for.
            data (MinedData): The MinedData instance containing repository, issues, pull requests, and commits.
        Returns:
            dict[int|str, Record]: A dictionary of records where the key is the issue or pull request number.
        """

        def register_pull_request(pull: PullRequest, skip_rec: bool) -> Optional["IssueRecord"]:
            detected_issues = extract_issue_numbers_from_body(pull)
            logger.debug("Detected issues - from body: %s", detected_issues)
            detected_issues.update(safe_call(get_issues_for_pr)(pull_number=pull.number))
            logger.debug("Detected issues - final: %s", detected_issues)

            for parent_issue_number in detected_issues:
                # try to find an issue record if not present for PR parent
                if parent_issue_number in data_issue_numbers:
                    # find it and register
                    rec = records.get(parent_issue_number)
                    if rec is None:
                        # the parent issue is sub-issue of some hierarchy issue - find the hierarchy issue and register to it
                        for r in records.values():
                            if isinstance(r, HierarchyIssueRecord):
                                rec = cast(HierarchyIssueRecord, r).find_issue(parent_issue_number)
                                if rec is not None:
                                    break

                    if rec is not None and isinstance(rec, PullRequestRecord):
                        continue
                    elif rec is not None and isinstance(rec, IssueRecord):
                        rec.register_pull_request(pull)
                        return rec
                    elif rec is not None and  isinstance(rec, HierarchyIssueRecord):
                        rec.register_pull_request_in_hierarchy(parent_issue_number, pull)
                        return rec

                else:   # parent_issue_number not in data_issue_numbers:
                    logger.warning(
                        "Detected PR %d linked to issue %d which is not in the list of received issues. "
                        "Fetching ...",
                        pull.number,
                        parent_issue_number,
                    )
                    parent_issue = (
                        safe_call(data.repository.get_issue)(parent_issue_number) if data.repository else None
                    )
                    if parent_issue is not None:
                        IssueHierarchyRecordFactory.create_record_for_issue(records, parent_issue)
                        data_issue_numbers.append(parent_issue_number)
                        rec = cast(IssueRecord, records[parent_issue_number])
                        rec.register_pull_request(pull)
                        logger.debug("Registering PR %d: %s to Issue %d", pull.number, pull.title, parent_issue_number)
                        return rec

                # solo PR found (no linked issue found)
                if parent_issue_number not in data_issue_numbers:
                    logger.debug(
                        "Registering stand-alone PR %d: %s as mentioned Issue %d not found.",
                        pull.number,
                        pull.title,
                        parent_issue_number,
                    )
                return None

        records: dict[int | str, Record] = {}
        rate_limiter = GithubRateLimiter(github)
        safe_call = safe_call_decorator(rate_limiter)
        registered_issues: list[int] = []
        data_issue_numbers = [issue.number for issue in data.issues]

        logger.debug("Registering hierarchy issues to records...")
        # create hierarchy issue records first => dict of hierarchy issues with registered sub-issues
        #   1. round - the most heavy ones  (e.g. Epic)
        #   2. round - the second most heavy ones   (e.g. Features)
        #   3. round - the rest (e.g. Bugs, Tasks, etc.) but can be just another hierarchy - depend on configuration
        for hierarchy_issue in ActionInputs.get_issue_type_weights():
            logger.debug("Registering hierarchy issues of type: %s", hierarchy_issue)
            for issue in data.issues:
                issue_labels: list[Label] = list(issue.get_labels())
                issue_type = self._get_issue_type(issue, issue_labels)
                if issue_type is not None and issue_type == hierarchy_issue and issue.number not in registered_issues:
                    sub_issues = list(issue.get_sub_issues())
                    if len(sub_issues) == 0:
                        continue    # not a hierarchy issue even if labeled or issue type say so

                    self.create_record_for_hierarchy_issue(records, issue, issue_type, issue_labels)
                    registered_issues.append(issue.number)
                    rec: HierarchyIssueRecord = cast(HierarchyIssueRecord, records[issue.number])
                    if len(sub_issues) > 0:
                        self._solve_sub_issues(rec, data, data_issue_numbers, registered_issues, sub_issues)

        # create or register non-hierarchy issue related records
        logger.debug("Registering issues to records...")
        for issue in data.issues:
            if issue.number not in registered_issues:
                parent_issue = issue.get_sub_issues()
                if parent_issue is not None:
                    pass  # TODO - find parent and register to it
                else:
                    IssueHierarchyRecordFactory.create_record_for_issue(records, issue)

        logger.debug("Registering pull requests to records and commit to Pull Requests...")
        registered_commits: list[str] = []
        for pull in data.pull_requests:
            pull_labels = [label.name for label in pull.get_labels()]
            skip_record: bool = any(item in pull_labels for item in ActionInputs.get_skip_release_notes_labels())
            related_commits = [c for c in data.commits if c.sha == pull.merge_commit_sha]
            registered_commits.extend(c.sha for c in related_commits)

            if not safe_call(get_issues_for_pr)(pull_number=pull.number) and not extract_issue_numbers_from_body(pull):
                pr_rec = PullRequestRecord(pull, skip=skip_record)
                for c in related_commits:   # register commits to the PR record
                    pr_rec.register_commit(c)
                records[pull.number] = pr_rec
                logger.debug("Created record for PR %d: %s", pull.number, pull.title)

            else:
                logger.debug("Registering pull number: %s, title : %s", pull.number, pull.title)
                rec: IssueRecord = register_pull_request(pull, skip_record)
                for c in related_commits:   # register commits to the PR record
                    if rec is not None:
                        rec.register_commit(pull, c)

        logger.debug("Registering direct commits to records...")
        for commit in data.commits:
            if commit.sha not in registered_commits:
                records[commit.sha] = CommitRecord(commit)

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected.",
            len(records),
            len(data.issues),
            len(data.pull_requests),
            len(data.commits),
        )
        return records

    def _solve_sub_issues(
        self,
        record: HierarchyIssueRecord,
        data: MinedData,
        data_issue_numbers: list[int],
        registered_issues: list[int],
        sub_issues: list[SubIssue],
    ) -> None:
        logger.debug("Solving sub issues for hierarchy issue record %d", record.issue.number)

        for sub_issue in sub_issues:  # closed in previous rls, in current one, open ones
            logger.debug("Processing sub-issue %d", sub_issue.number)

            if sub_issue.number in registered_issues:  # already registered
                logger.debug("Sub-issue %d already registered, skipping", sub_issue.number)
                continue
            if sub_issue.number not in data_issue_numbers:  # not closed in current rls or not opened == not in mined data
                logger.debug("Sub-issue %d not registered, skipping", sub_issue.number)
                continue

            sub_sub_issues = list(sub_issue.get_sub_issues())
            if len(sub_sub_issues) > 0:
                logger.debug("Solving sub issues for sub-issue: %s", sub_issue.number)
                rec = record.register_hierarchy_issue(sub_issue)
                registered_issues.append(sub_issue.number)
                self._solve_sub_issues(rec, data, data_issue_numbers, registered_issues, sub_sub_issues)
            else:
                logger.debug("Solving sub issues for sub-issue: %s", sub_issue.number)
                record.register_issue(sub_issue)
                registered_issues.append(sub_issue.number)

    @staticmethod
    def create_record_for_hierarchy_issue(records: dict[int | str, Record], i: Issue, issue_type: Optional[str],
                                          issue_labels: list[Label]) -> None:
        """
        Create a record for an issue.

        Parameters:
            records: The records to create the record for.
            i: Issue instance.
            issue_type: The type of the issue.
            issue_labels: The labels of the issue.

        Returns:
            None
        """
        # check for skip labels presence and skip when detected
        issue_labels_names = [label.name for label in issue_labels]
        skip_record = any(item in issue_labels_names for item in ActionInputs.get_skip_release_notes_labels())
        records[i.number] = HierarchyIssueRecord(issue=i, issue_type=issue_type, skip=skip_record)
        logger.debug("Created record for hierarchy issue %d: %s (type: %s)", i.number, i.title, issue_type)

    @staticmethod
    def _get_issue_type(issue: Issue, issue_labels: list[Label]) -> Optional[str]:
        if issue.type is not None:
            return issue.type.name

        if len(issue_labels) > 0:
            issue_labels_lower = [label.name.lower() for label in issue_labels]
            issue_types = [issue_type.lower() for issue_type in ActionInputs.get_issue_type_weights()]
            # Find all matching types and their indices in the original list
            matching_indices = [
                idx for idx, t in enumerate(issue_types) if t in issue_labels_lower
            ]
            if matching_indices:
                # Return the type from the original list with the lowest index
                return ActionInputs.get_issue_type_weights()[min(matching_indices)]

        return None
