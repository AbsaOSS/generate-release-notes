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
from release_notes_generator.utils.constants import (
    RELEASE_NOTE_DETECTION_PATTERN,
    RELEASE_NOTE_LINE_MARK,
)

logger = logging.getLogger(__name__)


class CommitRecord(Record):
    """
    A class used to represent a record in the release notes.
    The record represent an isolated commit without link to Issue or Pull request. Direct commit to master.
    """

    def __init__(self, repo: Repository, safe_call):
        super().__init__(repo, safe_call)

        self.__commit: Optional[Commit] = None

    @property
    def issue(self) -> Optional[Issue]:
        """Get the issue of the record."""
        return None

    @property
    def pull_requests(self) -> list[PullRequest]:
        """Get the pull requests of the record."""
        return []

    @property
    def commits(self) -> list[Commit]:
        """Get the commits of the record."""
        return [self.__commit] if self.__commit is not None else []

    @property
    def id(self) -> Optional[int | str]:
        """Get the id of the record."""
        return self.__commit.sha if self.__commit is not None else None

    @property
    def labels(self) -> list[str]:
        """Get the labels of the record."""
        return []

    @property
    def assignee(self) -> Optional[str]:
        """Get the assignee of the record."""
        return f"{self.commits[0].author.login}" if self.commits else None

    @property
    def assignees(self) -> Optional[str]:
        """Get the assignees of the record."""
        return f"{self.commits[0].author.login}" if self.commits else None

    @property
    def developers(self) -> Optional[str]:
        """Get the developers of the record."""
        return f"@{self.commits[0].author.login}" if self.commits else None

    @property
    def contributors(self) -> Optional[str]:
        """Get the contributors of the record."""
        logins = self.get_contributors_for_commit(self.__commit)
        return ", ".join(logins) if len(logins) > 0 else None

    def is_state(self, state: str) -> bool:
        """Check if the record is in the given state."""
        return False

    def get_rls_notes(self, detection_pattern=RELEASE_NOTE_DETECTION_PATTERN, line_mark=RELEASE_NOTE_LINE_MARK) -> str:
        """Get the release notes of the record."""
        return ""

    def pr_contains_issue_mentions(self) -> bool:
        """Check if the record's pull request contains issue mentions."""
        return False

    def pr_links(self) -> Optional[str]:
        """Get the pull request links of the record."""
        return None

    def register_pull_request(self, pr: PullRequest) -> None:
        """Register a pull request with the record."""
        pass

    def register_commit(self, commit: Commit) -> bool:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: Always return True.
        """
        self.__commit = commit
        logger.debug("Registering commit 'type: Isolated' sha: %s", commit.sha)
        return True

    def to_chapter_row(self) -> str:
        """
        Converts the record to a string row usable in a chapter.

        @return: The record as a row string.
        """
        self.increment_present_in_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters > 1 else ""
        format_values = {
            "sha": self.__commit.sha if self.__commit is not None else None,
        }

        format_values.update(self._get_row_format_values(ActionInputs.get_row_format_commit()))

        prefix = "Commit: " if ActionInputs.get_row_format_link_commit() else ""
        row = f"{row_prefix}{prefix}" + ActionInputs.get_row_format_commit().format(**format_values)
        if self.contains_release_notes():
            row = f"{row}\n{self.get_rls_notes()}"

        return row.replace("  ", " ")

    def fetch_pr_commits(self) -> None:
        """Fetch the pull request commits of the record."""
        pass

    def get_sha_of_all_commits(self) -> set[str]:
        """Get the set of all commit shas of the record."""
        pass
