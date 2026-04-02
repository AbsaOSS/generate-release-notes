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
from release_notes_generator.model.record.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.record.commit_record import CommitRecord
from release_notes_generator.model.record.record import Record
from release_notes_generator.utils.enums import DuplicityScopeEnum
from release_notes_generator.action_inputs import ActionInputs
from tests.unit.conftest import make_super_chapters_cc


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
        pytest.param(
            {"title": "Multi", "labels": "bug, enhancement"}, ["bug", "enhancement"], None, id="comma-separated"
        ),
        pytest.param(
            {"title": "Multi", "labels": "bug\nenhancement"}, ["bug", "enhancement"], None, id="newline-separated"
        ),
        pytest.param(
            {"title": "Multi", "labels": ["bug", "enhancement"]}, ["bug", "enhancement"], None, id="yaml-list"
        ),
        pytest.param(
            {"title": "Mixed", "labels": " bug, enhancement,bug\nfeature , enhancement"},
            ["bug", "enhancement", "feature"],
            None,
            id="mixed-separators-dedup-trim",
        ),
        pytest.param(
            {"title": "Precedence", "label": "legacy", "labels": "new1, new2"},
            ["new1", "new2"],
            "precedence",
            id="labels-key-precedence",
        ),
        pytest.param(
            {"title": "UnicodeSpace", "labels": "\u2003bug\u00a0,\u2009enhancement"},
            ["bug", "enhancement"],
            None,
            id="unicode-whitespace-trim",
        ),
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
    cc.from_yaml_array(
        [
            {"title": "Bugs", "labels": "bug"},
            {"title": "Features", "labels": "feature, bug"},
        ]
    )
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


# Tests for hidden flag functionality


def test_from_yaml_array_hidden_true():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Hidden Chapter", "labels": "bug", "hidden": True}])
    # Assert
    assert "Hidden Chapter" in cc.chapters
    assert cc.chapters["Hidden Chapter"].hidden is True


def test_from_yaml_array_hidden_false():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Visible Chapter", "labels": "bug", "hidden": False}])
    # Assert
    assert "Visible Chapter" in cc.chapters
    assert cc.chapters["Visible Chapter"].hidden is False


def test_from_yaml_array_hidden_omitted():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Default Chapter", "labels": "bug"}])
    # Assert
    assert "Default Chapter" in cc.chapters
    assert cc.chapters["Default Chapter"].hidden is False


@pytest.mark.parametrize(
    "hidden_value, expected_hidden, should_warn",
    [
        pytest.param("true", True, False, id="string-true-lowercase"),
        pytest.param("True", True, False, id="string-true-capitalized"),
        pytest.param("false", False, False, id="string-false-lowercase"),
        pytest.param("False", False, False, id="string-false-capitalized"),
        pytest.param("invalid", False, True, id="invalid-string"),
        pytest.param(123, False, True, id="integer-type"),
        pytest.param([], False, True, id="list-type"),
    ],
)
def test_from_yaml_array_hidden_validation(hidden_value, expected_hidden, should_warn, caplog, record_stub):
    # Arrange
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    record = record_stub("org/repo#1", ["bug"])
    records: dict[str, Record] = {"org/repo#1": record}
    # Act
    cc.from_yaml_array([{"title": "Test Chapter", "labels": "bug", "hidden": hidden_value}])
    cc.populate(records)
    # Assert
    assert "Test Chapter" in cc.chapters
    assert cc.chapters["Test Chapter"].hidden is expected_hidden
    assert "org/repo#1" in cc.chapters["Test Chapter"].rows
    if should_warn:
        assert any("invalid 'hidden' value" in r.message.lower() for r in caplog.records)
    else:
        assert not any("invalid 'hidden' value" in r.message.lower() for r in caplog.records)


def test_from_yaml_array_multi_label_with_hidden():
    # Arrange - Test that multi-label format works with hidden flag
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Multi", "labels": ["bug", "enhancement"], "hidden": True}])
    # Assert
    assert "Multi" in cc.chapters
    assert cc.chapters["Multi"].labels == ["bug", "enhancement"]
    assert cc.chapters["Multi"].hidden is True


def test_populate_hidden_chapter_assigns_records(record_stub):
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Hidden Bugs", "labels": "bug", "hidden": True}])
    record = record_stub("org/repo#1", ["bug"])
    records = {"org/repo#1": record}
    # Act
    cc.populate(records)
    # Assert - record is assigned to hidden chapter
    assert "org/repo#1" in cc.chapters["Hidden Bugs"].rows


