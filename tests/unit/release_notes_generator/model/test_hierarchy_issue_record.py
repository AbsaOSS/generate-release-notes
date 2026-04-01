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

from release_notes_generator.model.record.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.record.issue_record import IssueRecord
from tests.unit.conftest import (
    make_closed_sub_hierarchy_record_no_pr,
    make_closed_sub_hierarchy_record_with_pr,
    make_closed_sub_issue_record_no_pr,
    make_closed_sub_issue_record_with_pr,
    make_minimal_issue,
    make_minimal_pr,
    make_open_sub_hierarchy_record_no_pr,
    make_open_sub_hierarchy_record_with_pr,
    make_open_sub_issue_record_no_pr,
)


def test_to_chapter_row_closed_parent_renders_closed_and_open_sub_issues(mocker, patch_hierarchy_action_inputs):
    """
    Closed parent with one closed sub-issue (has PR) and one open sub-issue (no change
    increment) → both appear in to_chapter_row() output.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_issues["450"] = make_closed_sub_issue_record_with_pr(mocker, number=450)
    record.sub_issues["400"] = make_open_sub_issue_record_no_pr(mocker, number=400)

    row = record.to_chapter_row()

    assert "#450" in row, f"Closed sub-issue #450 must appear; got:\n{row}"
    assert "#400" in row, f"Open sub-issue #400 must appear when parent is closed; got:\n{row}"


def test_to_chapter_row_closed_parent_highlights_open_sub_issue(mocker, patch_hierarchy_action_inputs):
    """Open sub-issue under a closed parent is prefixed with the open-hierarchy-sub-issue-icon."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_issues["400"] = make_open_sub_issue_record_no_pr(mocker, number=400)
    record.sub_issues["450"] = make_closed_sub_issue_record_with_pr(mocker, number=450)

    row = record.to_chapter_row()

    lines = row.splitlines()
    open_line = next((l for l in lines if "#400" in l), None)
    closed_line = next((l for l in lines if "#450" in l), None)
    assert open_line is not None, f"Open sub-issue #400 must be present; got:\n{row}"
    assert "🟡" in open_line, f"Open sub-issue line must contain icon; got: {open_line!r}"
    assert closed_line is not None, f"Closed sub-issue #450 must be present; got:\n{row}"
    assert "🟡" not in closed_line, f"Closed sub-issue line must NOT contain icon; got: {closed_line!r}"


def test_to_chapter_row_closed_parent_highlights_open_sub_hierarchy_issue(mocker, patch_hierarchy_action_inputs):
    """Open sub-hierarchy-issue under a closed parent is prefixed with the open-hierarchy-sub-issue-icon."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_hierarchy_issues["360"] = make_open_sub_hierarchy_record_with_pr(mocker, number=360)
    record.sub_hierarchy_issues["350"] = make_closed_sub_hierarchy_record_with_pr(mocker, number=350)

    row = record.to_chapter_row()

    lines = row.splitlines()
    open_line = next((l for l in lines if "#360" in l), None)
    closed_line = next((l for l in lines if "#350" in l), None)
    assert open_line is not None, f"Open sub-hierarchy #360 must be present; got:\n{row}"
    assert "🟡" in open_line, f"Open sub-hierarchy line must contain icon; got: {open_line!r}"
    assert closed_line is not None, f"Closed sub-hierarchy #350 must be present; got:\n{row}"
    assert "🟡" not in closed_line, f"Closed sub-hierarchy line must NOT contain icon; got: {closed_line!r}"


def test_to_chapter_row_open_parent_only_renders_closed_sub_issues_with_change_increment(mocker, patch_hierarchy_action_inputs):
    """
    Open parent with one closed sub-issue (has PR) and one open sub-issue (no PR) →
    only the closed sub-issue appears; open sub-issue is suppressed.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_OPEN, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_issues["450"] = make_closed_sub_issue_record_with_pr(mocker, number=450)
    record.sub_issues["400"] = make_open_sub_issue_record_no_pr(mocker, number=400)

    row = record.to_chapter_row()

    assert "#450" in row, f"Closed sub-issue #450 must appear; got:\n{row}"
    assert "#400" not in row, f"Open sub-issue #400 must NOT appear when parent is open; got:\n{row}"


def test_to_chapter_row_open_parent_suppresses_closed_sub_issue_from_previous_release(mocker, patch_hierarchy_action_inputs):
    """
    Open parent with one closed sub-issue that has no change increment (closed or delivered
    in a previous release) → the sub-issue does not appear in the current release notes.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_OPEN, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_issues["450"] = make_closed_sub_issue_record_no_pr(mocker, number=450)

    row = record.to_chapter_row()

    assert "#450" not in row, f"Sub-issue from previous release must NOT appear; got:\n{row}"


def test_to_chapter_row_open_parent_suppresses_closed_sub_hierarchy_issue_from_previous_release(mocker, patch_hierarchy_action_inputs):
    """
    Open parent with one closed sub-hierarchy issue that has no change increment (closed or
    delivered in a previous release) → the sub-hierarchy issue does not appear.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_OPEN, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_hierarchy_issues["350"] = make_closed_sub_hierarchy_record_no_pr(mocker, number=350)

    row = record.to_chapter_row()

    assert "#350" not in row, f"Sub-hierarchy issue from previous release must NOT appear; got:\n{row}"


