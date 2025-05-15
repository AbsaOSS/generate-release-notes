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
import re

from typing import Optional

from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Commit import Commit

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import (
    PR_STATE_CLOSED,
    ISSUE_STATE_CLOSED,
    ISSUE_STATE_OPEN,
    RELEASE_NOTE_LINE_MARKS,
)
from release_notes_generator.utils.pull_reuqest_utils import extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Record:
    """
    A class used to represent a record in the release notes.
    """

    def __init__(self, issue: Optional[Issue] = None, skip: bool = False):
        self.__gh_issue: Optional[Issue] = issue
        self.__pulls: list[PullRequest] = []
        self.__pull_commits: dict[int, list[Commit]] = {}

        self.__is_release_note_detected: bool = False
        self.__present_in_chapters = 0
        self.__skip = skip

    @property
    def number(self) -> int:
        """Getter for the number of the record."""
        if self.__gh_issue is None:
            return self.__pulls[0].number
        return self.__gh_issue.number

    @property
    def issue(self) -> Optional[Issue]:
        """Getter for the issue of the record."""
        return self.__gh_issue

    @property
    def pulls(self) -> list[PullRequest]:
        """Getter for the pull requests of the record."""
        return self.__pulls

    @property
    def commits(self) -> dict:
        """Getter for the commits of the record."""
        return self.__pull_commits

    @property
    def is_present_in_chapters(self) -> bool:
        """Check if the record is present in chapters."""
        return self.__present_in_chapters > 0

    @property
    def skip(self) -> bool:
        """Check if the record should be skipped during output generation process."""
        return self.__skip

    @property
    def is_pr(self) -> bool:
        """Check if the record is a pull request."""
        return self.__gh_issue is None and len(self.__pulls) == 1

    @property
    def is_issue(self) -> bool:
        """Check if the record is an issue."""
        return self.__gh_issue is not None

    @property
    def is_closed(self) -> bool:
        """Check if the record is closed."""
        if self.__gh_issue is None:
            # no issue ==> stand-alone PR
            return self.__pulls[0].state == PR_STATE_CLOSED

        return self.__gh_issue.state == ISSUE_STATE_CLOSED

    @property
    def is_closed_issue(self) -> bool:
        """Check if the record is a closed issue."""
        return self.is_issue and self.__gh_issue.state == ISSUE_STATE_CLOSED  # type: ignore[union-attr]
        # mypy: check for None done first

    @property
    def is_open_issue(self) -> bool:
        """Check if the record is an open issue."""
        return self.is_issue and self.__gh_issue.state == ISSUE_STATE_OPEN  # type: ignore[union-attr]
        # mypy: check for None done first

    @property
    def is_merged_pr(self) -> bool:
        """Check if the record is a merged pull request."""
        if self.__gh_issue is None:
            return self.is_pull_request_merged(self.__pulls[0])
        return False

    @property
    def labels(self) -> list[str]:
        """Getter for the labels of the record."""
        if self.__gh_issue is None:
            return [label.name for label in self.__pulls[0].labels]

        return [label.name for label in self.__gh_issue.labels]

    def get_rls_notes(self, detection_pattern: str, line_marks: Optional[list[str]] = None) -> str:
        """
        Gets the release notes of the record.

        @param detection_pattern: The detection pattern (regex allowed) to use.
        @param line_marks: The line marks to use.
        @return: The release notes of the record as a string.
        """
        if line_marks is None:
            line_marks = RELEASE_NOTE_LINE_MARKS

        release_notes = ""

        # Compile the regex pattern for efficiency
        detection_regex = re.compile(detection_pattern)

        # Iterate over all PRs
        for pull in self.__pulls:
            body_lines = pull.body.split("\n") if pull.body is not None else []
            inside_release_notes = False

            for line in body_lines:
                stripped_line = line.strip()
                if len(stripped_line) == 0:
                    # skip empty lines as they are not relevant
                    continue

                if detection_regex.search(line):  # Use regex search
                    inside_release_notes = True
                    continue

                if inside_release_notes:
                    tmp = line.strip()
                    if len(tmp) > 0 and tmp[0] in line_marks:
                        release_notes += f"  {line.rstrip()}\n"
                    else:
                        break

        # Return the concatenated release notes
        return release_notes.rstrip()

    @property
    def contains_release_notes(self) -> bool:
        """Checks if the record contains release notes."""
        if self.__is_release_note_detected:
            return self.__is_release_note_detected

        rls_notes: str = self.get_rls_notes(detection_pattern=ActionInputs.get_release_notes_title())
        if any(mark in rls_notes for mark in RELEASE_NOTE_LINE_MARKS):
            self.__is_release_note_detected = True

        return self.__is_release_note_detected

    @property
    def pulls_count(self) -> int:
        """Getter for the count of pull requests of the record."""
        return len(self.__pulls)

    @property
    def pr_contains_issue_mentions(self) -> bool:
        """Checks if the pull request contains issue mentions."""
        return len(extract_issue_numbers_from_body(self.__pulls[0])) > 0

    @property
    def authors(self) -> Optional[str]:
        """Getter for the authors of the record."""
        return None
        # TODO in Issue named 'Chapter line formatting - authors'
        # authors: list[str] = []
        #
        # for pull in self.__pulls:
        #     if pull.author is not None:
        #         authors.append(f"@{pull.author}")
        #
        # if len(authors) > 0:
        #     return None
        #
        # res = ", ".join(authors)
        # return res

    @property
    def contributors(self) -> Optional[str]:
        """Getter for the contributors of the record."""
        return None

    @property
    def pr_links(self) -> Optional[str]:
        """Getter for the pull request links of the record."""
        if len(self.__pulls) == 0:
            return None

        template = "#{number}"
        res = [template.format(number=pull.number) for pull in self.__pulls]

        return ", ".join(res)

    def pull_request_commit_count(self, pull_number: int = 0) -> int:
        """
        Get count of commits in all record pull requests.

        @param pull_number: The number of the pull request.
        @return: The count of commits in the pull request.
        """
        for pull in self.__pulls:
            if pull.number == pull_number:
                if pull.number in self.__pull_commits:
                    pull_commits = self.__pull_commits.get(pull.number)
                    return len(pull_commits) if pull_commits is not None else 0

                return 0

        return 0

    def pull_request(self, index: int = 0) -> Optional[PullRequest]:
        """
        Gets a pull request associated with the record.

        @param index: The index of the pull request.
        @return: The PullRequest instance.
        """
        if index < 0 or index >= len(self.__pulls):
            return None
        return self.__pulls[index]

    def register_pull_request(self, pull) -> None:
        """
        Registers a pull request with the record.

        @param pull: The PullRequest object to register.
        @return: None
        """
        self.__pulls.append(pull)

    def register_commit(self, commit: Commit) -> None:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: None
        """
        for pull in self.__pulls:
            if commit.sha == pull.merge_commit_sha:
                if self.__pull_commits.get(pull.number) is None:
                    self.__pull_commits[pull.number] = []
                self.__pull_commits[pull.number].append(commit)
                return

        logger.error("Commit %s not registered in any PR of record %s", commit.sha, self.number)

    def to_chapter_row(self) -> str:
        """
        Converts the record to a string row in a chapter.

        @return: The record as a row string.
        """
        self.increment_present_in_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""
        format_values = {}

        if self.__gh_issue is None:
            p = self.__pulls[0]
            format_values["number"] = f"#{p.number}"
            format_values["title"] = p.title
            format_values["authors"] = self.authors if self.authors is not None else ""
            format_values["contributors"] = self.contributors if self.contributors is not None else ""

            pr_prefix = "PR: " if ActionInputs.get_row_format_link_pr() else ""
            row = f"{row_prefix}{pr_prefix}" + ActionInputs.get_row_format_pr().format(**format_values)

        else:
            format_values["number"] = f"#{self.__gh_issue.number}"
            format_values["title"] = self.__gh_issue.title
            pr_links: str = self.pr_links if self.pr_links is not None else ""
            format_values["pull-requests"] = pr_links if len(self.__pulls) > 0 else ""
            format_values["authors"] = self.authors if self.authors is not None else ""
            format_values["contributors"] = self.contributors if self.contributors is not None else ""

            row = f"{row_prefix}" + ActionInputs.get_row_format_issue().format(**format_values)

        if self.contains_release_notes:
            row = f"{row}\n{self.get_rls_notes(detection_pattern=ActionInputs.get_release_notes_title())}"

        return row

    def contains_min_one_label(self, labels: list[str]) -> bool:
        """
        Check if the record contains at least one of the specified labels.

        @param labels: A list of labels to check for.
        @return: A boolean indicating whether the record contains any of the specified labels.
        """
        for lbl in self.labels:
            if lbl in labels:
                return True
        return False

    def contain_all_labels(self, labels: list[str]) -> bool:
        """
        Check if the record contains all of the specified labels.

        @param labels: A list of labels to check for.
        @return: A boolean indicating whether the record contains all of the specified
        """
        if len(self.labels) != len(labels):
            return False

        for lbl in self.labels:
            if lbl not in labels:
                return False
        return True

    def increment_present_in_chapters(self) -> None:
        """
        Increments the count of chapters in which the record is present.

        @return: None
        """
        self.__present_in_chapters += 1

    def present_in_chapters(self) -> int:
        """
        Gets the count of chapters in which the record is present.

        @return: The count of chapters in which the record is present.
        """
        return self.__present_in_chapters

    def is_commit_sha_present(self, sha: str) -> bool:
        """
        Checks if the specified commit SHA is present in the record.

        @param sha: The commit SHA to check for.
        @return: A boolean indicating whether the specified commit SHA is present in the record.
        """
        for pull in self.__pulls:
            if pull.merge_commit_sha == sha:
                return True

        return False

    @staticmethod
    def is_pull_request_merged(pull: PullRequest) -> bool:
        """
        Checks if the pull request is merged.

        @param pull: The pull request to check.
        @return: A boolean indicating whether the pull request is merged.
        """
        return pull.state == PR_STATE_CLOSED and pull.merged_at is not None and pull.closed_at is not None