def test_populate_hidden_chapter_no_duplicity_count(record_stub, mocker):
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Hidden", "labels": "bug", "hidden": True}])
    record = record_stub("org/repo#1", ["bug"])
    records = {"org/repo#1": record}
    # Mock to_chapter_row to track calls
    original_to_chapter_row = record.to_chapter_row
    mock_to_chapter_row = mocker.Mock(side_effect=original_to_chapter_row)
    record.to_chapter_row = mock_to_chapter_row
    # Act
    cc.populate(records)
    # Assert - to_chapter_row called with add_into_chapters=False for hidden chapter
    mock_to_chapter_row.assert_called_once_with(False)


def test_populate_visible_chapter_duplicity_count(record_stub, mocker):
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Visible", "labels": "bug", "hidden": False}])
    record = record_stub("org/repo#1", ["bug"])
    records = {"org/repo#1": record}
    # Mock to_chapter_row to track calls
    original_to_chapter_row = record.to_chapter_row
    mock_to_chapter_row = mocker.Mock(side_effect=original_to_chapter_row)
    record.to_chapter_row = mock_to_chapter_row
    # Act
    cc.populate(records)
    # Assert - to_chapter_row called with add_into_chapters=True for visible chapter
    mock_to_chapter_row.assert_called_once_with(True)


def test_populate_mixed_visible_hidden_duplicity(record_stub):
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Visible1", "labels": "bug", "hidden": False},
            {"title": "Hidden1", "labels": "bug", "hidden": True},
            {"title": "Visible2", "labels": "bug", "hidden": False},
        ]
    )
    record = record_stub("org/repo#1", ["bug"])
    records = {"org/repo#1": record}
    # Act
    cc.populate(records)
    # Assert - record appears in all chapters but only counted in visible ones
    assert "org/repo#1" in cc.chapters["Visible1"].rows
    assert "org/repo#1" in cc.chapters["Hidden1"].rows
    assert "org/repo#1" in cc.chapters["Visible2"].rows
    # Record should be marked as present in 2 chapters (only visible ones)
    assert record.chapter_presence_count() == 2


def test_to_string_hidden_chapter_excluded():
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Visible", "labels": "bug"},
            {"title": "Hidden", "labels": "feature", "hidden": True},
        ]
    )
    cc.chapters["Visible"].add_row(1, "Bug fix")
    cc.chapters["Hidden"].add_row(2, "Hidden feature")
    # Act
    result = cc.to_string()
    # Assert
    assert "Visible" in result
    assert "Bug fix" in result
    assert "Hidden" not in result
    assert "Hidden feature" not in result


def test_to_string_all_hidden_returns_empty():
    # Arrange
    cc = CustomChapters()
    cc.print_empty_chapters = True  # Verify hidden chapters ignored even with this True
    cc.from_yaml_array(
        [
            {"title": "Hidden1", "labels": "bug", "hidden": True},
            {"title": "Hidden2", "labels": "feature", "hidden": True},
        ]
    )
    cc.chapters["Hidden1"].add_row(1, "Bug fix")
    cc.chapters["Hidden2"].add_row(2, "Feature")
    # Act
    result = cc.to_string()
    # Assert
    assert result == ""


def test_to_string_debug_logging_for_hidden(caplog, monkeypatch):
    # Arrange
    caplog.set_level("DEBUG")
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Hidden", "labels": "bug", "hidden": True}])
    cc.chapters["Hidden"].add_row(1, "Bug fix")
    # Mock verbose mode
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: True))
    # Act
    cc.to_string()
    # Assert
    assert any("Skipping hidden chapter" in r.message for r in caplog.records)
    assert any("Hidden" in r.message and "1 records tracked" in r.message for r in caplog.records)


def test_populate_debug_logging_for_hidden_assignment(record_stub, caplog, monkeypatch):
    # Arrange
    caplog.set_level("DEBUG")
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Hidden", "labels": "bug", "hidden": True}])
    record = record_stub("org/repo#1", ["bug"])
    records = {"org/repo#1": record}
    # Mock verbose mode
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: True))
    # Act
    cc.populate(records)
    # Assert
    assert any("assigned to hidden chapter" in r.message.lower() for r in caplog.records)
    assert any("not counted for duplicity" in r.message.lower() for r in caplog.records)


def test_hidden_chapter_info_logging(caplog):
    # Arrange
    caplog.set_level("INFO")
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Hidden", "labels": "bug", "hidden": True}])
    # Assert
    assert any(
        "marked as hidden" in r.message.lower() and "will not appear in output" in r.message.lower()
        for r in caplog.records
    )