def test_to_chapter_row_closed_parent_renders_closed_and_open_sub_hierarchy_issues(mocker, patch_hierarchy_action_inputs):
    """
    Closed parent with one closed sub-hierarchy issue (has PR) and one open sub-hierarchy
    issue (no change increment) → both appear in to_chapter_row() output.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_hierarchy_issues["350"] = make_closed_sub_hierarchy_record_with_pr(mocker, number=350)
    record.sub_hierarchy_issues["360"] = make_open_sub_hierarchy_record_no_pr(mocker, number=360)

    row = record.to_chapter_row()

    assert "#350" in row, f"Closed sub-hierarchy issue #350 must appear; got:\n{row}"
    assert "#360" in row, f"Open sub-hierarchy issue #360 must appear when parent is closed; got:\n{row}"


def test_to_chapter_row_open_parent_only_renders_sub_hierarchy_issues_with_change_increment(mocker, patch_hierarchy_action_inputs):
    """
    Open parent with one closed sub-hierarchy issue (has PR) and one open sub-hierarchy
    issue (no PR, no change increment) → only the closed sub-hierarchy issue appears.
    Unlike leaf sub-issues, sub-hierarchy issues are filtered by change increment only;
    an open sub-hierarchy issue that aggregates PRs from its own sub-issues would still appear.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_OPEN, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_hierarchy_issues["350"] = make_closed_sub_hierarchy_record_with_pr(mocker, number=350)
    record.sub_hierarchy_issues["360"] = make_open_sub_hierarchy_record_no_pr(mocker, number=360)

    row = record.to_chapter_row()

    assert "#350" in row, f"Closed sub-hierarchy issue #350 must appear; got:\n{row}"
    assert "#360" not in row, f"Sub-hierarchy issue #360 with no change increment must NOT appear; got:\n{row}"


