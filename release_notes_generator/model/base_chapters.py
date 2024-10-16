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

from abc import ABC, abstractmethod
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.record import Record


class BaseChapters(ABC):
    """
    An abstract base class representing the base chapters.
    """

    def __init__(self, sort_ascending: bool = True, print_empty_chapters: bool = True):
        self.sort_ascending = sort_ascending
        self.print_empty_chapters = print_empty_chapters
        self.chapters: dict[str, Chapter] = {}
        self.populated_record_numbers: list[int] = []

    @property
    def populated_record_numbers_list(self) -> list[int]:
        """
        Gets the list of populated record numbers.

        @return: A list of populated record numbers.
        """
        return self.populated_record_numbers

    def add_row(self, chapter_key: str, number: int, row: str) -> None:
        """
        Adds a row to a chapter.

        @param chapter_key: The key of the chapter.
        @param number: The number of the row.
        @param row: The row to add.
        @return: None
        """
        if chapter_key not in self.chapters:
            self.chapters[chapter_key] = Chapter(title=chapter_key)
        self.chapters[chapter_key].add_row(number, row)

    def to_string(self) -> str:
        """
        Converts the chapters to a string.

        @return: The chapters as a string.
        """
        result = ""
        for chapter in self.chapters.values():
            chapter_string = chapter.to_string(
                sort_ascending=self.sort_ascending, print_empty_chapters=self.print_empty_chapters
            )
            result += chapter_string + "\n\n"

        # Note: strip is required to remove leading newline chars when empty chapters are not printed option
        return result.strip()

    @property
    def titles(self) -> list[str]:
        """
        Gets the titles of the chapters.

        @return: A list of the titles of the chapters.
        """
        return [chapter.title for chapter in self.chapters.values()]

    @abstractmethod
    def populate(self, records: dict[int, Record]) -> None:
        """
        Populates the chapters with records.

        @param records: A dictionary of records where the key is an integer and the value is a Record object.
        """
