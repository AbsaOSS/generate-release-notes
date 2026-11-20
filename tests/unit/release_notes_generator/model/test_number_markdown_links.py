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
Tests that record numbers in chapter rows are full markdown links.

A newly created release draft does not auto-link bare ``#N`` references - the
links only appear after the draft is edited and saved (issue #359), so the
generator emits fully specified markdown links instead.
"""

import pytest

from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.pull_request_record import PullRequestRecord


ISSUE_LINK = "[#231](https://github.com/org/repo/issues/231)"
PR_LINK = "[#123](https://github.com/org/repo/pull/123)"


@pytest.fixture
def row_format(mocker):
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_row_format_issue",
        return_value="{type}: {number} _{title}_ developed by {developers} in {pull-requests}",
    )
    mocker.patch(
        "release_notes_generator.model.record.pull_request_record.ActionInputs.get_row_format_pr",
        return_value="{number} _{title}_ developed by {developers}",
    )
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_duplicity_icon",
        return_value="🔔",
    )
    mocker.patch(
        "release_notes_generator.model.record.pull_request_record.ActionInputs.get_row_format_link_pr",
        return_value=False,
    )


def test_issue_number_is_full_markdown_link(mocker, mock_issue_closed, row_format):
    issue = mock_issue_closed
    issue.title = "Dependency Dashboard"
    issue.number = 231
    issue.type = None
    issue.repository.full_name = "org/repo"

    row = IssueRecord(issue).to_chapter_row()

    assert ISSUE_LINK in row, f"Row should contain the full issue link, got: {row}"
    assert "{number}" not in row


def test_pr_link_value_is_full_markdown_link(mocker, mock_issue_closed, mock_pull_closed, row_format):
    issue = mock_issue_closed
    issue.number = 231
    issue.title = "Dependency Dashboard"
    issue.type = None
    issue.repository.full_name = "org/repo"

    record = IssueRecord(issue)
    record.register_pull_request(mock_pull_closed)

    row = record.to_chapter_row()

    assert f"in {PR_LINK}" in row, f"Row should contain the full PR link, got: {row}"


def test_pull_request_record_number_is_full_markdown_link(mocker, mock_pull_closed, row_format):
    pull = mock_pull_closed
    pull.title = "Fixed bug"

    repo = mocker.Mock()
    repo.full_name = "org/repo"

    row = PullRequestRecord(pull, repo).to_chapter_row()

    assert PR_LINK in row, f"Row should contain the full PR link, got: {row}"