def test_backward_compatibility_no_hidden_field():
    # Arrange - test that chapters without hidden field work as before
    cc = CustomChapters()
    # Act
    cc.from_yaml_array(
        [
            {"title": "Breaking Changes 💥", "label": "breaking-change"},
            {"title": "New Features 🎉", "labels": ["enhancement", "feature"]},
        ]
    )
    # Assert
    assert "Breaking Changes 💥" in cc.chapters
    assert "New Features 🎉" in cc.chapters
    assert cc.chapters["Breaking Changes 💥"].hidden is False
    assert cc.chapters["New Features 🎉"].hidden is False


def test_from_yaml_array_order_parsed():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array(
        [
            {"title": "Bugfixes 🛠", "labels": "bug", "order": 20},
            {"title": "Breaking Changes 💥", "label": "breaking-change", "order": 10},
            {"title": "Features 🎉", "labels": "feature"},
        ]
    )
    # Assert
    assert cc.chapters["Bugfixes 🛠"].order == 20
    assert cc.chapters["Breaking Changes 💥"].order == 10
    assert cc.chapters["Features 🎉"].order is None


def test_from_yaml_array_order_string_integer():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Ch", "labels": "bug", "order": "5"}])
    # Assert
    assert cc.chapters["Ch"].order == 5


@pytest.mark.parametrize(
    "order_value, expected_order, should_warn",
    [
        pytest.param(10, 10, False, id="valid-int"),
        pytest.param(0, 0, False, id="zero"),
        pytest.param(-5, -5, False, id="negative-int"),
        pytest.param("42", 42, False, id="string-int"),
        pytest.param("abc", None, True, id="invalid-string"),
        pytest.param(True, None, True, id="bool-true"),
        pytest.param(False, None, True, id="bool-false"),
        pytest.param([], None, True, id="list-type"),
        pytest.param(3.14, None, True, id="float-type"),
    ],
)
def test_from_yaml_array_order_validation(order_value, expected_order, should_warn, caplog):
    # Arrange
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "Test", "labels": "bug", "order": order_value}])
    # Assert
    assert cc.chapters["Test"].order == expected_order
    if should_warn:
        assert any("order" in r.message.lower() for r in caplog.records)
    else:
        assert not any("order" in r.message.lower() for r in caplog.records)


def test_from_yaml_array_order_omitted():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array([{"title": "NoOrder", "labels": "bug"}])
    # Assert
    assert cc.chapters["NoOrder"].order is None


def test_from_yaml_array_repeated_title_same_order():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array(
        [
            {"title": "Bugfixes 🛠", "label": "bug", "order": 20},
            {"title": "Bugfixes 🛠", "label": "error", "order": 20},
        ]
    )
    # Assert
    assert cc.chapters["Bugfixes 🛠"].labels == ["bug", "error"]
    assert cc.chapters["Bugfixes 🛠"].order == 20


def test_from_yaml_array_repeated_title_conflicting_order(caplog):
    # Arrange
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    # Act
    cc.from_yaml_array(
        [
            {"title": "Bugfixes 🛠", "label": "bug", "order": 20},
            {"title": "Bugfixes 🛠", "label": "error", "order": 10},
        ]
    )
    # Assert - keeps first explicit value
    assert cc.chapters["Bugfixes 🛠"].order == 20
    assert cc.chapters["Bugfixes 🛠"].labels == ["bug", "error"]
    assert any("conflicting order" in r.message.lower() for r in caplog.records)


def test_from_yaml_array_repeated_title_order_then_no_order():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array(
        [
            {"title": "Ch", "label": "bug", "order": 10},
            {"title": "Ch", "label": "error"},
        ]
    )
    # Assert - first explicit order kept
    assert cc.chapters["Ch"].order == 10


def test_from_yaml_array_repeated_title_no_order_then_order():
    # Arrange
    cc = CustomChapters()
    # Act
    cc.from_yaml_array(
        [
            {"title": "Ch", "label": "bug"},
            {"title": "Ch", "label": "error", "order": 15},
        ]
    )
    # Assert - second provides order, adopted
    assert cc.chapters["Ch"].order == 15


