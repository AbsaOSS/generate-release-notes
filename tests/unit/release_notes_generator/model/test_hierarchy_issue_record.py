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
from release_notes_generator.model.record.sub_issue_record import SubIssueRecord
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


def test_to_chapter_row_open_sub_hierarchy_icon_placed_after_list_marker(mocker, patch_hierarchy_action_inputs):
    """Icon must appear after the '- ' list marker, not before it.

    Correct:   '  - 🟡 _title_ #360'
    Wrong:     '  🟡 - _title_ #360'
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    record = HierarchyIssueRecord(parent)
    child = make_open_sub_hierarchy_record_with_pr(mocker, number=360)
    child.level = 1
    record.sub_hierarchy_issues["360"] = child

    row = record.to_chapter_row()

    open_line = next((l for l in row.splitlines() if "#360" in l), None)
    assert open_line is not None
    stripped = open_line.lstrip()
    assert stripped.startswith("- 🟡 "), (
        f"Expected '- 🟡 ' after leading spaces; got: {open_line!r}"
    )


def test_to_chapter_row_empty_icon_leaves_no_stray_space(mocker, patch_hierarchy_action_inputs):
    """When open-hierarchy-sub-issue-icon is '', the row indentation is unchanged (no stray space)."""
    mocker.patch(
        "release_notes_generator.model.record.hierarchy_issue_record.ActionInputs.get_open_hierarchy_sub_issue_icon",
        return_value="",
    )
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    record = HierarchyIssueRecord(parent)
    child = make_open_sub_hierarchy_record_with_pr(mocker, number=360)
    child.level = 1
    record.sub_hierarchy_issues["360"] = child

    row = record.to_chapter_row()

    open_line = next((l for l in row.splitlines() if "#360" in l), None)
    assert open_line is not None
    assert open_line.startswith("  - "), (
        f"Level-1 row must start with exactly '  - ' (2 spaces); got: {open_line!r}"
    )
    assert not open_line.startswith("   "), (
        f"No stray extra space in indentation with empty icon; got: {open_line!r}"
    )


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


# --- has_matching_labels ---


def test_has_matching_labels_own_label_matches(make_hierarchy_issue):
    """Parent's own labels trigger a match."""
    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    issue.get_labels.return_value = [type("L", (), {"name": "frontend"})()]
    record = HierarchyIssueRecord(issue, issue_labels=["frontend"])

    assert record.has_matching_labels(["frontend"]) is True


def test_has_matching_labels_sub_issue_label_matches(mocker, make_hierarchy_issue):
    """A sub-issue label satisfies the filter even when the parent has no matching labels."""
    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue, issue_labels=["epic"])

    sub_issue = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=200)
    sub_record = SubIssueRecord(sub_issue, issue_labels=["frontend"])
    record.sub_issues["200"] = sub_record

    assert record.has_matching_labels(["frontend"]) is True
    assert record.has_matching_labels(["backend"]) is False


def test_has_matching_labels_recursive_through_sub_hierarchy(mocker, make_hierarchy_issue):
    """Label matching recurses through nested HierarchyIssueRecords."""
    root_issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    root = HierarchyIssueRecord(root_issue, issue_labels=["epic"])

    child_issue = make_hierarchy_issue(200, IssueRecord.ISSUE_STATE_OPEN)
    child = HierarchyIssueRecord(child_issue, issue_labels=["sub-epic"])

    leaf_issue = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    leaf = SubIssueRecord(leaf_issue, issue_labels=["backend"])
    child.sub_issues["300"] = leaf

    root.sub_hierarchy_issues["200"] = child

    assert root.has_matching_labels(["backend"]) is True
    assert root.has_matching_labels(["frontend"]) is False


def test_has_matching_labels_no_match_returns_false(make_hierarchy_issue):
    """Returns False when no labels match anywhere in the tree."""
    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue, issue_labels=["epic"])

    assert record.has_matching_labels(["frontend"]) is False


# --- to_chapter_row with label_filter ---


