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



def test_progress_leaf_node_returns_empty_string(make_hierarchy_issue):
    """HierarchyIssueRecord with no direct sub-issues returns '' for progress."""
    issue = make_hierarchy_issue(100, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    assert record.progress == ""


def test_progress_leaf_node_suppressed_in_row(mocker, make_hierarchy_issue):
    """"_{title}_ {number} {progress}" token in format template produces no extra whitespace when leaf."""
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
    record.sub_issues.update({
        "org/repo#401": make_sub_issue(401, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#402": make_sub_issue(402, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#403": make_sub_issue(403, IssueRecord.ISSUE_STATE_OPEN),
    })
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

    record.sub_issues.update({
        "org/repo#401": make_sub_issue(401, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#402": make_sub_issue(402, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#403": make_sub_issue(403, IssueRecord.ISSUE_STATE_OPEN),
    })

    assert record.progress == "2/3 done"


def test_progress_all_closed(make_hierarchy_issue, make_sub_issue):
    """All direct sub-issues closed → 'Y/Y done'."""
    issue = make_hierarchy_issue(201, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record.sub_issues.update({
        "org/repo#501": make_sub_issue(501, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#502": make_sub_issue(502, IssueRecord.ISSUE_STATE_CLOSED),
    })

    assert record.progress == "2/2 done"


def test_progress_all_open(make_hierarchy_issue, make_sub_issue):
    """All direct sub-issues open → '0/N done'."""
    issue = make_hierarchy_issue(202, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(issue)

    record.sub_issues.update({
        "org/repo#601": make_sub_issue(601, IssueRecord.ISSUE_STATE_OPEN),
        "org/repo#602": make_sub_issue(602, IssueRecord.ISSUE_STATE_OPEN),
    })

    assert record.progress == "0/2 done"


def test_progress_mixed_sub_issues_and_sub_hierarchy_issues(make_hierarchy_issue, make_sub_issue):
    """Direct children include both SubIssueRecord and sub HierarchyIssueRecord."""
    parent_issue = make_hierarchy_issue(300, IssueRecord.ISSUE_STATE_OPEN)
    record = HierarchyIssueRecord(parent_issue)

    # 1 closed sub-issue
    record.sub_issues.update({
        "org/repo#701": make_sub_issue(701, IssueRecord.ISSUE_STATE_CLOSED),
    })

    # 1 open sub-hierarchy-issue, 1 closed sub-hierarchy-issue
    child_open_issue = make_hierarchy_issue(801, IssueRecord.ISSUE_STATE_OPEN)
    child_closed_issue = make_hierarchy_issue(802, IssueRecord.ISSUE_STATE_CLOSED)
    record.sub_hierarchy_issues.update({
        "org/repo#801": HierarchyIssueRecord(child_open_issue),
        "org/repo#802": HierarchyIssueRecord(child_closed_issue),
    })

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
    child_a.sub_issues.update({
        "org/repo#911": make_sub_issue(911, IssueRecord.ISSUE_STATE_CLOSED),
    })

    child_b_issue = make_hierarchy_issue(902, IssueRecord.ISSUE_STATE_CLOSED)
    child_b = HierarchyIssueRecord(child_b_issue)
    child_b.sub_issues.update({
        "org/repo#921": make_sub_issue(921, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#922": make_sub_issue(922, IssueRecord.ISSUE_STATE_CLOSED),
        "org/repo#923": make_sub_issue(923, IssueRecord.ISSUE_STATE_OPEN),
    })

    child_c_issue = make_hierarchy_issue(903, IssueRecord.ISSUE_STATE_OPEN)
    child_c = HierarchyIssueRecord(child_c_issue)

    root.sub_hierarchy_issues.update({
        "org/repo#901": child_a,
        "org/repo#902": child_b,
        "org/repo#903": child_c,
    })

    assert root.progress == "2/3 done", f"root: {root.progress!r}"
    assert child_a.progress == "1/1 done", f"child_a: {child_a.progress!r}"
    assert child_b.progress == "2/3 done", f"child_b: {child_b.progress!r}"
    assert child_c.progress == "", f"child_c: {child_c.progress!r}"


def _make_mock_pull(mocker, number: int):
    """Create a minimal mock PullRequest with the given number."""
    from github.PullRequest import PullRequest as GHPullRequest
    pull = mocker.Mock(spec=GHPullRequest)
    pull.number = number
    pull.get_labels.return_value = []
    return pull


def test_contains_change_increment_false_when_all_sub_issues_open(mocker, make_hierarchy_issue, make_sub_issue):
    """Bug regression: open hierarchy with only open sub-issues (with PRs) must not appear in release notes."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(10, IssueRecord.ISSUE_STATE_OPEN))

    sub1 = make_sub_issue(11, IssueRecord.ISSUE_STATE_OPEN)
    sub1.register_pull_request(_make_mock_pull(mocker, 111))
    sub2 = make_sub_issue(12, IssueRecord.ISSUE_STATE_OPEN)
    sub2.register_pull_request(_make_mock_pull(mocker, 112))
    parent.sub_issues.update({"org/repo#11": sub1, "org/repo#12": sub2})

    assert parent.contains_change_increment() is False


def test_contains_change_increment_true_when_one_closed_sub_issue_has_pr(mocker, make_hierarchy_issue, make_sub_issue):
    """A single closed sub-issue with a PR is enough to mark the parent as having a change increment."""
    parent = HierarchyIssueRecord(make_hierarchy_issue(20, IssueRecord.ISSUE_STATE_OPEN))

    open_sub = make_sub_issue(21, IssueRecord.ISSUE_STATE_OPEN)
    open_sub.register_pull_request(_make_mock_pull(mocker, 211))
    closed_sub = make_sub_issue(22, IssueRecord.ISSUE_STATE_CLOSED)
    closed_sub.register_pull_request(_make_mock_pull(mocker, 212))
    parent.sub_issues.update({"org/repo#21": open_sub, "org/repo#22": closed_sub})

    assert parent.contains_change_increment() is True


def test_contains_change_increment_false_leaf_no_prs(make_hierarchy_issue):
    """A leaf hierarchy issue with no direct PRs and no children returns False."""
    record = HierarchyIssueRecord(make_hierarchy_issue(30, IssueRecord.ISSUE_STATE_OPEN))

    assert record.contains_change_increment() is False


def test_contains_change_increment_true_leaf_with_direct_pr(mocker, make_hierarchy_issue):
    """A hierarchy issue with a direct PR on itself (not from sub-issues) returns True."""
    record = HierarchyIssueRecord(make_hierarchy_issue(40, IssueRecord.ISSUE_STATE_OPEN))
    record.register_pull_request(_make_mock_pull(mocker, 401))

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
    open_leaf.register_pull_request(_make_mock_pull(mocker, 621))
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
    closed_leaf.register_pull_request(_make_mock_pull(mocker, 721))
    child.sub_issues.update({"org/repo#72": closed_leaf})
    root.sub_hierarchy_issues.update({"org/repo#71": child})

    assert root.contains_change_increment() is True
