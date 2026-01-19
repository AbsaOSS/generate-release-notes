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
Tests for issue record row formatting with missing fields.
Tests that empty placeholders are properly suppressed in output.
"""

import pytest
from github.IssueType import IssueType

from release_notes_generator.model.record.issue_record import IssueRecord


def test_missing_type_no_assignees_no_prs(mocker, mock_issue_closed):
    """
    Test: issue with no type, no assignees, no PRs.
    Expected: No 'N/A:', no 'assigned to', no 'developed by' or 'in'.
    """
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
        return_value="{type}: {number} _{title}_ author is {author} assigned to {assignees} developed by {developers} in {pull-requests}",
    )
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
        return_value="🔔",
    )

    # Use existing fixture and modify it
    issue = mock_issue_closed
    issue.title = "Dependency Dashboard"
    issue.number = 231
    issue.type = None
    issue.assignees = []

    record = IssueRecord(issue)
    row = record.to_chapter_row()

    # Should NOT contain any of these fragments when fields are empty
    assert "N/A" not in row, f"Row should not contain 'N/A', got: {row}"
    assert "assigned to" not in row, f"Row should not contain 'assigned to', got: {row}"
    assert (
        "developed by" not in row
    ), f"Row should not contain 'developed by', got: {row}"
    assert (
        " in " not in row.lower() or " in #" in row.lower()
    ), f"Row should not contain dangling 'in', got: {row}"

    # Should contain these
    assert "#231" in row
    assert "Dependency Dashboard" in row
    # Author comes from issue.user which is already set in mock_issue_closed fixture


def test_missing_type_with_assignees(mocker, mock_issue_closed, mock_user):
    """
    Test: issue with no type but has assignees.
    Expected: No 'N/A:', should show assignees but no type prefix.
    """
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
        return_value="{type}: {number} _{title}_ assigned to {assignees}",
    )
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
        return_value="🔔",
    )

    issue = mock_issue_closed
    issue.title = "Fix bug"
    issue.number = 100
    issue.type = None

    # Create additional assignee
    mock_user2 = mocker.Mock()
    mock_user2.login = "bob"
    issue.assignees = [mock_user, mock_user2]

    record = IssueRecord(issue)
    row = record.to_chapter_row()

    assert "N/A" not in row, f"Row should not contain 'N/A', got: {row}"
    assert "#100" in row
    assert "Fix bug" in row
    assert "@user" in row
    assert "@bob" in row
    assert "assigned to" in row  # Should show because assignees exist


def test_has_type_missing_assignees_has_prs(mocker, mock_issue_closed, mock_pull_closed):
    """
    Test: issue with type and PRs but no assignees.
    Expected: Show type, no 'assigned to', show developers and PRs.
    """
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
        return_value="{type}: {number} _{title}_ assigned to {assignees} developed by {developers} in {pull-requests}",
    )
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
        return_value="🔔",
    )

    issue = mock_issue_closed
    issue.title = "Add feature"
    issue.number = 200
    mock_issue_type = mocker.Mock(spec=IssueType)
    mock_issue_type.name = "Task"
    issue.type = mock_issue_type
    issue.assignees = []

    record = IssueRecord(issue)

    # Add a PR to the record
    pr = mock_pull_closed
    pr.number = 201
    record.register_pull_request(pr)

    row = record.to_chapter_row()

    assert "Task:" in row or "Task" in row, f"Row should contain type, got: {row}"
    assert "#200" in row
    assert "Add feature" in row
    assert (
        "assigned to" not in row
    ), f"Row should not contain 'assigned to', got: {row}"
    assert "developed by" in row  # Should show because there are developers
    assert "#201" in row


def test_has_type_has_developers_has_prs(mocker, mock_issue_closed, mock_pull_closed):
    """
    Test: issue with all fields populated (control case).
    Expected: All fragments should be present.
    """
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
        return_value="{type}: {number} _{title}_ assigned to {assignees} developed by {developers} in {pull-requests}",
    )
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
        return_value="🔔",
    )

    issue = mock_issue_closed
    issue.title = "Complex feature"
    issue.number = 300
    mock_issue_type = mocker.Mock(spec=IssueType)
    mock_issue_type.name = "Feature"
    issue.type = mock_issue_type

    record = IssueRecord(issue)

    pr = mock_pull_closed
    pr.number = 301
    record.register_pull_request(pr)

    row = record.to_chapter_row()

    # All fragments should be present
    assert "Feature:" in row or "Feature" in row
    assert "#300" in row
    assert "Complex feature" in row
    assert "assigned to" in row
    assert "developed by" in row
    assert "#301" in row


def test_minimal_format_missing_type(mocker, mock_issue_closed):
    """
    Test: simple format with just type, number, title when type is missing.
    Expected: No type prefix, just number and title.
    """
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
        return_value="{type}: {number} _{title}_",
    )
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
        return_value="🔔",
    )

    issue = mock_issue_closed
    issue.title = "Simple issue"
    issue.number = 400
    issue.type = None

    record = IssueRecord(issue)
    row = record.to_chapter_row()

    assert "N/A" not in row, f"Row should not contain 'N/A', got: {row}"
    assert "#400" in row
    assert "Simple issue" in row