def test_to_string_order_sorting():
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Bugfixes 🛠", "labels": "bug", "order": 20},
            {"title": "Breaking Changes 💥", "label": "breaking-change", "order": 10},
            {"title": "Features 🎉", "labels": "feature"},
        ]
    )
    cc.chapters["Bugfixes 🛠"].add_row(1, "Fix 1")
    cc.chapters["Breaking Changes 💥"].add_row(2, "Break 1")
    cc.chapters["Features 🎉"].add_row(3, "Feat 1")
    # Act
    result = cc.to_string()
    # Assert - ordered chapters first ascending, then non-ordered
    breaking_pos = result.index("Breaking Changes 💥")
    bugfix_pos = result.index("Bugfixes 🛠")
    features_pos = result.index("Features 🎉")
    assert breaking_pos < bugfix_pos < features_pos


def test_to_string_order_tie_preserves_first_seen():
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Alpha", "labels": "a", "order": 10},
            {"title": "Beta", "labels": "b", "order": 10},
            {"title": "Gamma", "labels": "c", "order": 10},
        ]
    )
    cc.chapters["Alpha"].add_row(1, "A row")
    cc.chapters["Beta"].add_row(2, "B row")
    cc.chapters["Gamma"].add_row(3, "C row")
    # Act
    result = cc.to_string()
    # Assert - same order → first-seen order preserved
    alpha_pos = result.index("Alpha")
    beta_pos = result.index("Beta")
    gamma_pos = result.index("Gamma")
    assert alpha_pos < beta_pos < gamma_pos


def test_to_string_no_order_preserves_first_seen():
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Bugfixes 🛠", "labels": "bug"},
            {"title": "Features 🎉", "labels": "feature"},
            {"title": "Breaking Changes 💥", "label": "breaking-change"},
        ]
    )
    cc.chapters["Bugfixes 🛠"].add_row(1, "Fix 1")
    cc.chapters["Features 🎉"].add_row(2, "Feat 1")
    cc.chapters["Breaking Changes 💥"].add_row(3, "Break 1")
    # Act
    result = cc.to_string()
    # Assert - without order, first-seen order preserved (backward compat)
    bugfix_pos = result.index("Bugfixes 🛠")
    features_pos = result.index("Features 🎉")
    breaking_pos = result.index("Breaking Changes 💥")
    assert bugfix_pos < features_pos < breaking_pos


def test_to_string_mixed_ordered_and_unordered():
    # Arrange
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Unordered1", "labels": "a"},
            {"title": "Ordered30", "labels": "b", "order": 30},
            {"title": "Unordered2", "labels": "c"},
            {"title": "Ordered10", "labels": "d", "order": 10},
        ]
    )
    for title in cc.chapters:
        cc.chapters[title].add_row(1, "row")
    # Act
    result = cc.to_string()
    # Assert - ordered first (10, 30), then unordered (Unordered1, Unordered2)
    pos = {title: result.index(title) for title in cc.chapters}
    assert pos["Ordered10"] < pos["Ordered30"] < pos["Unordered1"] < pos["Unordered2"]


def test_sorted_chapters_hidden_with_order():
    # Arrange - hidden chapters with order are still sorted (but filtered in to_string)
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Visible", "labels": "a", "order": 20},
            {"title": "Hidden", "labels": "b", "order": 10, "hidden": True},
            {"title": "Visible2", "labels": "c"},
        ]
    )
    # Act
    sorted_chs = cc._sorted_chapters()
    # Assert
    assert sorted_chs[0].title == "Hidden"
    assert sorted_chs[1].title == "Visible"
    assert sorted_chs[2].title == "Visible2"


# ------- Tests for catch-open-hierarchy (Feature 1) -------


@pytest.fixture
def hierarchy_record_stub():
    """Create a minimal HierarchyIssueRecord-like stub for catch-open-hierarchy tests."""

    class HierarchyRecordStub(HierarchyIssueRecord):
        """Stub that avoids calling real GitHub Issue methods."""

        # noinspection PyMissingConstructor
        def __init__(self, rid, labels, state, contains_change):
            # Bypass real __init__ to avoid GitHub API objects
            Record.__init__(self, labels=labels, skip=False)
            self._rid = rid
            self._state = state
            self._contains = contains_change
            self._level = 0
            self._sub_issues = {}
            self._sub_hierarchy_issues = {}
            self._issue = None
            self._pull_requests = {}
            self._commits = {}
            self._issue_type = None

        @property
        def record_id(self):
            return self._rid

        @property
        def is_closed(self):
            return self._state == "closed"

        @property
        def is_open(self):
            return self._state == "open"

        @property
        def author(self):
            return "author"

        @property
        def assignees(self):
            return []

        @property
        def developers(self):
            return []

        def to_chapter_row(self, add_into_chapters=True):
            return f"{self._rid} row"

        def contains_change_increment(self):
            return self._contains

        def get_labels(self):
            return self.labels

        def get_rls_notes(self, _line_marks=None):
            return ""

    def _make(rid="org/repo#H1", labels=None, state="open", contains_change=True):
        return HierarchyRecordStub(rid, labels or [], state, contains_change)

    return _make


