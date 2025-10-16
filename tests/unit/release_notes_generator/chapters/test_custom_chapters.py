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

from release_notes_generator.chapters.custom_chapters import CustomChapters, _normalize_labels
from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.commit_record import CommitRecord
from release_notes_generator.model.record.record import Record
from release_notes_generator.utils.enums import DuplicityScopeEnum
from release_notes_generator.action_inputs import ActionInputs


@pytest.fixture
def record_stub():  # concrete minimal subclass of Record to satisfy typing
    class RecordStub(Record):
        def __init__(
            self,
            rid: str,
            labels: list[str] | None,
            skip: bool,
            contains_change_increment: bool,
        ):
            super().__init__(labels=labels, skip=skip)
            self._rid = rid
            self._contains = contains_change_increment

        # Abstract implementations (return simple defaults not under test focus)
        @property
        def record_id(self) -> str:
            return self._rid

        @property
        def is_closed(self) -> bool:  # not relevant for these tests
            return False

        @property
        def is_open(self) -> bool:
            return True

        @property
        def author(self) -> str:
            return "author"

        @property
        def assignees(self) -> list[str]:
            return []

        @property
        def developers(self) -> list[str]:
            return []

        def to_chapter_row(self, add_into_chapters: bool = True) -> str:
            return f"{self._rid} row"

        def contains_change_increment(self) -> bool:
            return self._contains

        def get_labels(self) -> list[str]:
            return self.labels

        def get_rls_notes(self, _line_marks: list[str] | None = None) -> str:
            return ""

    def _make(
        rid: str = "org/repo#X",
        labels: list[str] | None = None,
        skip: bool = False,
        contains_change_increment: bool = True,
    ) -> Record:
        return RecordStub(rid, labels or [], skip, contains_change_increment)

    return _make


def test_custom_chapters_initialization(custom_chapters):
    # Arrange (fixture already provides object)
    # Act (no explicit act needed; initialization handled by fixture)
    # Assert
    assert custom_chapters.sort_ascending
    assert custom_chapters.chapters["Chapter 1"].labels == ["bug", "enhancement"]
    assert custom_chapters.chapters["Chapter 2"].labels == ["feature"]


def test_populate_adds_rows_for_matching_labels(custom_chapters, record_stub):
    # Arrange
    record1 = record_stub("org/repo#1", ["bug"])  # Chapter 1
    record2 = record_stub("org/repo#2", ["enhancement"])  # Chapter 1
    record3 = record_stub("org/repo#3", ["feature"])  # Chapter 2
    records: dict[str, Record] = {
        "org/repo#1": record1,
        "org/repo#2": record2,
        "org/repo#3": record3,
    }
    # Act
    custom_chapters.populate(records)
    # Assert
    assert custom_chapters.chapters["Chapter 1"].rows["org/repo#1"] == "org/repo#1 row"
    assert custom_chapters.chapters["Chapter 1"].rows["org/repo#2"] == "org/repo#2 row"
    assert custom_chapters.chapters["Chapter 2"].rows["org/repo#3"] == "org/repo#3 row"


@pytest.mark.parametrize(
    "scope_enum",
    [DuplicityScopeEnum.SERVICE, DuplicityScopeEnum.NONE, DuplicityScopeEnum.BOTH],
    ids=["duplicity-scope-service", "duplicity-scope-none", "duplicity-scope-both"],
)
def test_populate_duplicity_scope_rows_present(custom_chapters, record_stub, mocker, scope_enum):
    # Arrange
    record1 = record_stub("org/repo#1", ["bug", "feature"])  # matches Chapter 1 & 2
    records: dict[str, Record] = {"org/repo#1": record1}
    mocker.patch(
        "release_notes_generator.action_inputs.ActionInputs.get_duplicity_scope",
        return_value=scope_enum,
    )
    # Act
    custom_chapters.populate(records)
    # Assert (row appears in both regardless of scope; deterministic ordering of keys)
    assert list(custom_chapters.chapters["Chapter 1"].rows.keys()) == ["org/repo#1"]
    assert list(custom_chapters.chapters["Chapter 2"].rows.keys()) == ["org/repo#1"]


