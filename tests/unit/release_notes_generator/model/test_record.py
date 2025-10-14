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
from typing import Optional

from release_notes_generator.model.record.record import Record


class DummyRecord(Record):
    def __init__(self, skip=False, labels=None, authors=None, closed=True, record_id=1, rls_notes: Optional[str]="notes"):
        super().__init__(labels, skip)
        self._labels = labels or ["bug", "feature"]
        self._authors = authors or ["alice", "bob"]
        self._closed = closed
        self._record_id = record_id
        self._rls_notes = rls_notes

    @property
    def record_id(self):
        return self._record_id

    @property
    def is_closed(self):
        return self._closed

    @property
    def is_open(self):
        return not self._closed

    @property
    def labels(self):
        return self._labels

    @property
    def author(self):
        return self._authors[0] if self._authors else ""

    @property
    def assignees(self):
        return self._authors

    @property
    def developers(self):
        return self._authors

    def to_chapter_row(self, add_into_chapters: bool = True):
        return f"Row for {self._record_id}"

    def get_rls_notes(self, line_marks=None):
        return self._rls_notes

    def get_labels(self) -> list[str]:
        return self._labels

    def contains_change_increment(self) -> bool:
        return True

def test_is_present_in_chapters():
    rec = DummyRecord()
    assert not rec.is_present_in_chapters
    rec.added_into_chapters()
    assert rec.is_present_in_chapters

def test_skip_property():
    rec = DummyRecord(skip=True)
    assert rec.skip is True
    rec2 = DummyRecord(skip=False)
    assert rec2.skip is False

def test_present_in_chapters_count():
    rec = DummyRecord()
    assert rec.present_in_chapters() == 0
    rec.added_into_chapters()
    rec.added_into_chapters()
    assert rec.present_in_chapters() == 2

def test_contains_min_one_label():
    rec = DummyRecord(labels=["bug", "feature"])
    assert rec.contains_min_one_label(["bug"])
    assert not rec.contains_min_one_label(["enhancement"])

def test_contain_all_labels():
    rec = DummyRecord(labels=["bug", "feature"])
    assert rec.contain_all_labels(["bug", "feature"])
    assert not rec.contain_all_labels(["bug", "other"])
    assert rec.contain_all_labels(["bug"])

def test_contains_release_notes_true():
    rec = DummyRecord(rls_notes="Some notes")
    assert rec.contains_release_notes() is True
    assert rec.contains_release_notes(re_check=True) is True
    assert rec.contains_release_notes() is True

def test_contains_release_notes_false():
    rec = DummyRecord(rls_notes=None)
    assert rec.contains_release_notes() is False
    assert rec.contains_release_notes(re_check=True) is False
    assert rec.contains_release_notes() is False