def test_catch_open_hierarchy_no_label_filter(hierarchy_record_stub, monkeypatch):
    """AC-1: Open hierarchy parent without label filter → routed to conditional chapter only."""
    # Arrange
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},
        ]
    )
    record = hierarchy_record_stub("org/repo#H1", ["feature"], state="open")
    records = {"org/repo#H1": record}
    # Act
    cc.populate(records)
    # Assert
    assert "org/repo#H1" in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#H1" not in cc.chapters["New Features 🎉"].rows


def test_catch_open_hierarchy_with_label_filter_match(hierarchy_record_stub, monkeypatch):
    """AC-2: Open hierarchy parent with matching label filter → intercepted."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True, "labels": "feature"},
        ]
    )
    record = hierarchy_record_stub("org/repo#H2", ["feature"], state="open")
    records = {"org/repo#H2": record}
    cc.populate(records)
    assert "org/repo#H2" in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#H2" not in cc.chapters["New Features 🎉"].rows


def test_catch_open_hierarchy_with_label_filter_no_match(hierarchy_record_stub, monkeypatch):
    """AC-3: Open hierarchy parent with non-matching label filter → normal routing."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True, "labels": "epic"},
        ]
    )
    record = hierarchy_record_stub("org/repo#H3", ["feature"], state="open")
    records = {"org/repo#H3": record}
    cc.populate(records)
    assert "org/repo#H3" not in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#H3" in cc.chapters["New Features 🎉"].rows


def test_catch_open_hierarchy_closed_parent_not_intercepted(hierarchy_record_stub, monkeypatch):
    """AC-4: Closed hierarchy parent → not intercepted; uses normal label routing."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},
        ]
    )
    record = hierarchy_record_stub("org/repo#H4", ["feature"], state="closed")
    records = {"org/repo#H4": record}
    cc.populate(records)
    assert "org/repo#H4" not in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#H4" in cc.chapters["New Features 🎉"].rows


def test_catch_open_hierarchy_disabled_hierarchy_noop(hierarchy_record_stub, monkeypatch, caplog):
    """AC-5: hierarchy=false → gate skipped, warning logged."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: False))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    caplog.set_level("WARNING")
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},
        ]
    )
    record = hierarchy_record_stub("org/repo#H5", ["feature"], state="open")
    records = {"org/repo#H5": record}
    cc.populate(records)
    # Record falls through to normal label routing since hierarchy is disabled
    assert "org/repo#H5" not in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#H5" in cc.chapters["New Features 🎉"].rows
    assert any("catch-open-hierarchy has no effect" in r.message for r in caplog.records)


def test_catch_open_hierarchy_duplicate_warning(caplog):
    """AC-6: Two catch-open-hierarchy chapters → only first used, warning logged."""
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},
            {"title": "Also Silent 🤫", "catch-open-hierarchy": True, "labels": "bug"},
        ]
    )
    # First chapter has it
    assert cc.chapters["Silent Live 🤫"].catch_open_hierarchy is True
    # Second chapter has it disabled due to duplicate
    assert cc.chapters["Also Silent 🤫"].catch_open_hierarchy is False
    assert any("ignoring duplicate" in r.message.lower() for r in caplog.records)


def test_catch_open_hierarchy_no_labels_chapter_created():
    """catch-open-hierarchy chapter without labels is created with empty label list."""
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},
        ]
    )
    assert "Silent Live 🤫" in cc.chapters
    assert cc.chapters["Silent Live 🤫"].labels == []
    assert cc.chapters["Silent Live 🤫"].catch_open_hierarchy is True


def test_catch_open_hierarchy_with_hidden(hierarchy_record_stub, monkeypatch):
    """catch-open-hierarchy combined with hidden: records tracked but not visible."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True, "hidden": True},
        ]
    )
    record = hierarchy_record_stub("org/repo#H6", ["feature"], state="open")
    records = {"org/repo#H6": record}
    cc.populate(records)
    # Record intercepted by hidden conditional chapter
    assert "org/repo#H6" in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#H6" not in cc.chapters["New Features 🎉"].rows
    # Hidden chapter should not appear in output
    result = cc.to_string()
    assert "Silent Live" not in result


def test_catch_open_hierarchy_non_hierarchy_record_not_intercepted(record_stub, monkeypatch):
    """Non-hierarchy records are never intercepted by catch-open-hierarchy."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},
        ]
    )
    record = record_stub("org/repo#R1", ["feature"])
    records = {"org/repo#R1": record}
    cc.populate(records)
    assert "org/repo#R1" not in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#R1" in cc.chapters["New Features 🎉"].rows