def test_to_chapter_row_open_parent_renders_open_sub_hierarchy_issue_with_change_increment(mocker, patch_hierarchy_action_inputs):
    """
    Open parent with one open sub-hierarchy issue that has a PR (change increment present)
    → the sub-hierarchy issue appears. Sub-hierarchy children are filtered by change
    increment only; open state alone is not a reason to suppress them.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_OPEN, number=300)
    record = HierarchyIssueRecord(parent)

    record.sub_hierarchy_issues["360"] = make_open_sub_hierarchy_record_with_pr(mocker, number=360)

    row = record.to_chapter_row()

    assert "#360" in row, f"Open sub-hierarchy issue #360 with a PR must appear under open parent; got:\n{row}"



def test_progress_leaf_node_returns_empty_string(make_hierarchy_issue):
    """HierarchyIssueRecord with no direct sub-issues returns '' for progress."""
    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    assert record.progress == ""


def test_progress_leaf_node_suppressed_in_row(mocker, make_hierarchy_issue):
    """ "_{title}_ {number} {progress}" token in format template produces no extra whitespace when leaf."""
    mocker.patch(
        "release_notes_generator.model.record.hierarchy_issue_record.ActionInputs.get_row_format_hierarchy_issue",
        return_value="_{title}_ {number} {progress}",
    )

    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)
    row = record.to_chapter_row(add_into_chapters=False)

    assert "progress" not in row.lower()
    assert "  " not in row  # no double spaces from suppressed token
    assert row.endswith("_HI100_ #100"), f"Unexpected row: {row!r}"


def test_progress_rendered_in_row(mocker, make_hierarchy_issue, make_sub_issue):
    """Non-empty progress value appears correctly in the rendered row."""
    mocker.patch(
        "release_notes_generator.model.record.hierarchy_issue_record.ActionInputs.get_row_format_hierarchy_issue",
        return_value="_{title}_ {number} {progress}",
    )

    issue = make_hierarchy_issue(200, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)
    record.sub_issues.update(
        {
            "org/repo#401": make_sub_issue(401, IssueRecord.ISSUE_STATE_CLOSED),
            "org/repo#402": make_sub_issue(402, IssueRecord.ISSUE_STATE_CLOSED),
            "org/repo#403": make_sub_issue(403, IssueRecord.ISSUE_STATE_OPEN),
        }
    )
    row = record.to_chapter_row(add_into_chapters=False)

    assert "2/3 done" in row, f"Expected '2/3 done' in row, got: {row!r}"


def test_progress_empty_leaves_adjacent_delimiters(mocker, make_hierarchy_issue):
    """Empty {progress} does not strip surrounding delimiter characters."""
    mocker.patch(
        "release_notes_generator.model.record.hierarchy_issue_record.ActionInputs.get_row_format_hierarchy_issue",
        return_value="_{title}_ {number} ({progress})",
    )

    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)  # leaf — no sub-issues
    row = record.to_chapter_row(add_into_chapters=False)

    assert "()" in row, f"Expected '()' in row when progress is empty, got: {row!r}"


def test_progress_partial_completion(make_hierarchy_issue, make_sub_issue):
    """3 direct sub-issues (2 closed, 1 open) → '2/3 done'."""
    issue = make_hierarchy_issue(200, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record.sub_issues.update(
        {
            "org/repo#401": make_sub_issue(401, IssueRecord.ISSUE_STATE_CLOSED),
            "org/repo#402": make_sub_issue(402, IssueRecord.ISSUE_STATE_CLOSED),
            "org/repo#403": make_sub_issue(403, IssueRecord.ISSUE_STATE_OPEN),
        }
    )

    assert record.progress == "2/3 done"


def test_progress_all_closed(make_hierarchy_issue, make_sub_issue):
    """All direct sub-issues closed → 'Y/Y done'."""
    issue = make_hierarchy_issue(201, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record.sub_issues.update(
        {
            "org/repo#501": make_sub_issue(501, IssueRecord.ISSUE_STATE_CLOSED),
            "org/repo#502": make_sub_issue(502, IssueRecord.ISSUE_STATE_CLOSED),
        }
    )

    assert record.progress == "2/2 done"


def test_progress_all_open(make_hierarchy_issue, make_sub_issue):
    """All direct sub-issues open → '0/N done'."""
    issue = make_hierarchy_issue(202, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record.sub_issues.update(
        {
            "org/repo#601": make_sub_issue(601, IssueRecord.ISSUE_STATE_OPEN),
            "org/repo#602": make_sub_issue(602, IssueRecord.ISSUE_STATE_OPEN),
        }
    )

    assert record.progress == "0/2 done"


def test_progress_mixed_sub_issues_and_sub_hierarchy_issues(make_hierarchy_issue, make_sub_issue):
    """Direct children include both SubIssueRecord and sub HierarchyIssueRecord."""
    parent_issue = make_hierarchy_issue(300, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(parent_issue)

    # 1 closed sub-issue
    record.sub_issues.update(
        {
            "org/repo#701": make_sub_issue(701, IssueRecord.ISSUE_STATE_CLOSED),
        }
    )

    # 1 open sub-hierarchy-issue, 1 closed sub-hierarchy-issue
    child_open_issue = make_hierarchy_issue(801, IssueRecord.ISSUE_STATE_OPEN)
    child_closed_issue = make_hierarchy_issue(802, IssueRecord.ISSUE_STATE_CLOSED)
    record.sub_hierarchy_issues.update(
        {
            "org/repo#801": HierarchyIssueRecord(child_open_issue),
            "org/repo#802": HierarchyIssueRecord(child_closed_issue),
        }
    )

    # total=3 (1 sub_issue + 2 sub_hierarchy_issues), closed=2 (sub_issue + child_closed)
    assert record.progress == "2/3 done"


def test_progress_per_level_independence(make_hierarchy_issue, make_sub_issue):
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
    root_issue = make_hierarchy_issue(900, IssueRecord.ISSUE_STATE_OPEN)
    root = HierarchyIssueRecord(root_issue)

    child_a_issue = make_hierarchy_issue(901, IssueRecord.ISSUE_STATE_CLOSED)
    child_a = HierarchyIssueRecord(child_a_issue)
    child_a.sub_issues.update(
        {
            "org/repo#911": make_sub_issue(911, IssueRecord.ISSUE_STATE_CLOSED),
        }
    )

    child_b_issue = make_hierarchy_issue(902, IssueRecord.ISSUE_STATE_CLOSED)
    child_b = HierarchyIssueRecord(child_b_issue)
    child_b.sub_issues.update(
        {
            "org/repo#921": make_sub_issue(921, IssueRecord.ISSUE_STATE_CLOSED),
            "org/repo#922": make_sub_issue(922, IssueRecord.ISSUE_STATE_CLOSED),
            "org/repo#923": make_sub_issue(923, IssueRecord.ISSUE_STATE_OPEN),
        }
    )

    child_c_issue = make_hierarchy_issue(903, IssueRecord.ISSUE_STATE_OPEN)
    child_c = HierarchyIssueRecord(child_c_issue)

    root.sub_hierarchy_issues.update(
        {
            "org/repo#901": child_a,
            "org/repo#902": child_b,
            "org/repo#903": child_c,
        }
    )

    assert root.progress == "2/3 done", f"root: {root.progress!r}"
    assert child_a.progress == "1/1 done", f"child_a: {child_a.progress!r}"
    assert child_b.progress == "2/3 done", f"child_b: {child_b.progress!r}"
    assert child_c.progress == "", f"child_c: {child_c.progress!r}"


def test_contains_change_increment_false_when_all_sub_issues_open(mocker, make_hierarchy_issue, make_sub_issue):
    """Bug regression: open hierarchy with only open sub-issues (with PRs) must not appear in release notes."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(10, IssueRecord.ISSUE_STATE_OPEN))

    sub1 = make_sub_issue(11, IssueRecord.ISSUE_STATE_OPEN)
    sub1.register_pull_request(make_minimal_pr(mocker, 111))
    sub2 = make_sub_issue(12, IssueRecord.ISSUE_STATE_OPEN)
    sub2.register_pull_request(make_minimal_pr(mocker, 112))
    parent.sub_issues.update({"org/repo#11": sub1, "org/repo#12": sub2})

    assert parent.contains_change_increment() is False