def test_to_chapter_row_label_filter_includes_matching_sub_issues(mocker, patch_hierarchy_action_inputs):
    """Only sub-issues whose labels intersect label_filter appear in the output."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1)
    record = HierarchyIssueRecord(parent)

    fe_sub = make_closed_sub_issue_record_with_pr(mocker, number=2, issue_labels=["enhancement", "frontend"])
    be_sub = make_closed_sub_issue_record_with_pr(mocker, number=3, issue_labels=["enhancement", "backend"])
    record.sub_issues["2"] = fe_sub
    record.sub_issues["3"] = be_sub

    row = record.to_chapter_row(label_filter=["frontend"])

    assert "#2" in row, f"Frontend sub-issue #2 should appear; got:\n{row}"
    assert "#3" not in row, f"Backend sub-issue #3 should NOT appear; got:\n{row}"


def test_to_chapter_row_label_filter_includes_matching_sub_hierarchy(mocker, patch_hierarchy_action_inputs):
    """Sub-hierarchy issues are filtered by label_filter recursively."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1)
    record = HierarchyIssueRecord(parent)

    fe_child = make_closed_sub_hierarchy_record_with_pr(mocker, number=10, issue_labels=["frontend"])
    be_child = make_closed_sub_hierarchy_record_with_pr(mocker, number=20, issue_labels=["backend"])
    record.sub_hierarchy_issues["10"] = fe_child
    record.sub_hierarchy_issues["20"] = be_child

    row = record.to_chapter_row(label_filter=["frontend"])

    assert "#10" in row, f"Frontend sub-hierarchy #10 should appear; got:\n{row}"
    assert "#20" not in row, f"Backend sub-hierarchy #20 should NOT appear; got:\n{row}"


def test_to_chapter_row_no_label_filter_renders_all(mocker, patch_hierarchy_action_inputs):
    """Without label_filter, all sub-issues render (existing behaviour preserved)."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1)
    record = HierarchyIssueRecord(parent)

    fe_sub = make_closed_sub_issue_record_with_pr(mocker, number=2, issue_labels=["frontend"])
    be_sub = make_closed_sub_issue_record_with_pr(mocker, number=3, issue_labels=["backend"])
    record.sub_issues["2"] = fe_sub
    record.sub_issues["3"] = be_sub

    row = record.to_chapter_row()

    assert "#2" in row
    assert "#3" in row


def test_has_unmatched_descendants_true_when_sub_issue_has_no_matching_label(mocker, make_hierarchy_issue):
    """Returns True when at least one sub-issue does not match the label set."""
    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue, issue_labels=["epic"])

    matched = SubIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, 200), issue_labels=["security"])
    unmatched = SubIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, 201), issue_labels=["other"])
    record.sub_issues["200"] = matched
    record.sub_issues["201"] = unmatched

    assert record.has_unmatched_descendants(["security"]) is True


def test_has_unmatched_descendants_false_when_all_match(mocker, make_hierarchy_issue):
    """Returns False when every descendant matches the label set."""
    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue, issue_labels=["epic"])

    s1 = SubIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, 200), issue_labels=["security"])
    s2 = SubIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, 201), issue_labels=["security", "bug"])
    record.sub_issues["200"] = s1
    record.sub_issues["201"] = s2

    assert record.has_unmatched_descendants(["security"]) is False


def test_has_unmatched_descendants_recursive(mocker, make_hierarchy_issue):
    """Recurses through sub-hierarchy-issues to find unmatched descendants."""
    root = HierarchyIssueRecord(make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN), issue_labels=["epic"])
    child = HierarchyIssueRecord(make_hierarchy_issue(200, IssueRecord.ISSUE_STATE_OPEN), issue_labels=["sub-epic"])
    leaf = SubIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, 300), issue_labels=["other"])
    child.sub_issues["300"] = leaf
    root.sub_hierarchy_issues["200"] = child

    assert root.has_unmatched_descendants(["security"]) is True


def test_has_unmatched_descendants_empty_tree(make_hierarchy_issue):
    """A leaf hierarchy issue with no descendants returns False (nothing to be unmatched)."""
    record = HierarchyIssueRecord(make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN))

    assert record.has_unmatched_descendants(["security"]) is False


def test_to_chapter_row_exclude_labels_hides_matching_sub_issues(mocker, patch_hierarchy_action_inputs):
    """Sub-issues whose labels intersect exclude_labels are hidden from the output."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1)
    record = HierarchyIssueRecord(parent)

    sec_sub = make_closed_sub_issue_record_with_pr(mocker, number=2, issue_labels=["enhancement", "scope:security"])
    plain_sub = make_closed_sub_issue_record_with_pr(mocker, number=3, issue_labels=["enhancement"])
    record.sub_issues["2"] = sec_sub
    record.sub_issues["3"] = plain_sub

    row = record.to_chapter_row(exclude_labels=["scope:security"])

    assert "#3" in row, f"Non-security sub-issue should appear; got:\n{row}"
    assert "#2" not in row, f"Security sub-issue should be excluded; got:\n{row}"