def test_from_yaml_array_catch_open_hierarchy_default_false():
    """catch-open-hierarchy defaults to False when omitted."""
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Features", "labels": "feature"}])
    assert cc.chapters["Features"].catch_open_hierarchy is False


@pytest.mark.parametrize(
    "coh_value, expected, should_warn",
    [
        pytest.param(True, True, False, id="bool-true"),
        pytest.param(False, False, False, id="bool-false"),
        pytest.param("true", True, False, id="string-true"),
        pytest.param("false", False, False, id="string-false"),
        pytest.param("invalid", False, True, id="invalid-string"),
        pytest.param(123, False, True, id="integer-type"),
    ],
)
def test_from_yaml_array_catch_open_hierarchy_validation(coh_value, expected, should_warn, caplog):
    """Validation of catch-open-hierarchy values."""
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Test", "labels": "bug", "catch-open-hierarchy": coh_value}])
    assert cc.chapters["Test"].catch_open_hierarchy is expected
    if should_warn:
        assert any("catch-open-hierarchy" in r.message for r in caplog.records)
    else:
        assert not any(
            "catch-open-hierarchy" in r.message.lower() and "invalid" in r.message.lower() for r in caplog.records
        )


def test_catch_open_hierarchy_merge_path_adopts_flag(hierarchy_record_stub, monkeypatch):
    """If a title is defined twice and the second entry adds catch-open-hierarchy,
    the flag must be set on the merged chapter (merge-path update)."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Silent Live 🤫", "labels": "bug"},  # first: no COH
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},  # second: adds COH
        ]
    )
    assert cc.chapters["Silent Live 🤫"].catch_open_hierarchy is True

    record = hierarchy_record_stub("org/repo#M1", ["bug"], state="open")
    cc.populate({"org/repo#M1": record})
    assert "org/repo#M1" in cc.chapters["Silent Live 🤫"].rows


def test_catch_open_hierarchy_no_labels_record_captured(hierarchy_record_stub, monkeypatch):
    """An open HierarchyIssueRecord with no labels must still be routed to a
    no-filter COH chapter (COH gate precedes the empty-labels early-exit)."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "New Features 🎉", "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},  # no label filter
        ]
    )
    record = hierarchy_record_stub("org/repo#N1", [], state="open")  # deliberately no labels
    cc.populate({"org/repo#N1": record})
    assert "org/repo#N1" in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#N1" not in cc.chapters["New Features 🎉"].rows


def test_catch_open_hierarchy_visible_increments_chapter_presence(hierarchy_record_stub, monkeypatch):
    """A visible COH chapter must increment chapter_presence_count, just like normal visible chapters."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True},
        ]
    )
    record = hierarchy_record_stub("org/repo#P1", ["feature"], state="open")
    cc.populate({"org/repo#P1": record})
    assert record.chapter_presence_count() == 1


def test_catch_open_hierarchy_hidden_does_not_increment_chapter_presence(hierarchy_record_stub, monkeypatch):
    """A hidden COH chapter must NOT increment chapter_presence_count (same rule as normal hidden chapters)."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True, "hidden": True},
        ]
    )
    record = hierarchy_record_stub("org/repo#P2", ["feature"], state="open")
    cc.populate({"org/repo#P2": record})
    assert "org/repo#P2" in cc.chapters["Silent Live 🤫"].rows
    assert record.chapter_presence_count() == 0


def test_catch_open_hierarchy_skipped_chapter_does_not_consume_coh_slot(caplog, hierarchy_record_stub, monkeypatch):
    """A COH chapter that is skipped (empty labels after normalization) must not consume the
    single-COH slot, so a subsequent valid COH chapter is still accepted."""
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Broken COH", "catch-open-hierarchy": True, "labels": "   "},  # empty → skipped
            {"title": "Real Silent Live", "catch-open-hierarchy": True},  # should succeed
        ]
    )
    # Skipped chapter not created
    assert "Broken COH" not in cc.chapters
    # Valid second COH chapter created normally
    assert "Real Silent Live" in cc.chapters
    assert cc.chapters["Real Silent Live"].catch_open_hierarchy is True
    # No false duplicate warning should be present
    assert not any("ignoring duplicate" in r.message.lower() for r in caplog.records)
    # Skipped-labels warning should be present
    assert any("empty after normalization" in r.message for r in caplog.records)


