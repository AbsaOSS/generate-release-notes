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
import re
from datetime import datetime

import pytest
from github.Issue import Issue
from github.IssueType import IssueType

from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.utils.record_utils import get_rls_notes_code_rabbit


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


@pytest.fixture
def issue_record(mocker):
    issue = mocker.Mock()
    issue.type = None
    issue.number = 123
    issue.state = "closed"
    issue.user = None
    return IssueRecord(issue)


def make_pr(mocker, body: str | None):
    pr = mocker.Mock()
    pr.body = body
    pr.number = 10
    return pr


CR_REGEX = re.compile("Summary by CodeRabbit")
LINE_MARKS = ["-", "*"]  # mimic IssueRecord.RELEASE_NOTE_LINE_MARKS


def test_issue_record_init_with_type_none(mocker):
    issue: Issue = _make_issue(mocker, type_name=None)
    record = IssueRecord(issue)
    assert record.issue_type is None


def test_issue_record_init_with_type_value(mocker):
    issue: Issue = _make_issue(mocker, type_name="enhancement")
    record = IssueRecord(issue)
    assert record.issue_type == "enhancement"


def test_code_rabbit_empty_body(issue_record, mocker):
    mocker.patch("release_notes_generator.model.record.issue_record.ActionInputs.get_coderabbit_summary_ignore_groups", return_value=[])
    pr = make_pr(mocker, None)
    out = get_rls_notes_code_rabbit(pr.body, LINE_MARKS, CR_REGEX)
    assert out == ""


def test_code_rabbit_extract_basic(issue_record, mocker):
    mocker.patch("release_notes_generator.model.record.issue_record.ActionInputs.get_coderabbit_summary_ignore_groups", return_value=[])
    body = """Intro line
Summary by CodeRabbit
  - Added feature A
  - Fixed bug B
Other trailing text not part
"""
    pr = make_pr(mocker, body)
    out = get_rls_notes_code_rabbit(pr.body, LINE_MARKS, CR_REGEX)
    assert out == "  - Added feature A\n  - Fixed bug B\n"


def test_code_rabbit_ignored_group_then_kept_group(issue_record, mocker):
    mocker.patch(
        "release_notes_generator.model.record.issue_record.ActionInputs.get_coderabbit_summary_ignore_groups",
        return_value=["Chore"]
    )
    body = """Header
Summary by CodeRabbit
- **Chore**
  - Internal cleanup
- **Features**
  - Public API v2
  - Faster engine
"""
    pr = make_pr(mocker, body)
    out = get_rls_notes_code_rabbit(pr.body, LINE_MARKS, CR_REGEX)
    # Chore group bullets skipped, Features group kept
    assert out == "  - Public API v2\n  - Faster engine\n"


def test_code_rabbit_non_bullet_terminates(issue_record, mocker):
    mocker.patch("release_notes_generator.model.record.issue_record.ActionInputs.get_coderabbit_summary_ignore_groups", return_value=[])
    body = """Preamble
Summary by CodeRabbit
  - First line
Notes:
  - Should NOT appear (after termination)
"""
    pr = make_pr(mocker, body)
    out = get_rls_notes_code_rabbit(pr.body, LINE_MARKS, CR_REGEX)
    assert out == "  - First line\n"


def test_get_pull_request_numbers(record_with_issue_closed_one_pull_merged):
    assert [124] == record_with_issue_closed_one_pull_merged.get_pull_request_numbers()


def test_get_commit_none(record_with_issue_closed_no_pull):
    assert record_with_issue_closed_no_pull.get_commit(1, "sha") is None


def test_get_pull_request(record_with_issue_closed_no_pull):
    assert record_with_issue_closed_no_pull.get_pull_request(1) is None


def test_register_commit(mock_issue_open_2, mock_pull_merged, mock_commit):
    record = IssueRecord(issue=mock_issue_open_2)
    mock_pull_merged.body = "Release Notes:\n- Fixed bug\n- Improved performance\n\nFixes #123"
    record.register_commit(mock_pull_merged, mock_commit)

    assert 1 == len(record._commits)
    assert 124 in record._pull_requests.keys()
    assert 124 in record._commits.keys()


def test_register_commit_pr_already_registered(mock_issue_open_2, mock_pull_merged, mock_commit):
    record = IssueRecord(issue=mock_issue_open_2)
    mock_pull_merged.body = "Release Notes:\n- Fixed bug\n- Improved performance\n\nFixes #123"
    record.register_pull_request(mock_pull_merged)
    record._commits.pop(124)
    record.register_commit(mock_pull_merged, mock_commit)

    assert 1 == len(record._commits)
    assert 124 in record._pull_requests.keys()
    assert 124 in record._commits.keys()
