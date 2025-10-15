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
import pytest

from release_notes_generator.model.chapter import Chapter
from release_notes_generator.chapters.custom_chapters import CustomChapters
from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.record import Record
from release_notes_generator.utils.enums import DuplicityScopeEnum


# __init__


def test_chapters_init(custom_chapters):
    assert custom_chapters.sort_ascending
    assert custom_chapters.chapters["Chapter 1"].labels == ["bug", "enhancement"]
    assert custom_chapters.chapters["Chapter 2"].labels == ["feature"]


# populate


def test_populate(custom_chapters, mocker):
    record1 = mocker.Mock(spec=Record)
    record1.labels = ["bug"]
    record1.pulls_count = 1
    record1.is_present_in_chapters = False
    record1.to_chapter_row.return_value = "Record 1 Chapter Row"
    record1.skip = False

    record2 = mocker.Mock(spec=Record)
    record2.labels = ["enhancement"]
    record2.pulls_count = 1
    record2.is_present_in_chapters = False
    record2.to_chapter_row.return_value = "Record 2 Chapter Row"
    record2.skip = False

    record3 = mocker.Mock(spec=Record)
    record3.labels = ["feature"]
    record3.pulls_count = 1
    record3.is_present_in_chapters = False
    record3.to_chapter_row.return_value = "Record 3 Chapter Row"
    record3.skip = False

    records = {
        "org/repo#1": record1,
        "org/repo#2": record2,
        "org/repo#3": record3,
    }

    custom_chapters.populate(records)

    assert "org/repo#1" in custom_chapters.chapters["Chapter 1"].rows
    assert custom_chapters.chapters["Chapter 1"].rows["org/repo#1"] == "Record 1 Chapter Row"
    assert "org/repo#2" in custom_chapters.chapters["Chapter 1"].rows
    assert custom_chapters.chapters["Chapter 1"].rows["org/repo#2"] == "Record 2 Chapter Row"
    assert "org/repo#3" in custom_chapters.chapters["Chapter 2"].rows
    assert custom_chapters.chapters["Chapter 2"].rows["org/repo#3"] == "Record 3 Chapter Row"


def test_populate_no_pulls_count(custom_chapters, mocker):
    record1 = mocker.Mock(spec=IssueRecord)
    record1.labels = ["bug"]
    record1.pulls_count = 0
    record1.is_present_in_chapters = False

    records = {
        1: record1,
    }

    custom_chapters.populate(records)
    assert 1 not in custom_chapters.chapters["Chapter 1"].rows


def test_populate_no_matching_labels(custom_chapters, mocker):
    record1 = mocker.Mock(spec=Record)
    record1.labels = ["non-existent-label"]
    record1.pulls_count = 1
    record1.is_present_in_chapters = False

    records = {
        1: record1,
    }

    custom_chapters.populate(records)
    assert 1 not in custom_chapters.chapters["Chapter 1"].rows
    assert 1 not in custom_chapters.chapters["Chapter 2"].rows


def test_populate_service_duplicity_scope(custom_chapters, mocker):
    record1 = mocker.Mock(spec=Record)
    record1.labels = ["bug", "feature"]
    record1.pulls_count = 1
    record1.is_present_in_chapters = False
    record1.to_chapter_row.return_value = "Record 1 Chapter Row"
    record1.skip = False

    records = {
        "org/repo#1": record1,
    }

    mocker.patch(
        "release_notes_generator.action_inputs.ActionInputs.get_duplicity_scope",
        return_value=DuplicityScopeEnum.SERVICE,
    )

    custom_chapters.populate(records)

    assert "org/repo#1" in custom_chapters.chapters["Chapter 1"].rows
    assert "org/repo#1" in custom_chapters.chapters["Chapter 2"].rows
    assert custom_chapters.chapters["Chapter 1"].rows["org/repo#1"] == "Record 1 Chapter Row"
    assert custom_chapters.chapters["Chapter 2"].rows["org/repo#1"] == "Record 1 Chapter Row"


def test_populate_none_duplicity_scope(custom_chapters, mocker):
    record1 = mocker.Mock(spec=Record)
    record1.labels = ["bug", "feature"]
    record1.pulls_count = 1
    record1.is_present_in_chapters = False
    record1.to_chapter_row.return_value = "Record 1 Chapter Row"
    record1.skip = False

    records = {
        "org/repo#1": record1,
    }

    mocker.patch(
        "release_notes_generator.action_inputs.ActionInputs.get_duplicity_scope", return_value=DuplicityScopeEnum.NONE
    )

    custom_chapters.populate(records)

    assert "org/repo#1" in custom_chapters.chapters["Chapter 1"].rows
    assert "org/repo#1" in custom_chapters.chapters["Chapter 2"].rows


# from_json


