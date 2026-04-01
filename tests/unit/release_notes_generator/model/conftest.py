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
Shared fixtures for model unit tests.
"""

from collections.abc import Callable
from datetime import datetime

import pytest
from pytest_mock import MockerFixture
from github.Issue import Issue

from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.sub_issue_record import SubIssueRecord


@pytest.fixture
def make_hierarchy_issue(mocker: MockerFixture) -> Callable[[int, str], Issue]:
    """Factory fixture that creates a mocked hierarchy Issue."""

    def _factory(number: int, state: str) -> Issue:
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

    return _factory


@pytest.fixture
def make_sub_issue(mocker: MockerFixture) -> Callable[[int, str], SubIssueRecord]:
    """Factory fixture that creates a mocked SubIssueRecord."""

    def _factory(number: int, state: str) -> SubIssueRecord:
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

    return _factory
