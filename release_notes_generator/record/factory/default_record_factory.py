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
DefaultRecordFactory builds Record objects (issues, pulls, commits) from mined GitHub data.
"""

import logging
from typing import cast, Optional

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Commit import Commit
from github.Repository import Repository

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
from release_notes_generator.utils.record_utils import get_id

logger = logging.getLogger(__name__)


class DefaultRecordFactory(RecordFactory):
    """
    A class used to generate records for release notes.
    """

    def __init__(self, github: Github, home_repository: Repository) -> None:
        self._github = github
        rate_limiter = GithubRateLimiter(github)
        self._safe_call = safe_call_decorator(rate_limiter)
        self._home_repository = home_repository

        self._records: dict[str, Record] = {}

    # TODO - this should not be needed now - delete
    # def get_repository(self, full_name: str) -> Optional[Repository]:
    #     """
    #     Retrieves the specified GitHub repository.
    #
    #     Returns:
    #         Optional[Repository]: The GitHub repository if found, None otherwise.
    #     """
    #     repo: Optional[Repository] = self._safe_call(self._github.get_repo)(full_name)
    #     if repo is None:
    #         logger.error("Repository not found: %s", full_name)
    #         return None
    #     return repo

    def generate(self, data: MinedData) -> dict[str, Record]:
        """
        Generate records for release notes.
        Parameters:
            data (MinedData): The MinedData instance containing repository, issues, pull requests, and commits.
        Returns:
            dict[str, Record]: A dictionary of records keyed by 'owner/repo#number' (or commit SHA for commits).
        """

        def register_pull_request(pr: PullRequest, l_pid: str, skip_rec: bool) -> None:
            l_pull_labels = [label.name for label in pr.get_labels()]
            attached_any = False
            detected_issues = extract_issue_numbers_from_body(pr, repository=data.home_repository)
            logger.debug("Detected issues - from body: %s", detected_issues)
            linked = self._safe_call(get_issues_for_pr)(pull_number=pr.number)
            if linked:
                detected_issues.update(linked)
            logger.debug("Detected issues - merged: %s", detected_issues)

            for parent_issue_id in detected_issues:
                # create an issue record if not present for PR parent
                if parent_issue_id not in self._records:
                    logger.warning(
                        "Detected PR %d linked to issue %s which is not in the list of received issues. "
                        "Fetching ...",
                        pr.number,
                        parent_issue_id,
                    )
                    # dev note: here we expect that PR links to an issue in the same repository !!!
                    pi_repo_name, pi_number_str = parent_issue_id.split("#", 1)
                    try:
                        pi_number = int(pi_number_str)
                    except ValueError:
                        logger.error("Invalid parent issue id: %s", parent_issue_id)
                        continue
                    parent_repository = data.get_repository(pi_repo_name)
                    if parent_repository is not None:
                        # cache for subsequent lookups
                        if data.get_repository(pi_repo_name) is None:
                            data.add_repository(parent_repository)
                        parent_issue = self._safe_call(parent_repository.get_issue)(pi_number)
                    else:
                        parent_issue = None

                    if parent_issue is not None:
                        self._create_record_for_issue(parent_issue, parent_issue_id)

                if parent_issue_id in self._records:
                    cast(IssueRecord, self._records[parent_issue_id]).register_pull_request(pr)
                    logger.debug("Registering PR %d: %s to Issue %s", pr.number, pr.title, parent_issue_id)
                    attached_any = True
                else:
                    logger.debug(
                        "Registering stand-alone PR %d: %s as mentioned Issue %s not found.",
                        pr.number,
                        pr.title,
                        parent_issue_id,
                    )

            if not attached_any:
                self._records[l_pid] = PullRequestRecord(pr, l_pull_labels, skip=skip_rec)
                logger.debug("Created stand-alone PR record %s: %s (fallback)", l_pid, pr.title)

        logger.debug("Registering issues to records...")
        for issue, repo in data.issues.items():
            self._create_record_for_issue(issue, get_id(issue, repo))

        logger.debug("Registering pull requests to records...")
        for pull, repo in data.pull_requests.items():
            pid = get_id(pull, repo)
            pull_labels = [label.name for label in pull.get_labels()]
            skip_record: bool = any(item in pull_labels for item in ActionInputs.get_skip_release_notes_labels())

            linked_from_api = self._safe_call(get_issues_for_pr)(pull_number=pull.number) or set()
            linked_from_body = extract_issue_numbers_from_body(pull, data.home_repository)
            if not linked_from_api and not linked_from_body:
                self._records[pid] = PullRequestRecord(pull, pull_labels, skip=skip_record)
                logger.debug("Created record for PR %s: %s", pid, pull.title)
            else:
                logger.debug("Registering pull number: %s, title : %s", pid, pull.title)
                register_pull_request(pull, pid, skip_record)

        logger.debug("Registering commits to records...")
        detected_direct_commits_count = sum(
            not self.register_commit_to_record(commit, get_id(commit, repo)) for commit, repo in data.commits.items()
        )

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected.",
            len(self._records),
            len(data.issues),
            len(data.pull_requests),
            detected_direct_commits_count,
        )
        return self._records

    def register_commit_to_record(self, commit: Commit, cid: str) -> bool:
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

        self._records[cid] = CommitRecord(commit=commit)
        logger.debug("Created record for direct commit %s: %s", commit.sha, commit.commit.message)
        return False

    def _create_record_for_issue(self, issue: Issue, iid: str, issue_labels: Optional[list[str]] = None) -> None:
        """
        Create a record for an issue.

        Parameters:
            issue (Issue): The issue to create a record for.
            iid (str): The ID of the issue in the format 'owner/repo#number'.
            issue_labels (Optional[list[str]]): Optional set of labels for the issue. If not provided, labels will be
                fetched from the issue.
        Returns:
            None
        """
        # check for skip labels presence and skip when detected
        if issue_labels is None:
            issue_labels = [label.name for label in issue.get_labels()]
        skip_record = any(item in issue_labels for item in ActionInputs.get_skip_release_notes_labels())
        self._records[iid] = IssueRecord(issue=issue, skip=skip_record, issue_labels=issue_labels)
        logger.debug("Created record for non hierarchy issue '%s': %s", iid, issue.title)
