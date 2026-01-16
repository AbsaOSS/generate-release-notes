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
from github.Issue import Issue
from github.IssueType import IssueType
from github.PullRequest import PullRequest

from release_notes_generator.model.record.issue_record import IssueRecord


def make_mock_user(mocker, login: str):
    """Create a mock user with a login."""
    user = mocker.Mock()
    user.login = login
    return user


def make_mock_issue(mocker, number: int, title: str, type_name=None, assignees=None, author=None):
    """Create a mock Issue for testing."""
    mock_issue = mocker.Mock(spec=Issue)
    mock_issue.number = number
    mock_issue.title = title
    mock_issue.state = "closed"
    mock_issue.user = author or make_mock_user(mocker, "renovate[bot]")
    mock_issue.get_labels.return_value = []
    mock_issue.body = None  # No release notes by default
    
    if type_name:
        mock_issue_type = mocker.Mock(spec=IssueType)
        mock_issue_type.name = type_name
        mock_issue.type = mock_issue_type
    else:
        mock_issue.type = None
    
    if assignees:
        mock_issue.assignees = [make_mock_user(mocker, login) for login in assignees]
    else:
        mock_issue.assignees = []
    
    return mock_issue


def make_mock_pr(mocker, number: int, author_login: str):
    """Create a mock PullRequest for testing."""
    pr = mocker.Mock(spec=PullRequest)
    pr.number = number
    pr.user = make_mock_user(mocker, author_login)
    pr.get_labels.return_value = []
    pr.body = None  # No release notes by default
    return pr


class TestIssueRecordRowFormattingMissingFields:
    """Test cases for issue row formatting when fields are missing."""

    def test_missing_type_no_assignees_no_prs(self, mocker):
        """
        Test: issue with no type, no assignees, no PRs.
        Expected: No 'N/A:', no 'assigned to', no 'developed by' or 'in'.
        """
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
            return_value="{type}: {number} _{title}_ author is {author} assigned to {assignees} developed by {developers} in {pull-requests}"
        )
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
            return_value="🔔"
        )

        issue = make_mock_issue(mocker, 231, "Dependency Dashboard", type_name=None, assignees=None)
        record = IssueRecord(issue)

        row = record.to_chapter_row()

        # Should NOT contain any of these fragments when fields are empty
        assert "N/A" not in row, f"Row should not contain 'N/A', got: {row}"
        assert "assigned to" not in row, f"Row should not contain 'assigned to', got: {row}"
        assert "developed by" not in row, f"Row should not contain 'developed by', got: {row}"
        assert " in " not in row.lower() or " in #" in row.lower(), f"Row should not contain dangling 'in', got: {row}"
        
        # Should contain these
        assert "#231" in row
        assert "Dependency Dashboard" in row
        assert "@renovate[bot]" in row

    def test_missing_type_with_assignees(self, mocker):
        """
        Test: issue with no type but has assignees.
        Expected: No 'N/A:', should show assignees but no type prefix.
        """
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
            return_value="{type}: {number} _{title}_ assigned to {assignees}"
        )
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
            return_value="🔔"
        )

        issue = make_mock_issue(mocker, 100, "Fix bug", type_name=None, assignees=["alice", "bob"])
        record = IssueRecord(issue)

        row = record.to_chapter_row()

        assert "N/A" not in row, f"Row should not contain 'N/A', got: {row}"
        assert "#100" in row
        assert "Fix bug" in row
        assert "@alice" in row
        assert "@bob" in row
        assert "assigned to" in row  # Should show because assignees exist

    def test_has_type_missing_assignees_has_prs(self, mocker):
        """
        Test: issue with type and PRs but no assignees.
        Expected: Show type, no 'assigned to', show developers and PRs.
        """
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
            return_value="{type}: {number} _{title}_ assigned to {assignees} developed by {developers} in {pull-requests}"
        )
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
            return_value="🔔"
        )

        issue = make_mock_issue(mocker, 200, "Add feature", type_name="Task", assignees=None)
        record = IssueRecord(issue)
        
        # Add a PR to the record
        pr = make_mock_pr(mocker, 201, "charlie")
        record.register_pull_request(pr)

        row = record.to_chapter_row()

        assert "Task:" in row or "Task" in row, f"Row should contain type, got: {row}"
        assert "#200" in row
        assert "Add feature" in row
        assert "assigned to" not in row, f"Row should not contain 'assigned to', got: {row}"
        assert "developed by" in row  # Should show because there are developers
        assert "@charlie" in row
        assert "#201" in row

    def test_has_type_has_developers_has_prs(self, mocker):
        """
        Test: issue with all fields populated (control case).
        Expected: All fragments should be present.
        """
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
            return_value="{type}: {number} _{title}_ assigned to {assignees} developed by {developers} in {pull-requests}"
        )
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
            return_value="🔔"
        )

        issue = make_mock_issue(mocker, 300, "Complex feature", type_name="Feature", assignees=["alice"])
        record = IssueRecord(issue)
        
        pr = make_mock_pr(mocker, 301, "bob")
        record.register_pull_request(pr)

        row = record.to_chapter_row()

        # All fragments should be present
        assert "Feature:" in row or "Feature" in row
        assert "#300" in row
        assert "Complex feature" in row
        assert "assigned to" in row
        assert "@alice" in row
        assert "developed by" in row
        assert "@bob" in row or "@alice" in row  # developers include assignees
        assert "#301" in row

    def test_minimal_format_missing_type(self, mocker):
        """
        Test: simple format with just type, number, title when type is missing.
        Expected: No type prefix, just number and title.
        """
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
            return_value="{type}: {number} _{title}_"
        )
        mocker.patch(
            "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
            return_value="🔔"
        )

        issue = make_mock_issue(mocker, 400, "Simple issue", type_name=None)
        record = IssueRecord(issue)

        row = record.to_chapter_row()

        assert "N/A" not in row, f"Row should not contain 'N/A', got: {row}"
        assert "#400" in row
        assert "Simple issue" in row
