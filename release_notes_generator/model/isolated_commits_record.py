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
import sys
from typing import Optional

from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.record import Record
from release_notes_generator.utils.constants import (
    RELEASE_NOTE_DETECTION_PATTERN,
    RELEASE_NOTE_LINE_MARK,
)

logger = logging.getLogger(__name__)


class IsolatedCommitsRecord(Record):
    """
    A class used to represent a record in the release notes.
    The record holds isolated commit without link to Issue or Pull request.
    """

    def __init__(self, repo: Repository):
        super().__init__(repo)
        self.__commits: dict = {}

    @property
    def number(self) -> int:
        """Getter for the number of the record."""
        return sys.maxsize

    @property
    def commits(self) -> dict:
        return self.__commits

    @property
    def is_pr(self) -> bool:
        """Check if the record is a pull request."""
        return False

    @property
    def is_issue(self) -> bool:
        """Check if the record is an issue."""
        return False

    @property
    def is_closed(self) -> bool:
        return False

    @property
    def is_merged_pr(self) -> bool:
        return False

    @property
    def labels(self) -> list[str]:
        return []

    def get_rls_notes(self, detection_pattern=RELEASE_NOTE_DETECTION_PATTERN, line_mark=RELEASE_NOTE_LINE_MARK) -> str:
        return ""

    @property
    def contains_release_notes(self) -> bool:
        return False

    @property
    def pr_contains_issue_mentions(self) -> bool:
        return False

    @property
    def assignee(self) -> Optional[str]:
        return None

    @property
    def assignees(self) -> Optional[str]:
        return None

    @property
    def developers(self) -> Optional[str]:
        return None

    @property
    def contributors(self) -> Optional[str]:
        return None

    @property
    def pr_links(self) -> Optional[str]:
        return None

    def pull_request_commit_count(self, pull_number: int = 0) -> int:
        return len(self.commits)

    def pull_request(self, index: int = 0) -> Optional[PullRequest]:
        return None

    def register_pull_request(self, pull) -> None:
        pass

    def register_commit(self, commit: Commit) -> bool:
        """
        Registers a commit with the record.

        @param commit: The Commit object to register.
        @return: Always return True.
        """
        self.__commits[0] = commit
        logger.debug("Commit 'type: Isolated' %s registered", commit.sha)
        return True

    def to_chapter_row(self) -> str:
        """
        Converts the record to a string row in a chapter.

        @return: The record as a row string.
        """
        self.increment_present_in_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""
        return f"{row_prefix}Commit: {self.commits[0].sha}"

    def __get_row_format_values(self, row_format: str) -> dict:
        return {}

    def contains_min_one_label(self, labels: list[str]) -> bool:
        return False

    def contain_all_labels(self, labels: list[str]) -> bool:
        return False

    @staticmethod
    def is_pull_request_merged(pull: PullRequest) -> bool:
        return False