def test_custom_chapters_from_yaml_array():
    # Arrange
    cc = CustomChapters()
    yaml_array_in_string = [
        {"title": "Breaking Changes 💥", "label": "breaking-change"},
        {"title": "New Features 🎉", "label": "enhancement"},
        {"title": "New Features 🎉", "label": "feature"},
        {"title": "Bugfixes 🛠", "label": "bug"},
    ]
    # Act
    cc.from_yaml_array(yaml_array_in_string)
    # Assert
    assert "Breaking Changes 💥" in cc.titles
    assert "New Features 🎉" in cc.titles
    assert "Bugfixes 🛠" in cc.titles
    assert ["breaking-change"] == cc.chapters["Breaking Changes 💥"].labels
    assert ["enhancement", "feature"] == cc.chapters["New Features 🎉"].labels
    assert ["bug"] == cc.chapters["Bugfixes 🛠"].labels


# Consolidated label normalization variants (ordering + precedence + duplicates + unicode whitespace)
@pytest.mark.parametrize(
    "chapter_def, expected, warning_substring",
    [
        pytest.param({"title": "Multi", "labels": "bug"}, ["bug"], None, id="single-string-labels"),
        pytest.param({"title": "Multi", "labels": "bug, enhancement"}, ["bug", "enhancement"], None, id="comma-separated"),
        pytest.param({"title": "Multi", "labels": "bug\nenhancement"}, ["bug", "enhancement"], None, id="newline-separated"),
        pytest.param({"title": "Multi", "labels": ["bug", "enhancement"]}, ["bug", "enhancement"], None, id="yaml-list"),
        pytest.param({"title": "Mixed", "labels": " bug, enhancement,bug\nfeature , enhancement"}, ["bug", "enhancement", "feature"], None, id="mixed-separators-dedup-trim"),
        pytest.param({"title": "Precedence", "label": "legacy", "labels": "new1, new2"}, ["new1", "new2"], "precedence", id="labels-key-precedence"),
        pytest.param({"title": "UnicodeSpace", "labels": "\u2003bug\u00A0,\u2009enhancement"}, ["bug", "enhancement"], None, id="unicode-whitespace-trim"),
    ],
)
def test_from_yaml_array_normalization_variants(chapter_def, expected, warning_substring, caplog):
    # Arrange
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([chapter_def])
    title = chapter_def["title"]
    # Assert
    assert title in cc.titles
    assert cc.chapters[title].labels == expected
    if warning_substring:
        warnings = [r for r in caplog.records if title in r.message and warning_substring in r.message.lower()]
        assert len(warnings) == 1
    else:
        assert not [r for r in caplog.records if title in r.message]


def test_duplicate_suppression_with_multi_label_record(record_stub):
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Changes", "labels": "bug, enhancement"}])
    record = record_stub("org/repo#1", ["bug", "enhancement"])
    records: dict[str, Record] = {"org/repo#1": record}
    # Act
    cc.populate(records)
    # Assert
    assert list(cc.chapters["Changes"].rows.keys()) == ["org/repo#1"]


def test_overlapping_chapters_record_in_both(record_stub):
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array([
        {"title": "Bugs", "labels": "bug"},
        {"title": "Features", "labels": "feature, bug"},
    ])
    record = record_stub("org/repo#99", ["bug"])  # qualifies for both
    records: dict[str, Record] = {"org/repo#99": record}
    # Act
    cc.populate(records)
    # Assert
    assert list(cc.chapters["Bugs"].rows.keys()) == ["org/repo#99"]
    assert list(cc.chapters["Features"].rows.keys()) == ["org/repo#99"]


