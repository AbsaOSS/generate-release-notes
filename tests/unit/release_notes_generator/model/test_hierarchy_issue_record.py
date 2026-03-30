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
Unit tests for HierarchyIssueRecord.
"""

from datetime import datetime

from github.Issue import Issue

from release_notes_generator.model.record.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.sub_issue_record import SubIssueRecord



def _make_hierarchy_issue(mocker, number: int, state: str) -> Issue:
    issue = mocker.Mock(spec=Issue)
    issue.number = number
    issue.title = f"HI{number}"
    issue.state = state
    issue.state_reason = None
    issue.body = ""
    issue.type = None
    issue.created_at = datetime.now()
    issue.closed_at = datetime.now() if state == IssueRecord.ISSUE_STATE_CLOSED else None
    issue.repository.full_name = "org/repo"
    issue.user = None
    issue.assignees = []
    issue.get_labels.return_value = []
    issue.get_sub_issues.return_value = []
    return issue


def _make_sub_issue(mocker, number: int, state: str) -> SubIssueRecord:
    issue = mocker.Mock(spec=Issue)
    issue.number = number
    issue.title = f"SI{number}"
    issue.state = state
    issue.state_reason = None
    issue.body = ""
    issue.type = None
    issue.created_at = datetime.now()
    issue.closed_at = datetime.now() if state == IssueRecord.ISSUE_STATE_CLOSED else None
    issue.repository.full_name = "org/repo"
    issue.user = None
    issue.assignees = []
    issue.get_labels.return_value = []
    issue.get_sub_issues.return_value = []
    return SubIssueRecord(issue)



def test_progress_leaf_node_returns_empty_string(mocker):
    """HierarchyIssueRecord with no direct sub-issues returns '' for progress."""
    issue = _make_hierarchy_issue(mocker, 100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    assert record.progress == ""


def test_progress_leaf_node_suppressed_in_row(mocker):
    """{progress} token in format template produces no extra whitespace when leaf."""
    mocker.patch(
        "release_notes_generator.model.record.hierarchy_issue_record.ActionInputs.get_row_format_hierarchy_issue",
        return_value="_{title}_ {number} {progress}",
    )

    issue = _make_hierarchy_issue(mocker, 100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)
    row = record.to_chapter_row(add_into_chapters=False)

    assert "progress" not in row.lower()
    assert "  " not in row  # no double spaces from suppressed token
    assert row.endswith("_HI100_ #100"), f"Unexpected row: {row!r}"


def test_progress_rendered_in_row(mocker):
    """Non-empty progress value appears correctly in the rendered row."""
    mocker.patch(
        "release_notes_generator.model.record.hierarchy_issue_record.ActionInputs.get_row_format_hierarchy_issue",
        return_value="_{title}_ {number} {progress}",
    )

    issue = _make_hierarchy_issue(mocker, 200, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)
    record._sub_issues = {
        "org/repo#401": _make_sub_issue(mocker, 401, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#402": _make_sub_issue(mocker, 402, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#403": _make_sub_issue(mocker, 403, IssueRecord.ISSUE_STATE_OPEN),
    }
    row = record.to_chapter_row(add_into_chapters=False)

    assert "2/3 done" in row, f"Expected '2/3 done' in row, got: {row!r}"


def test_progress_empty_leaves_adjacent_delimiters(mocker):
    """Empty {progress} does not strip surrounding delimiter characters."""
    mocker.patch(
        "release_notes_generator.model.record.hierarchy_issue_record.ActionInputs.get_row_format_hierarchy_issue",
        return_value="_{title}_ {number} ({progress})",
    )

    issue = _make_hierarchy_issue(mocker, 100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)  # leaf — no sub-issues
    row = record.to_chapter_row(add_into_chapters=False)

    assert "()" in row, f"Expected '()' in row when progress is empty, got: {row!r}"



def test_progress_partial_completion(mocker):
    """3 direct sub-issues (2 closed, 1 open) → '2/3 done'."""
    issue = _make_hierarchy_issue(mocker, 200, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record._sub_issues = {
        "org/repo#401": _make_sub_issue(mocker, 401, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#402": _make_sub_issue(mocker, 402, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#403": _make_sub_issue(mocker, 403, IssueRecord.ISSUE_STATE_OPEN),
    }

    assert record.progress == "2/3 done"


def test_progress_all_closed(mocker):
    """All direct sub-issues closed → 'Y/Y done'."""
    issue = _make_hierarchy_issue(mocker, 201, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record._sub_issues = {
        "org/repo#501": _make_sub_issue(mocker, 501, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#502": _make_sub_issue(mocker, 502, IssueRecord.ISSUE_STATE_CLOSED),
    }

    assert record.progress == "2/2 done"


def test_progress_all_open(mocker):
    """All direct sub-issues open → '0/N done'."""
    issue = _make_hierarchy_issue(mocker, 202, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record._sub_issues = {
        "org/repo#601": _make_sub_issue(mocker, 601, IssueRecord.ISSUE_STATE_OPEN),
        "org/repo#602": _make_sub_issue(mocker, 602, IssueRecord.ISSUE_STATE_OPEN),
    }

    assert record.progress == "0/2 done"


def test_progress_mixed_sub_issues_and_sub_hierarchy_issues(mocker):
    """Direct children include both SubIssueRecord and sub HierarchyIssueRecord."""
    parent_issue = _make_hierarchy_issue(mocker, 300, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(parent_issue)

    # 1 closed sub-issue
    record._sub_issues = {
        "org/repo#701": _make_sub_issue(mocker, 701, IssueRecord.ISSUE_STATE_CLOSED),
    }

    # 1 open sub-hierarchy-issue, 1 closed sub-hierarchy-issue
    child_open_issue = _make_hierarchy_issue(mocker, 801, IssueRecord.ISSUE_STATE_OPEN)
    child_closed_issue = _make_hierarchy_issue(mocker, 802, IssueRecord.ISSUE_STATE_CLOSED)
    record._sub_hierarchy_issues = {
        "org/repo#801": HierarchyIssueRecord(child_open_issue),
        "org/repo#802": HierarchyIssueRecord(child_closed_issue),
    }

    # total=3 (1 sub_issue + 2 sub_hierarchy_issues), closed=2 (sub_issue + child_closed)
    assert record.progress == "2/3 done"



def test_progress_per_level_independence(mocker):
    """
    In a 3-layer tree each node counts its own direct children only.

    Tree:
      root (open)
        child_a (closed)  → has 1 closed grandchild
        child_b (closed)  → has 3 grandchildren (2 closed)
        child_c (open)    → has 0 grandchildren

    root.progress   → 2/3 done  (child_a closed, child_b closed, child_c open)
    child_a.progress → 1/1 done (its own grandchild)
    child_b.progress → 2/3 done (its own grandchildren)
    child_c.progress → ""       (leaf)
    """
    root_issue = _make_hierarchy_issue(mocker, 900, IssueRecord.ISSUE_STATE_OPEN)
    root = HierarchyIssueRecord(root_issue)

    child_a_issue = _make_hierarchy_issue(mocker, 901, IssueRecord.ISSUE_STATE_CLOSED)
    child_a = HierarchyIssueRecord(child_a_issue)
    child_a._sub_issues = {
        "org/repo#911": _make_sub_issue(mocker, 911, IssueRecord.ISSUE_STATE_CLOSED),
    }

    child_b_issue = _make_hierarchy_issue(mocker, 902, IssueRecord.ISSUE_STATE_CLOSED)
    child_b = HierarchyIssueRecord(child_b_issue)
    child_b._sub_issues = {
        "org/repo#921": _make_sub_issue(mocker, 921, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#922": _make_sub_issue(mocker, 922, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#923": _make_sub_issue(mocker, 923, IssueRecord.ISSUE_STATE_OPEN),
    }

    child_c_issue = _make_hierarchy_issue(mocker, 903, IssueRecord.ISSUE_STATE_OPEN)
    child_c = HierarchyIssueRecord(child_c_issue)

    root._sub_hierarchy_issues = {
        "org/repo#901": child_a,
        "org/repo#902": child_b,
        "org/repo#903": child_c,
    }

    assert root.progress == "2/3 done", f"root: {root.progress!r}"
    assert child_a.progress == "1/1 done", f"child_a: {child_a.progress!r}"
    assert child_b.progress == "2/3 done", f"child_b: {child_b.progress!r}"
    assert child_c.progress == "", f"child_c: {child_c.progress!r}"
