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


class PullRequestRecord(Record):
    """
    A class used to represent a record in the release notes.
    The record represents a pull request and its commits.
    """

    def __init__(self, repo: Repository, safe_call, pull_request: PullRequest):
        super().__init__(repo, safe_call)

        self.__pull_request: PullRequest = pull_request
        self.__commits: list[Commit] = []

    @property
    def issue(self) -> Optional[Issue]:
        """Get the issue of the record."""
        return None

    @property
    def pull_requests(self) -> list[PullRequest]:
        """Get the pull requests of the record."""
        return [self.__pull_request]

    @property
    def commits(self) -> list[Commit]:
        """Get the commits of the record."""
        return self.__commits

    # TODO - remove this method after unit test fix
    # def pull_request_by_number(self) -> PullRequest:
    #     """Getter for the pull request of the record."""
    #     return self.__pull_request

    @property
    def id(self) -> Optional[int | str]:
        """Get the id of the record."""
        return self.__pull_request.number if self.__pull_request is not None else None

    @property
    def labels(self) -> list[str]:
        """Get the labels of the record."""
        return [label.name for label in self.__pull_request.labels] if self.__pull_request is not None else []

    @property
    def assignee(self) -> Optional[str]:
        """Get record assignee."""
        return self.__pull_request.assignee.login if self.__pull_request.assignee is not None else None

    @property
    def assignees(self) -> Optional[str]:
        """Get record assignees."""
        logins = [a.login for a in self.__pull_request.assignees]
        return ", ".join(logins) if len(logins) > 0 else None

    @property
    def developers(self) -> Optional[str]:
        """Get record developers."""
        logins = {f"@{c.author.login}" for c in self.__commits}
        if not logins:
            logger.warning("Found pull request record '%s' with no commits", self.__pull_request.number)
        return ", ".join(logins) if len(logins) > 0 else None

    @property
    def contributors(self) -> Optional[str]:
        """Get record contributors."""
        logins = []
        for c in self.__commits:
            logins.extend(self.get_contributors_for_commit(c))

        return ", ".join(logins) if len(logins) > 0 else None

    def is_state(self, state: str) -> bool:
        """Check if the record is in a specific state."""
        return self.__pull_request.state == state if self.__pull_request is not None else False

    def pr_contains_issue_mentions(self) -> bool:
        """Checks if the record's pull request contains issue mentions."""
        return len(extract_issue_numbers_from_body(self.__pull_request)) > 0

    def pr_links(self) -> Optional[str]:
        """Get links to record's pull requests."""
        return self.LINK_TO_PR_TEMPLATE.format(number=self.__pull_request.number, full_name=self._repo.full_name)

    def register_pull_request(self, pr: PullRequest) -> None:
        """
        Registers a pull request with the record.

        @param pr: The PullRequest object to register.
        @return: None
        """
        self.__pull_request = pr

    def register_commit(self, commit: Commit) -> bool:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: None
        """
        sha = commit.sha
        if sha == self.__pull_request.merge_commit_sha or sha == self.__pull_request.head.sha:
            self.__commits.append(commit)
            logger.debug(
                "Commit %s registered using sha in PR %s of record %s", commit.sha, self.__pull_request.number, self.id
            )
            return True

        return False

    def to_chapter_row(self) -> str:
        """
        Converts the record to a string row usable in a chapter.

        @return: The record as a row string.
        """
        self.increment_present_in_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters > 1 else ""
        format_values = {"number": self.__pull_request.number, "title": self.__pull_request.title}

        format_values.update(self._get_row_format_values(ActionInputs.get_row_format_pr()))

        pr_prefix = "PR: " if ActionInputs.get_row_format_link_pr() else ""
        row = f"{row_prefix}{pr_prefix}" + ActionInputs.get_row_format_pr().format(**format_values)
        row = row.replace("  ", " ")
        if self.contains_release_notes():
            row = f"{row}\n{self.get_rls_notes()}"

        return row

    def fetch_pr_commits(self) -> None:
        """Fetches the commits of the record."""
        self.__commits = list(self._safe_call(self.__pull_request.get_commits)())

    def get_sha_of_all_commits(self) -> set[str]:
        """Get the set of all commit shas of the record."""
        set_of_commit_shas = set()

        for c in self.__commits:
            set_of_commit_shas.add(c.sha)
            set_of_commit_shas.add(c.commit.sha)

        set_of_commit_shas.add(self.__pull_request.merge_commit_sha)
        return set_of_commit_shas
