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

from datetime import datetime

from github.Issue import Issue
from github.IssueType import IssueType

from release_notes_generator.model.record.issue_record import IssueRecord


def _make_issue(mocker, type_name=None) -> Issue:

    if type_name:
        mock_issue_type = mocker.Mock(spec=IssueType)
        mock_issue_type.name = type_name
    else:
        mock_issue_type = None

    mock_issue = mocker.Mock(spec=Issue)
    mock_issue.id = 1
    mock_issue.number = 123
    mock_issue.title = "Issue 1"
    mock_issue.body = "Body of issue 1"
    mock_issue.state = "open"
    mock_issue.created_at = datetime.now()
    mock_issue.get_labels.return_value = []
    mock_issue.type = mock_issue_type

    return mock_issue


def test_issue_record_init_with_type_none(mocker):
    issue: Issue = _make_issue(mocker, type_name=None)
    record = IssueRecord(issue)
    assert record.issue_type is None


def test_issue_record_init_with_type_value(mocker):
    issue: Issue = _make_issue(mocker, type_name="enhancement")
    record = IssueRecord(issue)
    assert record.issue_type == "enhancement"