def test_custom_chapters_from_yaml_array():
    custom_chapters = CustomChapters()
    yaml_array_in_string = [
        {"title": "Breaking Changes 💥", "label": "breaking-change"},
        {"title": "New Features 🎉", "label": "enhancement"},
        {"title": "New Features 🎉", "label": "feature"},
        {"title": "Bugfixes 🛠", "label": "bug"}
    ]

    custom_chapters.from_yaml_array(yaml_array_in_string)

    assert "Breaking Changes 💥" in custom_chapters.titles
    assert "New Features 🎉" in custom_chapters.titles
    assert "Bugfixes 🛠" in custom_chapters.titles
    assert isinstance(custom_chapters.chapters["Breaking Changes 💥"], Chapter)
    assert isinstance(custom_chapters.chapters["New Features 🎉"], Chapter)
    assert isinstance(custom_chapters.chapters["Bugfixes 🛠"], Chapter)
    assert ["breaking-change"] == custom_chapters.chapters["Breaking Changes 💥"].labels
    assert ["enhancement", "feature"] == custom_chapters.chapters["New Features 🎉"].labels
    assert ["bug"] == custom_chapters.chapters["Bugfixes 🛠"].labels


def _build_basic_record(record_id: str, labels: list[str]):  # helper for new tests
    class R:
        def __init__(self, rid, labs):
            self.labels = labs
            self.pulls_count = 1
            self.is_present_in_chapters = False
            self.skip = False
            self._rid = rid

        def contains_change_increment(self):
            return True

        def to_chapter_row(self, _include_prs: bool):
            return f"{self._rid} row"

    return R(record_id, labels)


@pytest.mark.parametrize(
    "chapter_def, expected",
    [
        ({"title": "Multi", "labels": "bug"}, ["bug"]),  # single label string via 'labels'
        ({"title": "Multi", "labels": "bug, enhancement"}, ["bug", "enhancement"]),  # comma list
        ({"title": "Multi", "labels": "bug\nenhancement"}, ["bug", "enhancement"]),  # newline list
        ({"title": "Multi", "labels": ["bug", "enhancement"]}, ["bug", "enhancement"]),  # yaml list
    ],
)
def test_from_yaml_array_with_labels_variants(chapter_def, expected):  # T003
    cc = CustomChapters()
    cc.from_yaml_array([chapter_def])
    assert "Multi" in cc.titles
    assert cc.chapters["Multi"].labels == expected


def test_from_yaml_array_with_mixed_separators_and_duplicates():  # T004
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Mixed", "labels": " bug, enhancement,bug\nfeature , enhancement"},
        ]
    )
    # Expect trimmed, order of first occurrence preserved, duplicates removed
    assert cc.chapters["Mixed"].labels == ["bug", "enhancement", "feature"]


def test_from_yaml_array_precedence_label_vs_labels(caplog):  # T005
    cc = CustomChapters()
    caplog.set_level("WARNING")
    cc.from_yaml_array(
        [
            {"title": "Precedence", "label": "legacy", "labels": "new1, new2"},
        ]
    )
    assert cc.chapters["Precedence"].labels == ["new1", "new2"], "'labels' key should take precedence over 'label'"
    # Expect exactly one warning referencing the chapter title
    warnings = [r for r in caplog.records if "Precedence" in r.message and "precedence" in r.message.lower()]
    assert len(warnings) == 1


def test_duplicate_suppression_with_multi_label_record():  # T006
    cc = CustomChapters()
    cc.from_yaml_array([
        {"title": "Changes", "labels": "bug, enhancement"},
    ])
    record = _build_basic_record("org/repo#1", ["bug", "enhancement"])  # matches both labels
    records = {"org/repo#1": record}
    cc.populate(records)
    rows = cc.chapters["Changes"].rows
    assert list(rows.keys()) == ["org/repo#1"], "Record should appear only once in chapter despite multi-match"


def test_overlapping_chapters_record_in_both():  # T007
    cc = CustomChapters()
    cc.from_yaml_array([
        {"title": "Bugs", "labels": "bug"},
        {"title": "Features", "labels": "feature, bug"},
    ])
    record = _build_basic_record("org/repo#99", ["bug"])  # qualifies for both
    records = {"org/repo#99": record}
    cc.populate(records)
    assert "org/repo#99" in cc.chapters["Bugs"].rows
    assert "org/repo#99" in cc.chapters["Features"].rows


def test_invalid_definitions_empty_and_wrong_type(caplog):  # T008
    cc = CustomChapters()
    caplog.set_level("WARNING")
    cc.from_yaml_array([
        {"title": "Empty", "labels": "   ,  \n"},  # becomes empty after normalization
        {"title": "WrongType", "labels": 12345},  # invalid type
    ])
    assert "Empty" not in cc.titles, "Empty chapter should be skipped"
    assert "WrongType" not in cc.titles, "Invalid type chapter should be skipped"
    empty_warnings = [r for r in caplog.records if "Empty" in r.message and "empty" in r.message.lower()]
    wrong_type_warnings = [r for r in caplog.records if "WrongType" in r.message and "invalid" in r.message.lower()]
    assert empty_warnings, "Expected warning about empty labels set"
    assert wrong_type_warnings, "Expected warning about invalid labels type"

