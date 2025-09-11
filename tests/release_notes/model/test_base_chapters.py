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

from release_notes_generator.chapters.base_chapters import BaseChapters


# Local Record class for testing
# pylint: disable=too-few-public-methods
class Record:
    pass


# Local Chapters class for testing
class Chapters(BaseChapters):
    def populate(self, records: dict[int, Record]):
        pass  # Implement a minimal populate method for testing


def test_add_row():
    chapters = Chapters()
    chapters.add_row("Chapter 1", 1, "Row 1")

    assert "Chapter 1" in chapters.chapters
    assert chapters.chapters["Chapter 1"].rows[1] == "Row 1"


def test_to_string():
    chapters = Chapters()
    chapters.add_row("Chapter 1", 1, "Row 1")
    chapters.add_row("Chapter 1", 2, "Row 2")

    result = chapters.to_string()

    assert "Row 1" in result
    assert "Row 2" in result


def test_titles():
    chapters = Chapters()
    chapters.add_row("Chapter 1", 1, "Row 1")
    chapters.add_row("Chapter 2", 2, "Row 2")

    titles = chapters.titles

    assert "Chapter 1" in titles
    assert "Chapter 2" in titles


def test_sort_ascending():
    chapters = Chapters()
    chapters.sort_ascending = False
    chapters.add_row("Chapter 1", 1, "Row 1")
    chapters.add_row("Chapter 1", 2, "Row 2")

    result = chapters.to_string()
    print(result)

    assert "- Row 2" == result.split("\n")[1]
    assert "- Row 1" == result.split("\n")[2]


def test_print_empty_chapters():
    chapters = Chapters()
    chapters.print_empty_chapters = False
    chapters.add_row("Chapter 1", 1, "Row 1")

    result = chapters.to_string()

    assert "Chapter 1" in result
