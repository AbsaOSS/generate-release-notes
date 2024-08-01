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

from release_notes_generator.model.chapter import Chapter


# __init__

def test_chapter_init():
    chapter = Chapter("Test Title", ["label1", "label2"])

    assert chapter.title == "Test Title"
    assert chapter.labels == ["label1", "label2"]
    assert chapter.rows == {}


# add_row

def test_add_row():
    chapter = Chapter("Test Title", ["label1", "label2"])
    chapter.add_row(1, "Test Row")

    assert {1: "Test Row"} == chapter.rows


# to_string

def test_to_string_ascending():
    chapter = Chapter("Test Title", ["label1", "label2"])
    chapter.add_row(1, "Test Row 1")
    chapter.add_row(2, "Test Row 2")
    expected_output = "### Test Title\n- Test Row 1\n- Test Row 2"

    assert expected_output == chapter.to_string(sort_ascending=True)


def test_to_string_descending():
    chapter = Chapter("Test Title", ["label1", "label2"])
    chapter.add_row(1, "Test Row 1")
    chapter.add_row(2, "Test Row 2")
    expected_output = "### Test Title\n- Test Row 2\n- Test Row 1"

    assert expected_output == chapter.to_string(sort_ascending=False)


def test_to_string_print_empty_chapters():
    chapter = Chapter("Test Title", ["label1", "label2"])
    expected_output = "### Test Title\nNo entries detected."

    assert expected_output == chapter.to_string()


def test_to_string_not_print_empty_chapters():
    chapter = Chapter("Test Title", ["label1", "label2"])
    expected_output = ""

    assert expected_output == chapter.to_string(print_empty_chapters=False)
