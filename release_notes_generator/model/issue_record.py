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
This module contains the BaseChapters class which is responsible for representing the base chapters.
"""

import logging
from typing import Optional

from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.base_record import Record
from release_notes_generator.utils.pull_reuqest_utils import extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


class IssueRecord(Record):
    """
    A class used to represent a record in the release notes.
    The record represents an issue with its Pull requests and commits.
    """

    def __init__(self, repo: Repository, safe_call, issue: Optional[Issue] = None):
        super().__init__(repo, safe_call)

        self.__issue: Issue = issue
        self.__pulls_requests: list[PullRequest] = []
        self.__pr_commits: dict[int, list[Commit]] = {}

    @property
    def issue(self) -> Optional[Issue]:
        """Get the issue of the record."""
        return self.__issue

    @property
    def pull_requests(self) -> list[PullRequest]:
        """Get the pull requests of the record."""
        return self.__pulls_requests

    @property
    def commits(self) -> list[Commit]:
        """Get the commits of the record."""
        all_commits = []
        for commits in self.__pr_commits.values():
            all_commits.extend(commits)
        return all_commits

    @property
    def id(self) -> Optional[int | str]:
        """Get the id of the record."""
        return self.__issue if self.__issue is not None else None

    @property
    def labels(self) -> list[str]:
        """Getter for the labels of the record."""
        return [label.name for label in self.__issue.labels] if self.__issue is not None else []

    @property
    def assignee(self) -> Optional[str]:
        """Get record's assignee."""
        return self.issue.assignee.login if self.issue.assignee is not None else None

    @property
    def assignees(self) -> Optional[str]:
        """Get record's assignees."""
        logins = [a.login for a in self.issue.assignees]
        return ", ".join(logins) if len(logins) > 0 else None

    @property
    def developers(self) -> Optional[str]:
        """Get record's developers."""
        logins = set()
        for commits in self.__pr_commits.values():
            for commit in commits:
                if commit.author is not None:
                    logins.add(f"@{commit.author.login}")

        if not logins:
            logger.warning(
                "Found issue record %s with %d pull requests and no commits", self.id, len(self.__pulls_requests)
            )

        return ", ".join(logins) if len(logins) > 0 else None

    @property
    def contributors(self) -> Optional[str]:
        """Get record's contributors."""
        logins = []
        for c in self.commits:
            for line in c.commit.message.split("\n"):
                if "Co-authored-by:" in line:
                    name = line.split("Co-authored-by:")[1].strip()
                    if name not in logins:
                        logins.append(name)

        return ", ".join(logins) if len(logins) > 0 else None

    def is_state(self, state: str) -> bool:
        """Check if the record is in a specific state."""
        return self.__issue.state == state if self.__issue is not None else False

    def pr_contains_issue_mentions(self) -> bool:
        """Checks if the record's pull request contains issue mentions."""
        return len(extract_issue_numbers_from_body(self.__pulls_requests[0])) > 0

    def pr_links(self) -> Optional[str]:
        """Get links to record's pull requests."""
        if len(self.__pulls_requests) == 0:
            return None

        res = [
            self.LINK_TO_PR_TEMPLATE.format(number=pull.number, full_name=self._repo.full_name)
            for pull in self.__pulls_requests
        ]
        return ", ".join(res)

    def register_pull_request(self, pr: PullRequest) -> None:
        """
        Registers a pull request with the record.

        @param pr: The PullRequest object to register.
        @return: None
        """
        self.__pulls_requests.append(pr)

    def register_commit(self, commit: Commit) -> bool:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: True if record is registered and valid for one of record's pull requests, False otherwise.
        """
        sha = commit.sha
        for pull in self.__pulls_requests:
            if sha == pull.merge_commit_sha or sha == pull.head.sha:
                if self.__pr_commits.get(pull.number) is None:
                    self.__pr_commits[pull.number] = []
                self.__pr_commits[pull.number].append(commit)
                logger.debug("Commit %s registered using sha in PR %s of record %s", commit.sha, pull.number, self.id)
                return True

        return False

    def to_chapter_row(self) -> str:
        """
        Converts the record to a string row usable in a chapter.

        @return: The record as a row string.
        """
        self.increment_present_in_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters > 1 else ""
        format_values = {
            "number": self.__issue.number,
            "title": self.__issue.title,
            "pull-requests": f"in {self.pr_links()}" if len(self.__pulls_requests) > 0 else "",
        }

        format_values.update(self._get_row_format_values(ActionInputs.get_row_format_issue()))

        row = f"{row_prefix}" + ActionInputs.get_row_format_issue().format(**format_values)
        row = row.replace("  ", " ")
        if self.contains_release_notes():
            row = f"{row}\n{self.get_rls_notes()}"

        return row

    def fetch_pr_commits(self) -> None:
        """Fetch commits of the record's pull requests."""
        for pull in self.__pulls_requests:
            self.__pr_commits[pull.number] = list(self._safe_call(pull.get_commits)())

    def get_sha_of_all_commits(self) -> set[str]:
        """Get the set of all commit shas of the record."""
        set_of_commit_shas = set()

        for commits in self.__pr_commits.values():
            for c in commits:
                set_of_commit_shas.add(c.sha)
                set_of_commit_shas.add(c.commit.sha)

        for pull in self.__pulls_requests:
            set_of_commit_shas.add(pull.merge_commit_sha)

        return set_of_commit_shas
