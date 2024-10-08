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
from abc import ABC, abstractmethod
from typing import Optional

from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit

from release_notes_generator.utils.constants import (
    RELEASE_NOTE_DETECTION_PATTERN,
    RELEASE_NOTE_LINE_MARK,
    PR_STATE_CLOSED,
)

logger = logging.getLogger(__name__)


class Record(ABC):
    """
    A class used to represent a record in the release notes.
    """

    LINK_TO_PR_TEMPLATE = "[#{number}](https://github.com/{full_name}/pull/{number})"

    def __init__(self, repo: Repository, safe_call):
        self._repo: Repository = repo
        self._safe_call = safe_call

        self.__is_release_note_detected: bool = False
        self.__present_in_chapters = 0

    @property
    def is_present_in_chapters(self) -> bool:
        """Check if the record is present in chapters."""
        return self.__present_in_chapters > 0

    @property
    def present_in_chapters(self) -> int:
        """Gets the count of chapters in which the record is present."""
        return self.__present_in_chapters

    @property
    @abstractmethod
    def id(self) -> Optional[int | str]:
        """Get the id of the record."""
        pass

    @property
    @abstractmethod
    def issue(self) -> Optional[Issue]:
        """Get the record's issue."""
        pass

    @property
    @abstractmethod
    def pull_requests(self) -> list[PullRequest]:
        """Get the record's pull requests."""
        pass

    @property
    @abstractmethod
    def commits(self) -> list[Commit]:
        """Get the record's commits."""
        pass

    @property
    @abstractmethod
    def labels(self) -> list[str]:
        """Get labels of the record."""
        pass

    # Note: assignee & assignees are related to this GitHub Docs - https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users#about-issue-and-pull-request-assignees
    @property
    @abstractmethod
    def assignee(self) -> Optional[str]:
        """Get record's assignee."""
        pass

    @property
    @abstractmethod
    def assignees(self) -> Optional[str]:
        """Get record's assignees."""
        pass

    @property
    @abstractmethod
    def developers(self) -> Optional[str]:
        """Get record's developers."""
        pass

    @property
    @abstractmethod
    def contributors(self) -> Optional[str]:
        """Get record's contributors."""
        pass

    @abstractmethod
    def pr_links(self) -> Optional[str]:
        """Get links to record's pull requests."""
        pass

    @abstractmethod
    def pr_contains_issue_mentions(self) -> bool:
        """Checks if the record's pull requests contains issue mentions."""
        pass

    @abstractmethod
    def is_state(self, state: str) -> bool:
        """Check if the record's state is the specified state."""
        pass

    # TODO - review of all method doc strings - same format, return values
    @abstractmethod
    def register_pull_request(self, pr: PullRequest) -> None:
        """
        Registers a pull request with the record.

        @param pr: The PullRequest object to register.
        @return: None
        """
        pass

    @abstractmethod
    def register_commit(self, commit: Commit) -> bool:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: True if record is registered and valid for one of record's pull requests, False otherwise.
        """
        pass

    @abstractmethod
    def to_chapter_row(self) -> str:
        """
        Converts the record to a string row usable in a chapter.

        @return: The record as a row string.
        """
        pass

    @abstractmethod
    def fetch_pr_commits(self) -> None:
        pass

    @abstractmethod
    def get_sha_of_all_commits(self) -> set[str]:
        pass

    # TODO - remove after fix of unit tests
    # @abstractmethod
    # def count_of_commits(self) -> int:
    #     """
    #     Get count of commits in all record pull requests.
    #
    #     @return: The count of commits in the records.
    #     """
    #     pass

    # TODO - remove after fix of unit tests
    # @abstractmethod
    # def pull_request_by_number(self, pr_number: int) -> Optional[PullRequest]:
    #     """
    #     Gets a pull request associated with the record.
    #
    #     @param index: The index of the pull request.
    #     @return: The PullRequest instance.
    #     """
    #     if index < 0 or index >= len(self.__pulls):
    #         return None
    #     return self.__pulls[index]

    @staticmethod
    def get_contributors_for_commit(commit: Commit) -> list[str]:
        """
        Gets Contributors from commit message.

        @param commit: The commit to get contributors from.
        @return: A list of contributors.
        """

        logins = []
        for line in commit.commit.message.split("\n"):
            if "Co-authored-by:" in line:
                name = line.split("Co-authored-by:")[1].strip()
                if name not in logins:
                    logins.append(name)

        return logins

    @staticmethod
    def is_pull_request_merged(pull: PullRequest) -> bool:
        """
        Checks if the pull request is merged.

        @param pull: The pull request to check.
        @return: A boolean indicating whether the pull request is merged.
        """
        return pull.state == PR_STATE_CLOSED and pull.merged_at is not None and pull.closed_at is not None

    def increment_present_in_chapters(self) -> None:
        """
        Increments the count of chapters in which the record is present.

        @return: None
        """
        self.__present_in_chapters += 1

    # TODO in Issue named 'Configurable regex-based Release note detection in the PR body'
    #   - 'Release notest:' as detection pattern default - can be defined by user
    #   - '-' as leading line mark for each release note to be used
    def get_rls_notes(self, detection_pattern=RELEASE_NOTE_DETECTION_PATTERN, line_mark=RELEASE_NOTE_LINE_MARK) -> str:
        """
        Gets the release notes of the record.

        @param detection_pattern: The detection pattern to use.
        @param line_mark: The line mark to use.
        @return: The release notes of the record as a string.
        """
        release_notes = ""

        # Iterate over all PRs
        for pull in self.pull_requests:
            body_lines = pull.body.split("\n") if pull.body is not None else []
            inside_release_notes = False

            for line in body_lines:
                if detection_pattern in line:
                    inside_release_notes = True

                if detection_pattern not in line and inside_release_notes:
                    if line.strip().startswith(line_mark):
                        release_notes += f"  {line}\n"
                    else:
                        break

        # Return the concatenated release notes
        return release_notes.rstrip()

    def contains_release_notes(self) -> bool:
        """Checks if the record contains release notes."""
        if self.__is_release_note_detected:
            return self.__is_release_note_detected

        rls_notes = self.get_rls_notes()
        # if RELEASE_NOTE_LINE_MARK in self.get_rls_notes():
        if RELEASE_NOTE_LINE_MARK in rls_notes:
            self.__is_release_note_detected = True

        return self.__is_release_note_detected

    def contains_min_one_label(self, input_labels: list[str]) -> bool:
        """
        Check if the record contains at least one of the specified labels.

        @param input_labels: A list of labels to check for.
        @return: A boolean indicating whether the record contains any of the specified labels.
        """
        for lbl in self.labels:
            if lbl in input_labels:
                return True

        return False

    def contain_all_labels(self, input_labels: list[str]) -> bool:
        """
        Check if the record contains all the specified labels.

        @param input_labels: A list of labels to check for.
        @return: A boolean indicating whether the record contains all the specified
        """
        if len(self.labels) != len(input_labels):
            return False

        for lbl in self.labels:
            if lbl not in input_labels:
                return False

        return True

    def _get_row_format_values(self, row_format: str) -> dict:
        """
        Create dictionary and fill by user row format defined values.
        NoteL some values are API call intensive.

        @param row_format: User defined row format.
        @return: The dictionary with supported values required by user row format.
        """
        format_values = {}

        if "{assignee}" in row_format:
            assignee = self.assignees
            format_values["assignee"] = f"assigned to @{assignee}" if assignee is not None else ""
        if "{assignees}" in row_format:
            assignees = self.assignees
            format_values["assignees"] = f"assigned to @{assignees}" if assignees is not None else ""
        if "{author}" in row_format:
            developers = self.developers
            format_values["author"] = f"developed by {developers}" if developers is not None else ""
        if "{developed-by}" in row_format:
            developers = self.developers
            format_values["developed-by"] = f"developed by {developers}" if developers is not None else ""
        if "{co-authored-by}" in row_format:
            contributors = self.contributors
            format_values["co-authored-by"] = f"co-authored by {contributors}" if contributors is not None else ""

        return format_values
