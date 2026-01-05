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
This module contains the BaseChapters class, which is responsible for representing the base chapters.
"""

import logging
import re
from abc import ABCMeta, abstractmethod
from typing import Optional

from release_notes_generator.action_inputs import ActionInputs

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Record(metaclass=ABCMeta):
    """
    A class used to represent an abstract record in the release notes.
    """

    RELEASE_NOTE_LINE_MARKS: list[str] = ["-", "*", "+"]

    def __init__(self, labels: Optional[list[str]] = None, skip: bool = False):
        self._present_in_chapters: set[str] = set()
        self._skip = skip
        self._is_cross_repo: bool = False
        self._is_release_note_detected: Optional[bool] = None
        self._labels: Optional[list[str]] = labels
        self._rls_notes: Optional[str] = None  # single annotation here

    # properties
    @property
    def is_present_in_chapters(self) -> bool:
        """
        Checks if the record is present in any chapter.
        Returns:
            bool: True if the record is present in at least one chapter, False otherwise.
        """
        return len(self._present_in_chapters) > 0

    @property
    def is_cross_repo(self) -> bool:
        """
        Checks if the record is a cross-repo record.
        Returns:
            bool: True if the record is a cross-repo record, False otherwise.
        """
        return self._is_cross_repo

    @is_cross_repo.setter
    def is_cross_repo(self, value: bool) -> None:
        """
        Sets the cross-repo status of the record.
        Parameters:
            value (bool): The cross-repo status to set.
        """
        self._is_cross_repo = value

    @property
    def skip(self) -> bool:
        """Check if the record should be skipped during output generation process."""
        return self._skip

    @property
    def labels(self) -> list[str]:
        """
        Gets the labels of the record.
        Returns:
            list[str]: A list of labels associated with the record.
        """
        if self._labels is None:
            self._labels = self.get_labels()

        return self._labels

    @property
    @abstractmethod
    def record_id(self) -> int | str:
        """
        Gets the unique identifier of the record.
        Returns:
            int | str: The unique identifier of the record.
        """

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        """
        Checks if the record is closed.
        Returns:
            bool: True if the record is closed, False otherwise.
        """

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """
        Checks if the record is open.
        Returns:
            bool: True if the record is open, False otherwise.
        """

    @property
    @abstractmethod
    def author(self) -> str:
        """
        Getter for the author of the record.
            - the issue or PR creator
        Returns:
            str: The author associated with the record.
        """

    @property
    @abstractmethod
    def assignees(self) -> list[str]:
        """
        Getter for the assignees of the record.
            - the issue or PR assignees
        Returns:
            list[str]: A list of assignees associated with the record.
        """

    @property
    @abstractmethod
    def developers(self) -> list[str]:
        """
        Getter for the developers of the record.
            - assignees
            - linked PR authors
            - commit authors
        Returns:
            list[str]: A list of developers associated with the record.
        """

    # abstract methods

    @abstractmethod
    def to_chapter_row(self, add_into_chapters: bool = True) -> str:
        """
        Converts the record to a string row in a chapter.

        Parameters:
            add_into_chapters (bool): Whether to increment the chapter count for this record.

        Returns:
            str: The string representation of the record in a chapter row.
        """

    @abstractmethod
    def contains_change_increment(self) -> bool:
        """
        Checks if the record contains a change increment.

        Returns:
            bool: True if the record contains a change increment, False otherwise.
        """

    @abstractmethod
    def get_labels(self) -> list[str]:
        """
        Gets the labels of the record.
        Returns:
            list[str]: A list of labels associated with the record.
        """

    @abstractmethod
    def get_rls_notes(self, line_marks: Optional[list[str]] = None) -> str:
        """
        Gets the release notes of the record.

        @param line_marks: The line marks to use.
        @return: The release notes of the record as a string.
        """

    # shared methods

    def added_into_chapters(self, chapter_id: str) -> None:
        """
        Adds a chapter identifier to track which chapters contain this record.

        Parameters:
            chapter_id (str): The unique identifier of the chapter.

        Returns:
            None
        """
        self._present_in_chapters.add(chapter_id)

    def present_in_chapters(self) -> int:
        """
        Gets the count of unique chapters in which the record is present.
        Returns:
            int: The count of unique chapters in which the record is present.
        """
        return len(self._present_in_chapters)

    def contains_min_one_label(self, labels: list[str]) -> bool:
        """
        Check if the record contains at least one of the specified labels.
        Parameters:
            labels (list[str]): List of labels to check.
        Returns:
            bool: True if the record contains at least one of the specified labels, False otherwise.
        """
        for lbl in self.labels:
            if lbl in labels:
                return True
        return False

    def contain_all_labels(self, labels: list[str]) -> bool:
        """
        Check if the record contains all of the specified labels.
        Parameters:
            labels (list[str]): List of labels to check.
        Returns:
            bool: True if the record contains all of the specified labels, False otherwise.
        """
        return all(lbl in self.labels for lbl in labels)

    def contains_release_notes(self, re_check: bool = False) -> bool:
        """
        Checks if the record contains release notes.

        Parameters:
            re_check (bool): Whether to re-check the release notes or use the cached value.

        Returns:
            bool: True if the record contains release notes, False otherwise.
        """
        if self._rls_notes is None or re_check:
            self._rls_notes = self.get_rls_notes()
        self._is_release_note_detected = bool(self._rls_notes and self._rls_notes.strip())
        return self._is_release_note_detected

    # shared protected methods

    def _get_rls_notes_setup(self, line_marks: Optional[list[str]] = None) -> tuple[re.Pattern[str], list[str], bool]:
        detection_pattern = ActionInputs.get_release_notes_title()

        if line_marks is None:
            line_marks = self.RELEASE_NOTE_LINE_MARKS

        # Compile detection regex
        detection_regex = re.compile(detection_pattern)

        return detection_regex, line_marks, ActionInputs.is_coderabbit_support_active()