def test_to_chapter_row_exclude_labels_hides_matching_sub_hierarchy(mocker, patch_hierarchy_action_inputs):
    """Sub-hierarchy issue with only SC-matching labels is hidden by exclude_labels.

    A leaf sub-hierarchy node whose own labels all match exclude_labels and which
    has no unmatched descendants is excluded from the Uncategorized render.
    A sibling leaf whose labels do NOT match is kept.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1)
    record = HierarchyIssueRecord(parent)

    sec_child = make_closed_sub_hierarchy_record_with_pr(mocker, number=10, issue_labels=["scope:security"])
    plain_child = make_closed_sub_hierarchy_record_with_pr(mocker, number=20, issue_labels=["other"])
    record.sub_hierarchy_issues["10"] = sec_child
    record.sub_hierarchy_issues["20"] = plain_child

    row = record.to_chapter_row(exclude_labels=["scope:security"])

    assert "#20" in row, f"Non-security sub-hierarchy should appear; got:\n{row}"
    assert "#10" not in row, f"Security sub-hierarchy should be excluded; got:\n{row}"


def test_to_chapter_row_exclude_labels_none_renders_all(mocker, patch_hierarchy_action_inputs):
    """Without exclude_labels, all sub-issues render (backward compatible)."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1)
    record = HierarchyIssueRecord(parent)

    s1 = make_closed_sub_issue_record_with_pr(mocker, number=2, issue_labels=["scope:security"])
    s2 = make_closed_sub_issue_record_with_pr(mocker, number=3, issue_labels=["other"])
    record.sub_issues["2"] = s1
    record.sub_issues["3"] = s2

    row = record.to_chapter_row()

    assert "#2" in row
    assert "#3" in row


def test_to_chapter_row_exclude_labels_keeps_sub_hierarchy_with_mixed_descendants(mocker, patch_hierarchy_action_inputs):
    """Sub-hierarchy issue with SOME matching descendants is kept (not hidden) by exclude_labels.

    Real-data scenario:
      Epic (level 0)
        Feature (level 1) — aggregates scope:security from Task2
          Task1 (no scope:security)  → must appear in Uncategorized
          Task2 (scope:security)     → must be excluded from Uncategorized

    Bug: Feature's aggregated labels include scope:security so has_matching_labels returns True,
    causing the entire Feature branch to be skipped — leaving only the Epic root line.
    Fix: skip Feature only when ALL its descendants are SC-covered (has_unmatched_descendants=False).
    """
    epic = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1))

    feature = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=10), issue_labels=["security"])

    task1 = make_closed_sub_issue_record_with_pr(mocker, number=20, issue_labels=["enhancement"])
    task2 = make_closed_sub_issue_record_with_pr(mocker, number=21, issue_labels=["enhancement", "scope:security"])

    feature.sub_issues["20"] = task1
    feature.sub_issues["21"] = task2
    epic.sub_hierarchy_issues["10"] = feature

    row = epic.to_chapter_row(exclude_labels=["scope:security"])

    assert "#10" in row, f"Feature should appear (has non-SC sub-issue Task1); got:\n{row}"
    assert "#20" in row, f"Task1 (no SC label) should appear; got:\n{row}"
    assert "#21" not in row, f"Task2 (scope:security) should be excluded; got:\n{row}"