@pytest.mark.parametrize(
    "chapter_def, expectation, warning_fragment",
    [
        pytest.param({"title": "Empty", "labels": "   ,  \n"}, "skipped", "empty", id="empty-after-normalization"),
        pytest.param({"title": "WrongType", "labels": 12345}, "skipped", "invalid", id="invalid-type"),
        pytest.param({"label": "bug"}, "skipped", "without title", id="missing-title"),
        pytest.param({"title": "WithExtra", "label": "bug", "extra": 123}, "added", "unknown keys", id="unknown-keys"),
        pytest.param({"title": "NoLabels"}, "skipped", "no 'label' or 'labels'", id="no-label-keys"),
    ],
)
def test_invalid_and_edge_chapter_definitions(chapter_def, expectation, warning_fragment, caplog):
    # Arrange
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([chapter_def])
    title = chapter_def.get("title")
    # Assert
    if expectation == "added":
        assert title in cc.chapters
    else:
        if title:
            assert title not in cc.chapters
        else:
            assert len(cc.chapters) == 0
    assert any(warning_fragment in r.message for r in caplog.records)


def test_from_yaml_array_skips_non_dict_definitions(caplog):  # new test for non-dict entries
    # Arrange
    caplog.set_level("WARNING")
    cc = CustomChapters()
    items = [123, "chapter", ["list"], None, {"title": "Valid", "labels": "bug"}]
    # Act
    cc.from_yaml_array(items)
    # Assert
    assert "Valid" in cc.chapters
    assert len(cc.chapters) == 1
    skip_msgs = [r.message for r in caplog.records if "invalid type" in r.message]
    assert len(skip_msgs) == 4  # one per non-dict invalid entry
    expected_types = ["<class 'int'>", "<class 'str'>", "<class 'list'>", "<class 'NoneType'>"]
    for t in expected_types:
        assert any(t in m for m in skip_msgs)


def test_from_yaml_array_verbose_debug_branch(monkeypatch, caplog):
    # Arrange
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: True))
    caplog.set_level("DEBUG")
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Verbose", "labels": "bug"}])
    # Assert
    assert "Verbose" in cc.chapters
    assert any("normalized labels" in m for m in caplog.messages)
    assert not any("token" in m.lower() for m in caplog.messages)


@pytest.mark.parametrize(
    "raw, expected",
    [
        pytest.param(12345, [], id="invalid-type"),
        pytest.param(["bug", 42, "feature", None, "bug"], ["bug", "feature"], id="list-with-non-strings"),
    ],
)
def test_normalize_labels_edge_cases(raw, expected):
    # Arrange / Act
    result = _normalize_labels(raw)
    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "scenario",
    [
        "no_pulls_count",
        "no_matching_labels",
        "no_change_increment",
        "commit_record_missing_labels",
        "empty_labels",
    ],
    ids=[
        "skip-no-pulls-count",
        "skip-no-matching-labels",
        "skip-no-change-increment",
        "skip-commit-record",
        "skip-empty-labels",
    ],
)
def test_populate_skips_for_record_conditions(scenario, record_stub, mocker):
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Bugs", "labels": "bug"}])
    records: dict[str, Record] = {}
    if scenario == "no_pulls_count":
        rec = mocker.create_autospec(IssueRecord, instance=True)
        rec.contains_change_increment.return_value = False
        rec.skip = False
        rec.labels = ["bug"]
        records = {"1": rec}
    elif scenario == "no_matching_labels":
        rec = record_stub("org/repo#X", ["non-existent-label"])
        records = {"org/repo#X": rec}
    elif scenario == "no_change_increment":
        rec = record_stub("org/repo#Y", ["bug"], contains_change_increment=False)
        records = {"org/repo#Y": rec}
    elif scenario == "commit_record_missing_labels":
        commit = mocker.create_autospec(CommitRecord, instance=True)
        commit.contains_change_increment.return_value = True
        commit.skip = False
        commit.labels = []
        records = {"org/repo#C": commit}
    elif scenario == "empty_labels":
        rec = record_stub("org/repo#Z", [])
        records = {"org/repo#Z": rec}
    else:
        pytest.fail(f"Unhandled scenario: {scenario}")
    # Act
    cc.populate(records)
    # Assert
    assert not cc.chapters["Bugs"].rows