def test_contains_change_increment_true_when_one_closed_sub_issue_has_pr(mocker, make_hierarchy_issue, make_sub_issue):
    """A single closed sub-issue with a PR is enough to mark the parent as having a change increment."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(20, IssueRecord.ISSUE_STATE_OPEN))

    open_sub = make_sub_issue(21, IssueRecord.ISSUE_STATE_OPEN)
    open_sub.register_pull_request(make_minimal_pr(mocker, 211))
    closed_sub = make_sub_issue(22, IssueRecord.ISSUE_STATE_CLOSED)
    closed_sub.register_pull_request(make_minimal_pr(mocker, 212))
    parent.sub_issues.update({"org/repo#21": open_sub, "org/repo#22": closed_sub})

    assert parent.contains_change_increment() is True


def test_contains_change_increment_false_leaf_no_prs(make_hierarchy_issue):
    """A leaf hierarchy issue with no direct PRs and no children returns False."""
    record = HierarchyIssueRecord(make_hierarchy_issue(30, IssueRecord.ISSUE_STATE_OPEN))

    assert record.contains_change_increment() is False


def test_contains_change_increment_true_leaf_with_direct_pr(mocker, make_hierarchy_issue):
    """A hierarchy issue with a direct PR on itself (not from sub-issues) returns True."""
    record = HierarchyIssueRecord(make_hierarchy_issue(40, IssueRecord.ISSUE_STATE_OPEN))
    record.register_pull_request(make_minimal_pr(mocker, 401))

    assert record.contains_change_increment() is True


def test_contains_change_increment_true_cross_repo(make_hierarchy_issue):
    """Cross-repo records always return True regardless of sub-issue state."""
    record = HierarchyIssueRecord(make_hierarchy_issue(50, IssueRecord.ISSUE_STATE_OPEN))
    record.is_cross_repo = True

    assert record.contains_change_increment() is True


def test_contains_change_increment_false_nested_open_only(mocker, make_hierarchy_issue, make_sub_issue):
    """
    Regression: open root → open child hierarchy → open leaf sub-issues with PRs.

    The entire tree is open; no closed work exists → root must return False.
    """
    root = HierarchyIssueRecord(make_hierarchy_issue(60, IssueRecord.ISSUE_STATE_OPEN))
    child = HierarchyIssueRecord(make_hierarchy_issue(61, IssueRecord.ISSUE_STATE_OPEN))

    open_leaf = make_sub_issue(62, IssueRecord.ISSUE_STATE_OPEN)
    open_leaf.register_pull_request(make_minimal_pr(mocker, 621))
    child.sub_issues.update({"org/repo#62": open_leaf})
    root.sub_hierarchy_issues.update({"org/repo#61": child})

    assert root.contains_change_increment() is False


def test_contains_change_increment_true_nested_with_closed_leaf(mocker, make_hierarchy_issue, make_sub_issue):
    """
    Open root → open child hierarchy → one closed leaf sub-issue with a PR.

    A closed descendant exists → root must return True.
    """
    root = HierarchyIssueRecord(make_hierarchy_issue(70, IssueRecord.ISSUE_STATE_OPEN))
    child = HierarchyIssueRecord(make_hierarchy_issue(71, IssueRecord.ISSUE_STATE_OPEN))

    closed_leaf = make_sub_issue(72, IssueRecord.ISSUE_STATE_CLOSED)
    closed_leaf.register_pull_request(make_minimal_pr(mocker, 721))
    child.sub_issues.update({"org/repo#72": closed_leaf})
    root.sub_hierarchy_issues.update({"org/repo#71": child})

    assert root.contains_change_increment() is True