def test_catch_open_hierarchy_same_title_repeat_no_warning(caplog):
    """Repeating catch-open-hierarchy: true on the same title must not warn and
    must produce one chapter with the flag set and all labels merged."""
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True, "labels": "feature"},
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True, "labels": "epic"},
        ]
    )
    assert "Silent Live 🤫" in cc.chapters
    assert cc.chapters["Silent Live 🤫"].catch_open_hierarchy is True
    assert cc.chapters["Silent Live 🤫"].labels == ["feature", "epic"]
    assert not any("ignoring duplicate" in r.message.lower() for r in caplog.records)


def test_labels_null_non_coh_chapter_warns_and_skips(caplog):
    """labels: null on a non-COH chapter must warn and skip — not silently create an unroutable chapter."""
    caplog.set_level("WARNING", logger="release_notes_generator.chapters.custom_chapters")
    cc = CustomChapters()
    cc.from_yaml_array([{"title": "Bad Chapter", "labels": None}])
    assert "Bad Chapter" not in cc.chapters
    assert any("null labels" in r.message for r in caplog.records)


def test_coh_chapter_not_populated_via_label_routing(hierarchy_record_stub, monkeypatch):
    """A COH chapter with labels must NOT receive closed hierarchy parents or non-hierarchy records
    via normal label routing — only open hierarchy parents route through the COH gate."""
    monkeypatch.setattr(ActionInputs, "get_hierarchy", staticmethod(lambda: True))
    monkeypatch.setattr(ActionInputs, "get_verbose", staticmethod(lambda: False))
    cc = CustomChapters()
    cc.from_yaml_array(
        [
            {"title": "Silent Live 🤫", "catch-open-hierarchy": True, "labels": "feature"},
            {"title": "New Features 🎉", "labels": "feature"},
        ]
    )

    # Closed hierarchy parent with matching label → must go to normal chapter, not COH
    closed_parent = hierarchy_record_stub("org/repo#C1", ["feature"], state="closed")
    # Open hierarchy parent with matching label → must go to COH chapter
    open_parent = hierarchy_record_stub("org/repo#O1", ["feature"], state="open")

    cc.populate({"org/repo#C1": closed_parent, "org/repo#O1": open_parent})

    assert "org/repo#C1" not in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#C1" in cc.chapters["New Features 🎉"].rows
    assert "org/repo#O1" in cc.chapters["Silent Live 🤫"].rows
    assert "org/repo#O1" not in cc.chapters["New Features 🎉"].rows


def test_super_chapters_no_super_chapters_renders_flat(mocker, record_stub):
    """When no super chapters are defined, output is flat (### headings only)."""
    # Arrange
    cc = make_super_chapters_cc(mocker, [{"title": "Features", "label": "feature"}], [])
    cc.populate({"org/repo#1": record_stub("org/repo#1", ["feature"])})
    # Act
    output = cc.to_string()
    # Assert
    assert output.startswith("### Features")
    for line in output.splitlines():
        assert not line.startswith("## ")


def test_super_chapters_records_grouped_under_super_chapter(mocker, record_stub):
    """Records matching a super-chapter label appear nested under the super-chapter heading."""
    # Arrange
    cc = make_super_chapters_cc(
        mocker,
        [
            {"title": "Enhancements", "label": "enhancement"},
            {"title": "Bugfixes", "label": "bug"},
        ],
        [
            {"title": "Atum server", "label": "atum-server"},
            {"title": "Atum agent", "label": "atum-agent"},
        ],
    )
    r1 = record_stub("org/repo#1", ["enhancement", "atum-server"])
    r2 = record_stub("org/repo#2", ["enhancement", "atum-agent"])
    r3 = record_stub("org/repo#3", ["bug", "atum-agent"])
    cc.populate({"org/repo#1": r1, "org/repo#2": r2, "org/repo#3": r3})
    # Act
    output = cc.to_string()
    # Assert
    assert "## Atum server" in output
    assert "## Atum agent" in output
    server_section = output.split("## Atum agent")[0]
    assert "### Enhancements" in server_section
    assert "org/repo#1 row" in server_section
    assert "org/repo#2 row" not in server_section
    agent_section = output.split("## Atum agent")[1]
    assert "### Enhancements" in agent_section
    assert "org/repo#2 row" in agent_section
    assert "### Bugfixes" in agent_section
    assert "org/repo#3 row" in agent_section


