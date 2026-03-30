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
Tests for HierarchyIssueRecord.
"""

from release_notes_generator.model.record.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.record.issue_record import IssueRecord
from tests.unit.conftest import (
    make_closed_sub_hierarchy_record_no_pr,
    make_closed_sub_hierarchy_record_with_pr,
    make_closed_sub_issue_record_no_pr,
    make_closed_sub_issue_record_with_pr,
    make_minimal_issue,
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

    record._sub_issues["450"] = make_closed_sub_issue_record_with_pr(mocker, number=450)
    record._sub_issues["400"] = make_open_sub_issue_record_no_pr(mocker, number=400)

    row = record.to_chapter_row()

    assert "#450" in row, f"Closed sub-issue #450 must appear; got:\n{row}"
    assert "#400" in row, f"Open sub-issue #400 must appear when parent is closed; got:\n{row}"


def test_to_chapter_row_open_parent_only_renders_closed_sub_issues_with_change_increment(mocker, patch_hierarchy_action_inputs):
    """
    Open parent with one closed sub-issue (has PR) and one open sub-issue (no PR) →
    only the closed sub-issue appears; open sub-issue is suppressed.
    """
    parent = make_minimal_issue(mocker, IssueRecord.ISSUE_STATE_OPEN, number=300)
    record = HierarchyIssueRecord(parent)

    record._sub_issues["450"] = make_closed_sub_issue_record_with_pr(mocker, number=450)
    record._sub_issues["400"] = make_open_sub_issue_record_no_pr(mocker, number=400)

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

    record._sub_issues["450"] = make_closed_sub_issue_record_no_pr(mocker, number=450)

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