def test_to_chapter_row_exclude_labels_hides_sub_hierarchy_when_all_descendants_match(
    mocker, patch_hierarchy_action_inputs
):
    """Sub-hierarchy issue is hidden when ALL its descendants match exclude_labels."""
    epic = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1))

    feature = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=10), issue_labels=["security"])

    task2 = make_closed_sub_issue_record_with_pr(mocker, number=21, issue_labels=["enhancement", "scope:security"])

    feature.sub_issues["21"] = task2
    epic.sub_hierarchy_issues["10"] = feature

    row = epic.to_chapter_row(exclude_labels=["scope:security"])

    assert "#10" not in row, f"Feature should be hidden (all descendants have SC label); got:\n{row}"
    assert "#21" not in row, f"Task2 should be excluded; got:\n{row}"


def test_get_labels_aggregates_deep_sub_hierarchy_labels(mocker, make_hierarchy_issue):
    """get_labels() must recursively aggregate labels from nested HierarchyIssueRecords.

    Bug: previous implementation used sub_hierarchy_issue.labels (own labels only),
    so a label that exists only on a grandchild was invisible to the root Epic.
    This caused the root Epic to be missing from claimed_ids and therefore never rendered
    in the matching super chapter.
    """
    root_issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_CLOSED)
    root = HierarchyIssueRecord(root_issue, issue_labels=["epic"])

    feature_issue = make_hierarchy_issue(200, IssueRecord.ISSUE_STATE_CLOSED)
    feature = HierarchyIssueRecord(feature_issue, issue_labels=["feature"])  # no "scope:security"

    leaf_issue = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    leaf = SubIssueRecord(leaf_issue, issue_labels=["scope:security"])
    feature.sub_issues["300"] = leaf

    root.sub_hierarchy_issues["200"] = feature

    result = root.get_labels()

    assert "scope:security" in result, (
        "Root Epic must aggregate 'scope:security' from grandchild leaf; got: " + str(result)
    )


def test_to_chapter_row_sub_issues_rendered_in_ascending_number_order(mocker, patch_hierarchy_action_inputs):
    """Leaf sub-issues must be rendered sorted ascending by issue number regardless of insertion order."""
    parent = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1))

    high = make_closed_sub_issue_record_with_pr(mocker, number=4150)
    low = make_closed_sub_issue_record_with_pr(mocker, number=4149)

    # Intentionally insert higher number first
    parent.sub_issues["4150"] = high
    parent.sub_issues["4149"] = low

    row = parent.to_chapter_row()

    pos_low = row.index("#4149")
    pos_high = row.index("#4150")
    assert pos_low < pos_high, f"#4149 must appear before #4150; got:\n{row}"


def test_to_chapter_row_sub_hierarchy_issues_rendered_in_ascending_number_order(
    mocker, patch_hierarchy_action_inputs
):
    """Sub-hierarchy issues must be rendered sorted ascending by issue number regardless of insertion order."""
    parent = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1))

    high = make_closed_sub_hierarchy_record_with_pr(mocker, number=200)
    high.level = 1
    low = make_closed_sub_hierarchy_record_with_pr(mocker, number=100)
    low.level = 1

    # Intentionally insert higher number first
    parent.sub_hierarchy_issues["200"] = high
    parent.sub_hierarchy_issues["100"] = low

    row = parent.to_chapter_row()

    pos_low = row.index("#100")
    pos_high = row.index("#200")
    assert pos_low < pos_high, f"#100 must appear before #200; got:\n{row}"


