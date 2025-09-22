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
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Commit import Commit

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.model.record import Record
from release_notes_generator.record.factory.record_factory import RecordFactory

from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.pull_request_utils import get_issues_for_pr, extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


class DefaultRecordFactory(RecordFactory):
    """
    A class used to generate records for release notes.
    """

    def __init__(self, github: Github) -> None:
        self._github: Github = github
        rate_limiter = GithubRateLimiter(github)
        self._safe_call = safe_call_decorator(rate_limiter)

        self._records: dict[int | str, Record] = {}

    def generate(self, data: MinedData) -> dict[int | str, Record]:
        """
        Generate records for release notes.
        Parameters:
            data (MinedData): The MinedData instance containing repository, issues, pull requests, and commits.
        Returns:
            dict[int|str, Record]: A dictionary of records where the key is the issue or pull request number.
        """

        def register_pull_request(pull: PullRequest, skip_rec: bool) -> None:
            detected_issues = extract_issue_numbers_from_body(pull)
            logger.debug("Detected issues - from body: %s", detected_issues)
            detected_issues.update(self._safe_call(get_issues_for_pr)(pull_number=pull.number))
            logger.debug("Detected issues - final: %s", detected_issues)

            for parent_issue_number in detected_issues:
                # create an issue record if not present for PR parent
                if parent_issue_number not in self._records:
                    logger.warning(
                        "Detected PR %d linked to issue %d which is not in the list of received issues. "
                        "Fetching ...",
                        pull.number,
                        parent_issue_number,
                    )
                    parent_issue = (
                        self._safe_call(data.repository.get_issue)(parent_issue_number) if data.repository else None
                    )
                    if parent_issue is not None:
                        self._create_record_for_issue(parent_issue)

                if parent_issue_number in self._records:
                    cast(IssueRecord, self._records[parent_issue_number]).register_pull_request(pull)
                    logger.debug("Registering PR %d: %s to Issue %d", pull.number, pull.title, parent_issue_number)
                else:
                    logger.debug(
                        "Registering stand-alone PR %d: %s as mentioned Issue %d not found.",
                        pull.number,
                        pull.title,
                        parent_issue_number,
                    )

        logger.debug("Registering issues to records...")
        for issue in data.issues:
            self._create_record_for_issue(issue)

        logger.debug("Registering pull requests to records...")
        for pull in data.pull_requests:
            pull_labels = [label.name for label in pull.get_labels()]
            skip_record: bool = any(item in pull_labels for item in ActionInputs.get_skip_release_notes_labels())

            if not self._safe_call(get_issues_for_pr)(pull_number=pull.number) and not extract_issue_numbers_from_body(
                pull
            ):
                self._records[pull.number] = PullRequestRecord(pull, skip=skip_record)
                logger.debug("Created record for PR %d: %s", pull.number, pull.title)
            else:
                logger.debug("Registering pull number: %s, title : %s", pull.number, pull.title)
                register_pull_request(pull, skip_record)

        logger.debug("Registering commits to records...")
        detected_direct_commits_count = sum(not self.register_commit_to_record(commit) for commit in data.commits)

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected.",
            len(self._records),
            len(data.issues),
            len(data.pull_requests),
            detected_direct_commits_count,
        )
        return self._records

    def register_commit_to_record(self, commit: Commit) -> bool:
        """
        Register a commit to a record.

        @param commit: The commit to register.
        @return: True if the commit was registered to a record, False otherwise
        """
        for record in self._records.values():
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

        self._records[commit.sha] = CommitRecord(commit=commit)
        logger.debug("Created record for direct commit %s: %s", commit.sha, commit.commit.message)
        return False

    def _create_record_for_issue(self, issue: Issue, issue_labels: Optional[list[str]] = None) -> None:
        """
        Create a record for an issue.

        Parameters:
            records (dict[int|str, Record]): The dictionary of records to add the issue record to.
            issue (Issue): The issue to create a record for.
            issue_labels (Optional[list[str]]): Optional set of labels for the issue. If not provided, labels will be
                fetched from the issue.
        Returns:
            None
        """
        # check for skip labels presence and skip when detected
        if issue_labels is None:
            issue_labels = [label.name for label in issue.get_labels()]
        skip_record = any(item in issue_labels for item in ActionInputs.get_skip_release_notes_labels())
        self._records[issue.number] = IssueRecord(issue=issue, skip=skip_record)
        logger.debug("Created record for non hierarchy issue %d: %s", issue.number, issue.title)
