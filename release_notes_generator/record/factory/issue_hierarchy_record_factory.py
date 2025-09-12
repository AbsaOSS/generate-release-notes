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
from typing import cast

from github import Github
from github.Issue import Issue, SubIssue
from github.PullRequest import PullRequest
from github.Commit import Commit

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

        def register_pull_request(pull: PullRequest, skip_rec: bool) -> None:
            detected_issues = extract_issue_numbers_from_body(pull)
            logger.debug("Detected issues - from body: %s", detected_issues)
            detected_issues.update(safe_call(get_issues_for_pr)(pull_number=pull.number))
            logger.debug("Detected issues - final: %s", detected_issues)

            for parent_issue_number in detected_issues:
                # create an issue record if not present for PR parent
                if parent_issue_number not in records:
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

                if parent_issue_number in records:
                    cast(IssueRecord, records[parent_issue_number]).register_pull_request(pull)
                    logger.debug("Registering PR %d: %s to Issue %d", pull.number, pull.title, parent_issue_number)
                else:
                    logger.debug(
                        "Registering stand-alone PR %d: %s as mentioned Issue %d not found.",
                        pull.number,
                        pull.title,
                        parent_issue_number,
                    )

        records: dict[int | str, Record] = {}
        rate_limiter = GithubRateLimiter(github)
        safe_call = safe_call_decorator(rate_limiter)
        registered_issues: list[int] = []

        logger.debug("Registering issues to records...")
        # create hierarchy issue records first => dict of hierarchy issues with registered sub-issues
        #   1. round - the most heavy ones  (e.g. Epic)
        #   2. round - the second most heavy ones   (e.g. Features)
        #   3. round - the rest (e.g. Bugs, Tasks, etc.) but can be just another hierarchy - depend on configuration
        for hierarchy_issue in ActionInputs.get_issue_type_weights():
            for issue in data.issues:
                if issue.type.name == hierarchy_issue and issue.number not in registered_issues:
                    self.create_record_for_issue(records, issue)
                    registered_issues.append(issue.number)
                    rec: HierarchyIssueRecord = cast(HierarchyIssueRecord, records[issue.number])
                    sub_issues = list(rec.issue.get_sub_issues())
                    if len(sub_issues) > 0:
                        self._solve_sub_issues(rec, data, registered_issues, sub_issues)

        # create or register non-hierarchy issue related records
        for issue in data.issues:
            if issue.number not in registered_issues:
                parent_issue = issue.get_sub_issues()
                if parent_issue is not None:
                    pass  # TODO - find parent and register to it
                else:
                    IssueHierarchyRecordFactory.create_record_for_issue(records, issue)

        logger.debug("Registering pull requests to records...")
        for pull in data.pull_requests:
            pull_labels = [label.name for label in pull.get_labels()]
            skip_record: bool = any(item in pull_labels for item in ActionInputs.get_skip_release_notes_labels())

            if not safe_call(get_issues_for_pr)(pull_number=pull.number) and not extract_issue_numbers_from_body(pull):
                records[pull.number] = PullRequestRecord(pull, skip=skip_record)
                logger.debug("Created record for PR %d: %s", pull.number, pull.title)
            else:
                logger.debug("Registering pull number: %s, title : %s", pull.number, pull.title)
                register_pull_request(pull, skip_record)

        logger.debug("Registering commits to records...")
        detected_direct_commits_count = sum(
            not IssueHierarchyRecordFactory.register_commit_to_record(records, commit) for commit in data.commits
        )

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected.",
            len(records),
            len(data.issues),
            len(data.pull_requests),
            detected_direct_commits_count,
        )
        return records

    def _solve_sub_issues(
        self,
        record: HierarchyIssueRecord,
        data: MinedData,
        registered_issues: list[int],
        sub_issues: list[SubIssue],
    ) -> None:
        for sub_issue in sub_issues:  # closed in previous rls, in current one, open ones
            if sub_issue.number in registered_issues:  # already registered
                continue
            if sub_issue.number not in data.issues:  # not closed in current rls or not opened == not in mined data
                continue

            sub_sub_issues = list(sub_issue.get_sub_issues())
            if len(sub_sub_issues) > 0:
                rec = record.register_hierarchy_issue(sub_issue)
                registered_issues.append(sub_issue.number)
                self._solve_sub_issues(rec, data, registered_issues, sub_sub_issues)
            else:
                record.register_issue(sub_issue)
                registered_issues.append(sub_issue.number)

    @staticmethod
    def register_commit_to_record(records: dict[int | str, Record], commit: Commit) -> bool:
        """
        Register a commit to a record.

        @param commit: The commit to register.
        @return: True if the commit was registered to a record, False otherwise
        """
        for record in records.values():
            if isinstance(record, IssueRecord):
                rec_i = cast(IssueRecord, record)
                for number in rec_i.get_pull_request_numbers():
                    pr = rec_i.get_pull_request(number)
                    if pr and pr.merge_commit_sha == commit.sha:
                        rec_i.register_commit(pr, commit)
                        return True

            elif isinstance(record, PullRequestRecord):
                rec_pr = cast(PullRequestRecord, record)
                if rec_pr.is_commit_sha_present(commit.sha):
                    rec_pr.register_commit(commit)
                    return True

        records[commit.sha] = CommitRecord(commit=commit)
        logger.debug("Created record for direct commit %s: %s", commit.sha, commit.commit.message)
        return False

    @staticmethod
    def create_record_for_issue(records: dict[int | str, Record], i: Issue) -> None:
        """
        Create a record for an issue.

        @param i: Issue instance.
        @return: None
        """
        # check for skip labels presence and skip when detected
        issue_labels = [label.name for label in i.get_labels()]
        skip_record = any(item in issue_labels for item in ActionInputs.get_skip_release_notes_labels())
        records[i.number] = IssueRecord(issue=i, skip=skip_record)

        logger.debug("Created record for issue %d: %s", i.number, i.title)