def test_five_level_hierarchy_label_filter_and_exclude_labels(mocker, patch_hierarchy_action_inputs):
    """All recursive methods work correctly at 5 levels of nesting.

    Tree:
      L1: Epic #1        (labels: epic)
        L2: Theme #2     (labels: theme)
          L3: Feature #3 (labels: feature)
            L4: Story #4 (labels: story)
              L5a: Task #10 (labels: scope:security)   ← SC match
              L5b: Task #11 (labels: enhancement)       ← no SC label

    Verified behaviours:
    - get_labels() on L1 includes scope:security (aggregated from 4 levels down)
    - has_matching_labels(["scope:security"]) on L1 is True
    - has_unmatched_descendants(["scope:security"]) on L1 is True (Task #11 is unmatched)
    - to_chapter_row(label_filter=["scope:security"]) shows only the SC path down to Task #10
    - to_chapter_row(exclude_labels=["scope:security"]) shows the non-SC path down to Task #11
      and omits Task #10
    """
    # Build bottom-up: Task leaves first
    task_sc = make_closed_sub_issue_record_with_pr(mocker, number=10, issue_labels=["scope:security"])
    task_plain = make_closed_sub_issue_record_with_pr(mocker, number=11, issue_labels=["enhancement"])

    story = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=4), issue_labels=["story"])
    story.level = 3
    story.sub_issues["10"] = task_sc
    story.sub_issues["11"] = task_plain

    feature = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=3), issue_labels=["feature"])
    feature.level = 2
    feature.sub_hierarchy_issues["4"] = story

    theme = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=2), issue_labels=["theme"])
    theme.level = 1
    theme.sub_hierarchy_issues["3"] = feature

    epic = HierarchyIssueRecord(make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=1), issue_labels=["epic"])
    epic.sub_hierarchy_issues["2"] = theme

    # --- get_labels aggregates across all 5 levels ---
    all_labels = epic.get_labels()
    assert "scope:security" in all_labels, f"scope:security must bubble up to L1; got {all_labels}"
    assert "enhancement" in all_labels, f"enhancement must bubble up to L1; got {all_labels}"

    # --- has_matching_labels ---
    assert epic.has_matching_labels(["scope:security"]) is True
    assert epic.has_matching_labels(["unknown"]) is False

    # --- has_unmatched_descendants ---
    # Task #11 has no scope:security → True
    assert epic.has_unmatched_descendants(["scope:security"]) is True
    # Both leaf labels covered → False
    assert epic.has_unmatched_descendants(["scope:security", "enhancement"]) is False

    # --- to_chapter_row with label_filter: only SC path visible ---
    row_sc = epic.to_chapter_row(label_filter=["scope:security"])
    assert "#1" in row_sc, f"Epic root must appear; got:\n{row_sc}"
    assert "#2" in row_sc, f"Theme must appear (contains SC path); got:\n{row_sc}"
    assert "#3" in row_sc, f"Feature must appear (contains SC path); got:\n{row_sc}"
    assert "#4" in row_sc, f"Story must appear (contains SC path); got:\n{row_sc}"
    assert "#10" in row_sc, f"SC task must appear; got:\n{row_sc}"
    assert "#11" not in row_sc, f"Plain task must be excluded; got:\n{row_sc}"

    # --- to_chapter_row with exclude_labels: only non-SC path visible ---
    row_plain = epic.to_chapter_row(exclude_labels=["scope:security"])
    assert "#1" in row_plain, f"Epic root must appear; got:\n{row_plain}"
    assert "#2" in row_plain, f"Theme must appear (has non-SC path); got:\n{row_plain}"
    assert "#3" in row_plain, f"Feature must appear (has non-SC path); got:\n{row_plain}"
    assert "#4" in row_plain, f"Story must appear (has non-SC path); got:\n{row_plain}"
    assert "#11" in row_plain, f"Plain task must appear; got:\n{row_plain}"
    assert "#10" not in row_plain, f"SC task must be excluded; got:\n{row_plain}"


def test_developers_returns_empty_list_when_issue_is_none():
    """developers returns [] when the underlying issue is None (defensive guard)."""
    record = HierarchyIssueRecord(None)  # type: ignore[arg-type]
    assert record.developers == []


