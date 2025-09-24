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
from abc import ABCMeta, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Record(metaclass=ABCMeta):
    """
    A class used to represent an abstract record in the release notes.
    """

    RELEASE_NOTE_LINE_MARKS: list[str] = ["-", "*", "+"]

    def __init__(self, labels: Optional[list[str]] = None, skip: bool = False):
        self._present_in_chapters = 0
        self._skip = skip
        self._is_release_note_detected: Optional[bool] = None
        self._labels: Optional[list[str]] = labels if labels is not None else None
        self._rls_notes: Optional[str] = None  # single annotation here

    # properties
    @property
    def is_present_in_chapters(self) -> bool:
        """
        Checks if the record is present in any chapter.
        Returns:
            bool: True if the record is present in at least one chapter, False otherwise.
        """
        return self._present_in_chapters > 0

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
    def authors(self) -> list[str]:
        """
        Getter for the authors of the record.
        Returns:
            list[str]: A list of authors associated with the record.
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
    def get_labels(self) -> list[str]:
        """
        Gets the labels of the record.
        Returns:
            set[str]: A list of labels associated with the record.
        """

    @abstractmethod
    def get_rls_notes(self, line_marks: Optional[list[str]] = None) -> str:
        """
        Gets the release notes of the record.

        @param line_marks: The line marks to use.
        @return: The release notes of the record as a string.
        """

    # shared methods
    def added_into_chapters(self) -> None:
        """
        Increments the count of chapters in which the record is present.
        Returns: None
        """
        self._present_in_chapters += 1
        # TODO - this is wrong - it does not count chapters but conversions

    def present_in_chapters(self) -> int:
        """
        Gets the count of chapters in which the record is present.
        Returns:
            int: The count of chapters in which the record is present.
        """
        return self._present_in_chapters

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
        if len(self.labels) != len(labels):
            return False

        for lbl in self.labels:
            if lbl not in labels:
                return False
        return True

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
