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

from typing import Optional, Any, Dict, List

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
from release_notes_generator.utils.pull_request_utils import extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Record:
    """
    A class used to represent a record in the release notes.
    """

    def __init__(self, issue: Optional[Issue] = None, skip: bool = False):
        self._gh_issue: Optional[Issue] = issue
        self._pulls: list[PullRequest] = []
        # int - pr.number, list[Commit] - commits in the PR
        self._pull_commits: dict[int, list[Commit]] = {}

        self._is_release_note_detected: bool = False
        self._present_in_chapters = 0
        self._skip = skip

    @property
    def number(self) -> int:
        """Getter for the number of the record."""
        if self._gh_issue is None:
            return self._pulls[0].number
        return self._gh_issue.number

    @property
    def issue(self) -> Optional[Issue]:
        """Getter for the issue of the record."""
        return self._gh_issue

    @property
    def pulls(self) -> list[PullRequest]:
        """Getter for the pull requests of the record."""
        return self._pulls

    @property
    def commits(self) -> dict:
        """Getter for the commits of the record."""
        return self._pull_commits

    @property
    def is_present_in_chapters(self) -> bool:
        """Check if the record is present in chapters."""
        return self._present_in_chapters > 0

    @property
    def skip(self) -> bool:
        """Check if the record should be skipped during output generation process."""
        return self._skip

    @property
    def is_pr(self) -> bool:
        """Check if the record is a pull request."""
        return self._gh_issue is None and len(self._pulls) == 1

    @property
    def is_issue(self) -> bool:
        """Check if the record is an issue."""
        return self._gh_issue is not None

    @property
    def is_closed(self) -> bool:
        """Check if the record is closed."""
        if self._gh_issue is None:
            # no issue ==> stand-alone PR
            return self._pulls[0].state == PR_STATE_CLOSED

        return self._gh_issue.state == ISSUE_STATE_CLOSED

    @property
    def is_closed_issue(self) -> bool:
        """Check if the record is a closed issue."""
        return self.is_issue and self._gh_issue.state == ISSUE_STATE_CLOSED  # type: ignore[union-attr]
        # mypy: check for None done first

    @property
    def is_open_issue(self) -> bool:
        """Check if the record is an open issue."""
        return self.is_issue and self._gh_issue.state == ISSUE_STATE_OPEN  # type: ignore[union-attr]
        # mypy: check for None done first

    @property
    def is_merged_pr(self) -> bool:
        """Check if the record is a merged pull request."""
        if self._gh_issue is None:
            return self.is_pull_request_merged(self._pulls[0])
        return False

    @property
    def labels(self) -> list[str]:
        """Getter for the labels of the record."""
        if self._gh_issue is None:
            return [label.name for label in self._pulls[0].labels]

        return [label.name for label in self._gh_issue.labels]

    def get_rls_notes(self, line_marks: Optional[list[str]] = None) -> str:
        """
        Gets the release notes of the record.

        @param line_marks: The line marks to use.
        @return: The release notes of the record as a string.
        """
        release_notes = ""
        detection_pattern = ActionInputs.get_release_notes_title()

        if line_marks is None:
            line_marks = RELEASE_NOTE_LINE_MARKS

        # Compile the regex pattern for efficiency
        detection_regex = re.compile(detection_pattern)
        cr_active: bool = ActionInputs.is_coderabbit_support_active()
        cr_detection_regex: Optional[re.Pattern[Any]] = (
            re.compile(ActionInputs.get_coderabbit_release_notes_title()) if cr_active else None
        )

        # Iterate over all PRs
        for pull in self._pulls:
            if pull.body and detection_regex.search(pull.body):
                release_notes += self.__get_rls_notes_default(pull, line_marks, detection_regex)
            elif pull.body and cr_active and cr_detection_regex.search(pull.body):  # type: ignore[union-attr]
                release_notes += self.__get_rls_notes_code_rabbit(pull, line_marks,
                                                                  cr_detection_regex)  # type: ignore[arg-type]

        # Return the concatenated release notes
        return release_notes.rstrip()

    def __get_rls_notes_default(
        self, pull: PullRequest, line_marks: list[str], detection_regex: re.Pattern[str]
    ) -> str:
        if not pull.body:
            return ""

        lines = pull.body.splitlines()
        release_notes_lines = []

        found_section = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if not found_section:
                if detection_regex.search(line):
                    found_section = True
                continue

            if stripped[0] in line_marks:
                release_notes_lines.append(f"  {line.rstrip()}")
            else:
                break

        return "\n".join(release_notes_lines) + ("\n" if release_notes_lines else "")

    def __get_rls_notes_code_rabbit(
        self, pull: PullRequest, line_marks: list[str], cr_detection_regex: re.Pattern[str]
    ) -> str:
        if not pull.body:
            return ""

        lines = pull.body.splitlines()
        ignore_groups: list[str] = ActionInputs.get_coderabbit_summary_ignore_groups()
        release_notes_lines = []

        inside_section = False
        skipping_group = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if not inside_section:
                if cr_detection_regex.search(line):
                    inside_section = True
                continue

            if inside_section:
                # Check if this is a bold group heading
                if line[0] in line_marks and "**" in stripped:
                    # Group heading – check if it should be skipped
                    group_name = stripped.split("**")[1]
                    skipping_group = any(group.lower() == group_name.lower() for group in ignore_groups)
                    continue

                if skipping_group and line.startswith("  - "):
                    continue

                if stripped[0] in line_marks and line.startswith("  - "):
                    release_notes_lines.append(line.rstrip())
                else:
                    break

        return "\n".join(release_notes_lines) + ("\n" if release_notes_lines else "")

    @property
    def contains_release_notes(self) -> bool:
        """Checks if the record contains release notes."""
        if self._is_release_note_detected:
            return self._is_release_note_detected

        rls_notes: str = self.get_rls_notes()
        if any(mark in rls_notes for mark in RELEASE_NOTE_LINE_MARKS):
            self._is_release_note_detected = True

        return self._is_release_note_detected

    @property
    def pulls_count(self) -> int:
        """Getter for the count of pull requests of the record."""
        return len(self._pulls)

    @property
    def pr_contains_issue_mentions(self) -> bool:
        """Checks if the pull request contains issue mentions."""
        # TODO call both and merge solve in issue #153
        return len(extract_issue_numbers_from_body(self._pulls[0])) > 0

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
        if len(self._pulls) == 0:
            return None

        template = "#{number}"
        res = [template.format(number=pull.number) for pull in self._pulls]

        return ", ".join(res)

    def pull_request_commit_count(self, pull_number: int = 0) -> int:
        """
        Get count of commits in all record pull requests.

        @param pull_number: The number of the pull request.
        @return: The count of commits in the pull request.
        """
        for pull in self._pulls:
            if pull.number == pull_number:
                if pull.number in self._pull_commits:
                    pull_commits = self._pull_commits.get(pull.number)
                    return len(pull_commits) if pull_commits is not None else 0

                return 0

        return 0

    def pull_request(self, index: int = 0) -> Optional[PullRequest]:
        """
        Gets a pull request associated with the record.

        @param index: The index of the pull request.
        @return: The PullRequest instance.
        """
        if index < 0 or index >= len(self._pulls):
            return None
        return self._pulls[index]

    def register_pull_request(self, pull) -> None:
        """
        Registers a pull request with the record.

        @param pull: The PullRequest object to register.
        @return: None
        """
        self._pulls.append(pull)

    def register_commit(self, commit: Commit) -> None:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: None
        """
        for pull in self._pulls:
            if commit.sha == pull.merge_commit_sha:
                if self._pull_commits.get(pull.number) is None:
                    self._pull_commits[pull.number] = []
                self._pull_commits[pull.number].append(commit)
                return

        logger.error("Commit %s not registered in any PR of record %s", commit.sha, self.number)

    def to_chapter_row(self) -> str:
        """
        Converts the record to a string row in a chapter.

        @return: The record as a row string.
        """
        # TODO - create a version on child classes #152
        self.increment_present_in_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""
        format_values = {}

        if isinstance(self, CommitRecord):
            commit_message = self._pull_commits[0][0].commit.message.replace("\n", " ")
            row = f"{row_prefix}Commit: {self._pull_commits[0][0].sha[:7]} - {commit_message}"
        elif self._gh_issue is None:
            p = self._pulls[0]
            format_values["number"] = f"#{p.number}"
            format_values["title"] = p.title
            format_values["authors"] = self.authors if self.authors is not None else ""
            format_values["contributors"] = self.contributors if self.contributors is not None else ""

            pr_prefix = "PR: " if ActionInputs.get_row_format_link_pr() else ""
            row = f"{row_prefix}{pr_prefix}" + ActionInputs.get_row_format_pr().format(**format_values)
        else:
            format_values["number"] = f"#{self._gh_issue.number}"
            format_values["title"] = self._gh_issue.title
            pr_links: str = self.pr_links if self.pr_links is not None else ""
            format_values["pull-requests"] = pr_links if len(self._pulls) > 0 else ""
            format_values["authors"] = self.authors if self.authors is not None else ""
            format_values["contributors"] = self.contributors if self.contributors is not None else ""

            row = f"{row_prefix}" + ActionInputs.get_row_format_issue().format(**format_values)

        if self.contains_release_notes:
            row = f"{row}\n{self.get_rls_notes()}"

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
        self._present_in_chapters += 1

    def present_in_chapters(self) -> int:
        """
        Gets the count of chapters in which the record is present.

        @return: The count of chapters in which the record is present.
        """
        return self._present_in_chapters

    def is_commit_sha_present(self, sha: str) -> bool:
        """
        Checks if the specified commit SHA is present in the record.

        @param sha: The commit SHA to check for.
        @return: A boolean indicating whether the specified commit SHA is present in the record.
        """
        return any(pull.merge_commit_sha == sha for pull in self._pulls)

    @staticmethod
    def is_pull_request_merged(pull: PullRequest) -> bool:
        """
        Checks if the pull request is merged.

        @param pull: The pull request to check.
        @return: A boolean indicating whether the pull request is merged.
        """
        return pull.state == PR_STATE_CLOSED and pull.merged_at is not None and pull.closed_at is not None


class PullRequestRecord(Record):
    """
    A class used to represent a pull request record in the release notes.
    Inherits from Record and provides additional functionality specific to pull requests.
    """

    def __init__(self, pull: PullRequest, skip: bool = False):
        super().__init__(issue=None, skip=skip)
        self.register_pull_request(pull)
        self.__is_release_note_detected = self.contains_release_notes
        self.__issues: Dict[int, List[Issue]] = {}


class IssueRecord(Record):
    """
    A class used to represent an issue record in the release notes.
    Inherits from Record and provides additional functionality specific to issues.
    """

    def __init__(self, issue: Issue, skip: bool = False):
        super().__init__(issue=issue, skip=skip)
        self.__is_release_note_detected = self.contains_release_notes


class CommitRecord(Record):
    """
    A class used to represent a direct commit record in the release notes.
    Inherits from Record and provides additional functionality specific to direct commits.
    """

    def __init__(self, commit: Commit, skip: bool = False):
        super().__init__(issue=None, skip=skip)
        self._pull_commits[0] = [commit]  # Using 0 as a placeholder for direct commits
        self.__is_release_note_detected = False
