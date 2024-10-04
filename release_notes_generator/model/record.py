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
from release_notes_generator.utils.constants import (
    PR_STATE_CLOSED,
    ISSUE_STATE_CLOSED,
    ISSUE_STATE_OPEN,
    RELEASE_NOTE_DETECTION_PATTERN,
    RELEASE_NOTE_LINE_MARK,
)
from release_notes_generator.utils.pull_reuqest_utils import extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


# TODO - recheck the size of class, is there a way to reduce or split it?
# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Record:
    """
    A class used to represent a record in the release notes.
    """

    def __init__(self, repo: Repository, safe_call, issue: Optional[Issue] = None):
        self.__repo: Repository = repo
        self.__gh_issue: Issue = issue
        self.__pulls: list[PullRequest] = []
        self.__pull_commits: dict[int, list[Commit]] = {}

        self.__is_release_note_detected: bool = False
        self.__present_in_chapters = 0

        self._safe_call = safe_call

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
    def commits(self) -> dict[int, list[Commit]]:
        """Getter for the commits of the record."""
        return self.__pull_commits

    @property
    def is_present_in_chapters(self) -> bool:
        """Check if the record is present in chapters."""
        return self.__present_in_chapters > 0

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
        return self.is_issue and self.__gh_issue.state == ISSUE_STATE_CLOSED

    @property
    def is_open_issue(self) -> bool:
        """Check if the record is an open issue."""
        return self.is_issue and self.__gh_issue.state == ISSUE_STATE_OPEN

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
        for pull in self.__pulls:
            body_lines = pull.body.split("\n") if pull.body is not None else []
            inside_release_notes = False

            for line in body_lines:
                if detection_pattern in line:
                    inside_release_notes = True
                    continue

                if inside_release_notes:
                    if line.startswith(line_mark):
                        release_notes += f"  {line.strip()}\n"
                    else:
                        break

        # Return the concatenated release notes
        return release_notes.rstrip()

    @property
    def contains_release_notes(self) -> bool:
        """Checks if the record contains release notes."""
        if self.__is_release_note_detected:
            return self.__is_release_note_detected

        if RELEASE_NOTE_LINE_MARK in self.get_rls_notes():
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

    # Note: assignee & assignees are related to this GitHub Docs - https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users#about-issue-and-pull-request-assignees
    @property
    def assignee(self) -> Optional[str]:
        """Getter for the authors of the record."""
        if self.__gh_issue is None:
            return self.pulls[0].assignee.login if self.pulls[0].assignee is not None else None

        else:
            return self.issue.assignee.login if self.issue.assignee is not None else None

    @property
    def assignees(self) -> Optional[str]:
        """Getter for the assignees of the record."""
        if self.__gh_issue is None:
            logins = [a.login for a in self.pulls[0].assignees]
            return ", ".join(logins) if len(logins) > 0 else None

        else:
            logins = [a.login for a in self.issue.assignees]
            return ", ".join(logins) if len(logins) > 0 else None

    @property
    def developers(self) -> Optional[str]:
        """Getter for the developers of the record."""
        if self.is_issue:
            # is issue - go for its pulls
            logins = set()
            for commits in self.__pull_commits.values():
                for commit in commits:
                    if commit.author is not None:
                        logins.add(f"@{commit.author.login}")

            if not logins:
                logger.warning("Found issue record %s with %d pull requests and no commits", self.number, len(self.__pulls))
            return ", ".join(logins) if len(logins) > 0 else None

        elif self.is_pr:
            # is pr - go for its one pull only
            logins = {f"@{c.author.login}" for c in self.__pull_commits[self.pulls[0].number]}
            if not logins:
                logger.warning("Found pull request record '%s' with no commits", self.pulls[0].number)
            return ", ".join(logins) if len(logins) > 0 else None

        else:
            logger.warning("Record '%s' is not issue nor PR. Developers cannot be determined.", self.number)
            return None

    @property
    def contributors(self) -> Optional[str]:
        """Getter for the contributors of the record."""

        if not self.is_issue and not self.is_pr:
            logger.warning("Record '%s' is not issue nor PR. Contributors cannot be determined.", self.number)
            return None

        logins = []
        for commits in self.commits.values():
            for c in commits:
                for line in c.commit.message.split("\n"):
                    if "Co-authored-by:" in line:
                        name = line.split("Co-authored-by:")[1].strip()
                        if name not in logins:
                            logins.append(name)

        return ", ".join(logins) if len(logins) > 0 else None

    @property
    def pr_links(self) -> Optional[str]:
        """Getter for the pull request links of the record."""
        if len(self.__pulls) == 0:
            return None

        template = "[#{number}](https://github.com/{full_name}/pull/{number})"
        res = [template.format(number=pull.number, full_name=self.__repo.full_name) for pull in self.__pulls]

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
                    return len(self.__pull_commits.get(pull.number))

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

    def register_commit(self, commit: Commit) -> bool:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: None
        """
        sha = commit.sha
        for pull in self.__pulls:
            if sha == pull.merge_commit_sha or sha == pull.head.sha:
                if self.__pull_commits.get(pull.number) is None:
                    self.__pull_commits[pull.number] = []
                self.__pull_commits[pull.number].append(commit)
                logger.debug("Commit %s registered using sha in PR %s of record %s", commit.sha, pull.number, self.number)
                return True

        return False

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
            format_values["number"] = p.number
            format_values["title"] = p.title
            format_values.update(self.__get_row_format_values(ActionInputs.get_row_format_pr()))

            pr_prefix = "PR: " if ActionInputs.get_row_format_link_pr() else ""
            row = f"{row_prefix}{pr_prefix}" + ActionInputs.get_row_format_pr().format(**format_values)

        else:
            format_values["number"] = self.__gh_issue.number
            format_values["title"] = self.__gh_issue.title
            format_values["pull-requests"] = f"in {self.pr_links}" if len(self.__pulls) > 0 else ""
            format_values.update(self.__get_row_format_values(ActionInputs.get_row_format_issue()))

            row = f"{row_prefix}" + ActionInputs.get_row_format_issue().format(**format_values)

        if self.contains_release_notes:
            row = f"{row}\n{self.get_rls_notes()}"

        return row.replace("  ", " ")

    def __get_row_format_values(self, row_format: str) -> dict:
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
        if "{developed-by}" in row_format:
            developers = self.developers
            format_values["developed-by"] = f"developed by {developers}" if developers is not None else ""
        if "{co-authored-by}" in row_format:
            contributors = self.contributors
            format_values["co-authored-by"] = f"co-authored by {contributors}" if contributors is not None else ""

        return format_values


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

    @staticmethod
    def is_pull_request_merged(pull: PullRequest) -> bool:
        """
        Checks if the pull request is merged.

        @param pull: The pull request to check.
        @return: A boolean indicating whether the pull request is merged.
        """
        return pull.state == PR_STATE_CLOSED and pull.merged_at is not None and pull.closed_at is not None

    def get_commits(self) -> None:
        for pull in self.__pulls:
            self.__pull_commits[pull.number] = list(self._safe_call(pull.get_commits)())

    def get_commits_shas(self) -> set[str]:
        set_of_commit_shas = set()

        for commits in self.__pull_commits.values():
            for c in commits:
                set_of_commit_shas.add(c.sha)
                set_of_commit_shas.add(c.commit.sha)

        for pull in self.__pulls:
            set_of_commit_shas.add(pull.merge_commit_sha)

        return set_of_commit_shas
