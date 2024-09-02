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
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.model.record import Record


# __init__

def test_chapters_init(custom_chapters):
    assert custom_chapters.sort_ascending
    assert custom_chapters.chapters['Chapter 1'].labels == ['bug', 'enhancement']
    assert custom_chapters.chapters['Chapter 2'].labels == ['feature']


# populate

def test_populate(custom_chapters, mocker):
    record1 = mocker.Mock(spec=Record)
    record1.labels = ['bug']
    record1.pulls_count = 1
    record1.is_present_in_chapters = False
    record1.to_chapter_row.return_value = "Record 1 Chapter Row"

    record2 = mocker.Mock(spec=Record)
    record2.labels = ['enhancement']
    record2.pulls_count = 1
    record2.is_present_in_chapters = False
    record2.to_chapter_row.return_value = "Record 2 Chapter Row"

    record3 = mocker.Mock(spec=Record)
    record3.labels = ['feature']
    record3.pulls_count = 1
    record3.is_present_in_chapters = False
    record3.to_chapter_row.return_value = "Record 3 Chapter Row"

    records = {
        1: record1,
        2: record2,
        3: record3,
    }

    custom_chapters.populate(records)

    assert 1 in custom_chapters.chapters['Chapter 1'].rows
    assert custom_chapters.chapters['Chapter 1'].rows[1] == "Record 1 Chapter Row"
    assert 2 in custom_chapters.chapters['Chapter 1'].rows
    assert custom_chapters.chapters['Chapter 1'].rows[2] == "Record 2 Chapter Row"
    assert 3 in custom_chapters.chapters['Chapter 2'].rows
    assert custom_chapters.chapters['Chapter 2'].rows[3] == "Record 3 Chapter Row"


def test_populate_no_pulls_count(custom_chapters, mocker):
    record1 = mocker.Mock(spec=Record)
    record1.labels = ['bug']
    record1.pulls_count = 0
    record1.is_present_in_chapters = False

    records = {
        1: record1,
    }

    custom_chapters.populate(records)
    assert 1 not in custom_chapters.chapters['Chapter 1'].rows


def test_populate_no_matching_labels(custom_chapters, mocker):
    record1 = mocker.Mock(spec=Record)
    record1.labels = ['non-existent-label']
    record1.pulls_count = 1
    record1.is_present_in_chapters = False

    records = {
        1: record1,
    }

    custom_chapters.populate(records)
    assert 1 not in custom_chapters.chapters['Chapter 1'].rows
    assert 1 not in custom_chapters.chapters['Chapter 2'].rows


# from_json

def test_custom_chapters_from_json():
    custom_chapters = CustomChapters()
    json_string = '''
    [
        {"title": "Breaking Changes 💥", "label": "breaking-change"},
        {"title": "New Features 🎉", "label": "enhancement"},
        {"title": "New Features 🎉", "label": "feature"},
        {"title": "Bugfixes 🛠", "label": "bug"}
    ]
    '''
    custom_chapters.from_json(json_string)

    assert "Breaking Changes 💥" in custom_chapters.titles
    assert "New Features 🎉" in custom_chapters.titles
    assert "Bugfixes 🛠" in custom_chapters.titles
    assert isinstance(custom_chapters.chapters["Breaking Changes 💥"], Chapter)
    assert isinstance(custom_chapters.chapters["New Features 🎉"], Chapter)
    assert isinstance(custom_chapters.chapters["Bugfixes 🛠"], Chapter)
    assert ["breaking-change"] == custom_chapters.chapters["Breaking Changes 💥"].labels
    assert ["enhancement", "feature"] == custom_chapters.chapters["New Features 🎉"].labels
    assert ["bug"] == custom_chapters.chapters["Bugfixes 🛠"].labels