def test_super_chapters_record_in_multiple_super_chapters(mocker, record_stub):
    """A record with labels matching multiple super chapters appears in each."""
    # Arrange
    cc = make_super_chapters_cc(
        mocker,
        [{"title": "Enhancements", "label": "enhancement"}],
        [{"title": "Module A", "label": "mod-a"}, {"title": "Module B", "label": "mod-b"}],
    )
    r1 = record_stub("org/repo#1", ["enhancement", "mod-a", "mod-b"])
    cc.populate({"org/repo#1": r1})
    # Act
    output = cc.to_string()
    # Assert
    assert output.count("org/repo#1 row") == 2


def test_super_chapters_empty_super_chapter_skipped_when_print_empty_false(mocker, record_stub):
    """Super chapter with no matching records is omitted when print_empty_chapters=False."""
    # Arrange
    cc = make_super_chapters_cc(
        mocker,
        [{"title": "Features", "label": "feature"}],
        [{"title": "Module A", "label": "mod-a"}, {"title": "Module B", "label": "mod-b"}],
        print_empty=False,
    )
    r1 = record_stub("org/repo#1", ["feature", "mod-a"])
    cc.populate({"org/repo#1": r1})
    # Act
    output = cc.to_string()
    # Assert
    assert "## Module A" in output
    assert "## Module B" not in output


def test_super_chapters_parse_logs_and_skips_invalid(mocker):
    """Invalid super-chapter entries are skipped with a warning."""
    # Arrange
    cc = make_super_chapters_cc(
        mocker,
        [{"title": "Features", "label": "feature"}],
        [
            "not-a-dict",
            {"no-title": True},
            {"title": "Missing labels"},
            {"title": "Valid", "label": "ok"},
        ],
    )
    # Act
    output = cc.to_string()
    # Assert - only the "Valid" super chapter survives
    assert "## Valid" in output
    assert sum(1 for line in output.splitlines() if line.startswith("## ") and not line.startswith("### ")) == 1


def test_super_chapters_uncategorized_fallback(mocker, record_stub):
    """Records without any super-chapter label appear under '## Uncategorized'."""
    # Arrange
    cc = make_super_chapters_cc(
        mocker,
        [
            {"title": "Enhancements", "label": "enhancement"},
            {"title": "Bugfixes", "label": "bug"},
        ],
        [{"title": "Module A", "label": "mod-a"}],
    )
    r1 = record_stub("org/repo#1", ["enhancement", "mod-a"])
    r2 = record_stub("org/repo#2", ["bug"])  # no super-chapter label
    cc.populate({"org/repo#1": r1, "org/repo#2": r2})
    # Act
    output = cc.to_string()
    # Assert
    assert "## Module A" in output
    assert "org/repo#1 row" in output
    assert "## Uncategorized" in output
    uncategorized_section = output.split("## Uncategorized")[1]
    assert "org/repo#2 row" in uncategorized_section
    assert "org/repo#1 row" not in uncategorized_section


def test_super_chapters_no_uncategorized_when_all_claimed(mocker, record_stub):
    """No '## Uncategorized' section when all records match a super chapter."""
    # Arrange
    cc = make_super_chapters_cc(
        mocker,
        [{"title": "Enhancements", "label": "enhancement"}],
        [{"title": "Module A", "label": "mod-a"}],
    )
    r1 = record_stub("org/repo#1", ["enhancement", "mod-a"])
    cc.populate({"org/repo#1": r1})
    # Act
    output = cc.to_string()
    # Assert
    assert "## Module A" in output
    assert "Uncategorized" not in output


def test_super_chapters_coh_record_visible_in_fallback(mocker, hierarchy_record_stub):
    """COH-routed label-less record appears in Uncategorized when super chapters are active."""
    # Arrange
    cc = make_super_chapters_cc(
        mocker,
        [
            {"title": "Features", "labels": "feature"},
            {"title": "Silent Live", "catch-open-hierarchy": True},
        ],
        [{"title": "Module A", "label": "mod-a"}],
        hierarchy=True,
    )
    record = hierarchy_record_stub("org/repo#H1", [], state="open")
    cc.populate({"org/repo#H1": record})
    # Act
    output = cc.to_string()
    # Assert - COH record appears in Uncategorized since it has no super-chapter label
    assert "## Uncategorized" in output
    assert "org/repo#H1 row" in output
