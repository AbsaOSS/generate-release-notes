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
IssueHierarchyRecordFactory builds hierarchical issue records (Epics/Features/Tasks) and associates PRs/commits.
"""

import logging
from typing import cast, Optional

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.model.record import Record
from release_notes_generator.model.sub_issue_record import SubIssueRecord
from release_notes_generator.record.factory.default_record_factory import DefaultRecordFactory

from release_notes_generator.utils.pull_request_utils import get_issues_for_pr, extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


class IssueHierarchyRecordFactory(DefaultRecordFactory):
    """
    A class used to generate records for release notes.
    """

    def __init__(self, github: Github) -> None:
        super().__init__(github)

        self.__registered_issues: set[int] = set()
        self.__sub_issue_parents: dict[int, int] = {}
        self.__registered_commits: set[str] = set()

    def generate(self, data: MinedData) -> dict[int | str, Record]:
        """
        Generate records for release notes.
        Parameters:
            data (MinedData): The MinedData instance containing repository, issues, pull requests, and commits.
        Returns:
            dict[int|str, Record]: A dictionary of records where the key is the issue or pull request number.
        """
        logger.debug("Creation of records started...")
        # First register all issues with sub-issues
        for issue in data.issues:
            if issue.number in self.__registered_issues:
                continue

            self._create_issue_record_using_sub_issues_existence(issue)

        # Now register all issues without sub-issues
        for issue in data.issues:
            if issue.number in self.__registered_issues:
                continue

            self._create_issue_record_using_sub_issues_not_existence(issue)

        # dev note: Each issue is now in records dict by its issue number - all on same level - no hierarchy
        # This is useful for population by PRs and commits

        logger.debug("Registering Commits to Pull Requests and Pull Requests to Issues...")
        for pull in data.pull_requests:
            self._register_pull_and_its_commits_to_issue(pull, data)

        logger.debug("Registering direct commits to records...")
        for commit in data.commits:
            if commit.sha not in self.__registered_commits:
                self._records[commit.sha] = CommitRecord(commit)

        # dev note: now we have all PRs and commits registered to issues or as stand-alone records
        #   let build hierarchy
        logger.debug("Building issues hierarchy...")
        self._re_register_hierarchy_issues()
        self.order_hierarchy_levels()

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected.",
            len(self._records),
            len(data.issues),
            len(data.pull_requests),
            len(data.commits),
        )
        return self._records

    def _register_pull_and_its_commits_to_issue(self, pull: PullRequest, data: MinedData) -> None:
        pull_labels = [label.name for label in pull.get_labels()]
        skip_record: bool = any(item in pull_labels for item in ActionInputs.get_skip_release_notes_labels())
        related_commits = [c for c in data.commits if c.sha == pull.merge_commit_sha]
        self.__registered_commits.update(c.sha for c in related_commits)

        linked_from_api = self._safe_call(get_issues_for_pr)(pull_number=pull.number) or set()
        linked_from_body = extract_issue_numbers_from_body(pull)
        pull_issues: list[int] = list(linked_from_api.union(linked_from_body))
        attached_any = False
        if len(pull_issues) > 0:
            record_keys = self._records.keys()

            for issue_number in pull_issues:
                if issue_number not in record_keys:
                    logger.warning(
                        "Detected PR %d linked to issue %d which is not in the list of received issues. "
                        "Fetching ...",
                        pull.number,
                        issue_number,
                    )
                    parent_issue = self._safe_call(data.repository.get_issue)(issue_number) if data.repository else None
                    if parent_issue is not None:
                        self._create_issue_record_using_sub_issues_existence(parent_issue)

                if issue_number in record_keys and isinstance(
                    self._records[issue_number], (SubIssueRecord, HierarchyIssueRecord, IssueRecord)
                ):
                    rec = cast(IssueRecord, self._records[issue_number])
                    rec.register_pull_request(pull)
                    logger.debug("Registering pull number: %s, title : %s", pull.number, pull.title)

                    for c in related_commits:  # register commits to the PR record
                        rec.register_commit(pull, c)
                        logger.debug("Registering commit %s to PR %d", c.sha, pull.number)

                    attached_any = True

        if not attached_any:
            pr_rec = PullRequestRecord(pull, pull_labels, skip_record)
            for c in related_commits:  # register commits to the PR record
                pr_rec.register_commit(c)
            self._records[pull.number] = pr_rec
            logger.debug("Created record for PR %d: %s", pull.number, pull.title)

    def _create_issue_record_using_sub_issues_existence(self, issue: Issue) -> None:
        # use presence of sub-issues as a hint for hierarchy issue or non hierarchy issue
        sub_issues = list(issue.get_sub_issues())

        if len(sub_issues) > 0:
            self._create_record_for_hierarchy_issue(issue)
            for si in sub_issues:
                # register sub-issue and its parent for later hierarchy building
                self.__sub_issue_parents[si.number] = issue.number  # Note: GitHub now allows only 1 parent

    def _create_issue_record_using_sub_issues_not_existence(self, issue: Issue) -> None:
        # Expected to run after all issue with sub-issues are registered
        if issue.number in self.__sub_issue_parents.keys():  # pylint: disable=consider-iterating-dictionary
            self._create_record_for_sub_issue(issue)
        else:
            self._create_record_for_issue(issue)

    def _create_record_for_hierarchy_issue(self, i: Issue, issue_labels: Optional[list[str]] = None) -> None:
        """
        Create a hierarchy issue record and register sub-issues.

        Parameters:
            i: The issue to create the record for.
            issue_labels: The labels of the issue.

        Returns:
            None
        """
        # check for skip labels presence and skip when detected
        if issue_labels is None:
            issue_labels = self._get_issue_labels_mix_with_type(i)
        skip_record = any(item in issue_labels for item in ActionInputs.get_skip_release_notes_labels())

        self._records[i.number] = HierarchyIssueRecord(issue=i, skip=skip_record)
        self.__registered_issues.add(i.number)
        logger.debug("Created record for hierarchy issue %d: %s", i.number, i.title)

    def _get_issue_labels_mix_with_type(self, issue: Issue) -> list[str]:
        labels: list[str] = [label.name for label in issue.get_labels()]

        if issue.type is not None:
            issue_type = issue.type.name.lower()
            if issue_type not in labels:
                labels.append(issue_type)

        return labels

    def _create_record_for_issue(self, issue: Issue, issue_labels: Optional[list[str]] = None) -> None:
        if issue_labels is None:
            issue_labels = self._get_issue_labels_mix_with_type(issue)

        super()._create_record_for_issue(issue, issue_labels)
        self.__registered_issues.add(issue.number)

    def _create_record_for_sub_issue(self, issue: Issue, issue_labels: Optional[list[str]] = None) -> None:
        if issue_labels is None:
            issue_labels = self._get_issue_labels_mix_with_type(issue)

        skip_record = any(item in issue_labels for item in ActionInputs.get_skip_release_notes_labels())
        logger.debug("Created record for sub issue %d: %s", issue.number, issue.title)
        self.__registered_issues.add(issue.number)
        self._records[issue.number] = SubIssueRecord(issue, issue_labels, skip_record)

    def _re_register_hierarchy_issues(self):
        sub_issues_numbers = list(self.__sub_issue_parents.keys())

        made_progress = False
        for sub_issue_number in sub_issues_numbers:
            # remove issue(sub_issue_number) from current records and add it to parent
            #   as sub-issue or sub-hierarchy-issue
            # but do it only for issue where parent issue number is not in _sub_issue_parents keys
            #   Why? We building hierarchy from bottom. Access in records is very easy.
            if sub_issue_number in self.__sub_issue_parents.values():
                continue

            parent_issue_nr: int = self.__sub_issue_parents[sub_issue_number]
            parent_rec = cast(HierarchyIssueRecord, self._records[parent_issue_nr])
            sub_rec = self._records[sub_issue_number]

            if isinstance(sub_rec, SubIssueRecord):
                parent_rec.sub_issues[sub_issue_number] = sub_rec  # add to parent as SubIssueRecord
                self._records.pop(sub_issue_number)  # remove from main records as it is sub-one
                self.__sub_issue_parents.pop(sub_issue_number)  # remove from sub-parents as it is now sub-one
                made_progress = True
            elif isinstance(sub_rec, HierarchyIssueRecord):
                parent_rec.sub_hierarchy_issues[sub_issue_number] = (
                    sub_rec  # add to parent as 'Sub' HierarchyIssueRecord
                )
                self._records.pop(sub_issue_number)  # remove from main records as it is sub-one
                self.__sub_issue_parents.pop(sub_issue_number)  # remove from sub-parents as it is now sub-one
                made_progress = True
            else:
                logger.error(
                    "Detected IssueRecord in position of SubIssueRecord - leaving as standalone" " and dropping mapping"
                )
                # Avoid infinite recursion by removing the unresolved mapping
                self.__sub_issue_parents.pop(sub_issue_number, None)

        if self.__sub_issue_parents and made_progress:
            self._re_register_hierarchy_issues()

    def order_hierarchy_levels(self, level: int = 0) -> None:
        """
        Order hierarchy levels for proper rendering.

        Parameters:
            level (int): The current level in the hierarchy. Default is 0.
        """
        # we have now all hierarchy issues in records - but levels are not set
        #   we need to set levels for proper rendering
        #   This have to be done from up to down
        top_hierarchy_records = [rec for rec in self._records.values() if isinstance(rec, HierarchyIssueRecord)]
        for rec in top_hierarchy_records:
            rec.order_hierarchy_levels(level=level)