def test_pull_requests_count_cross_repo_sub_issue(mocker, make_hierarchy_issue):
    """A cross-repo sub-issue counts as 1 PR regardless of its own pull-request list."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN))
    sub = SubIssueRecord(make_hierarchy_issue(200, IssueRecord.ISSUE_STATE_CLOSED))
    sub.is_cross_repo = True
    parent.sub_issues["org/repo#200"] = sub

    assert parent.pull_requests_count() == 1


def test_pull_requests_count_cross_repo_sub_hierarchy_issue(mocker, make_hierarchy_issue):
    """A cross-repo sub-hierarchy-issue counts as 1 PR."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN))
    child = HierarchyIssueRecord(make_hierarchy_issue(200, IssueRecord.ISSUE_STATE_CLOSED))
    child.is_cross_repo = True
    parent.sub_hierarchy_issues["org/repo#200"] = child

    assert parent.pull_requests_count() == 1


def test_get_labels_includes_pr_labels(mocker, make_hierarchy_issue, make_sub_issue):
    """get_labels aggregates labels from attached pull requests."""
    issue = make_hierarchy_issue(10, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    pr = mocker.Mock()
    mock_label = mocker.Mock()
    mock_label.name = "pr-label"
    pr.get_labels.return_value = [mock_label]
    record.register_pull_request(pr)

    labels = record.get_labels()
    assert "pr-label" in labels


def test_has_unmatched_descendants_leaf_hierarchy_child_unmatched(mocker, make_hierarchy_issue):
    """Leaf sub-hierarchy-issue whose own labels don't match the SC set returns True."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(1, IssueRecord.ISSUE_STATE_OPEN))

    leaf_issue = make_hierarchy_issue(2, IssueRecord.ISSUE_STATE_OPEN)
    other_label = mocker.Mock()
    other_label.name = "other-label"
    leaf_issue.get_labels.return_value = [other_label]
    leaf = HierarchyIssueRecord(leaf_issue)
    parent.sub_hierarchy_issues["org/repo#2"] = leaf

    assert parent.has_unmatched_descendants(["sc-label"]) is True


def test_has_unmatched_descendants_leaf_hierarchy_child_matched(mocker, make_hierarchy_issue):
    """Leaf sub-hierarchy-issue whose labels match the SC set returns False."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(1, IssueRecord.ISSUE_STATE_OPEN))

    leaf_issue = make_hierarchy_issue(2, IssueRecord.ISSUE_STATE_OPEN)
    sc_label = mocker.Mock()
    sc_label.name = "sc-label"
    leaf_issue.get_labels.return_value = [sc_label]
    leaf = HierarchyIssueRecord(leaf_issue)
    parent.sub_hierarchy_issues["org/repo#2"] = leaf

    assert parent.has_unmatched_descendants(["sc-label"]) is False


# --- release notes block rendering ---


def test_to_chapter_row_renders_release_notes_heading_and_content(mocker, patch_hierarchy_action_inputs):
    """Issue body with a Release Notes section is rendered as an indented block by to_chapter_row()."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    parent.body = "Description\nRelease Notes:\n- Fixed the critical bug"
    record = HierarchyIssueRecord(parent)

    row = record.to_chapter_row()

    assert "_Release Notes_:" in row, f"Release Notes heading must appear; got:\n{row}"
    assert "Fixed the critical bug" in row, f"Release notes content must appear; got:\n{row}"


def test_to_chapter_row_release_notes_block_indented_relative_to_level(mocker, patch_hierarchy_action_inputs):
    """Release Notes heading is indented one level deeper than the issue's own hierarchy level."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=300)
    parent.body = "Description\nRelease Notes:\n- Fixed the critical bug"
    record = HierarchyIssueRecord(parent)
    record.level = 0

    row = record.to_chapter_row()

    rls_line = next((line for line in row.splitlines() if "_Release Notes_:" in line), None)
    assert rls_line is not None, f"Release Notes heading line missing; got:\n{row}"
    assert rls_line.startswith("  - "), (
        f"At level 0 heading must start with '  - ' (2-space indent + list marker); got: {rls_line!r}"
    )


def test_to_chapter_row_no_release_notes_body_omits_block(mocker, patch_hierarchy_action_inputs):
    """Issue body without a Release Notes section produces no Release Notes heading."""
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_CLOSED, number=301)
    parent.body = "Just a plain description with no special section."
    record = HierarchyIssueRecord(parent)

    row = record.to_chapter_row()

    assert "_Release Notes_:" not in row, f"No Release Notes heading expected; got:\n{row}"
