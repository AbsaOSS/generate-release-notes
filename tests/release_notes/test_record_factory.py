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

import time

from datetime import datetime

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Commit import Commit

from release_notes_generator.model.record import Record
from release_notes_generator.record.record_factory import RecordFactory
from tests.conftest import MockLabel


def setup_no_issues_pulls_commits(mocker):
    mock_git_pr1 = mocker.Mock(spec=PullRequest)
    mock_git_pr1.id = 101
    mock_git_pr1.number = 101
    mock_git_pr1.title = "PR 101"
    mock_git_pr1.body = "No linked issue"
    mock_git_pr1.state = "closed"
    mock_git_pr1.created_at = datetime.now()
    mock_git_pr1.updated_at = datetime.now()
    mock_git_pr1.closed_at = None
    mock_git_pr1.merged_at = None
    mock_git_pr1.assignee = None
    mock_git_pr1.merge_commit_sha = "abc123"
    mock_git_pr1.labels = []

    mock_git_pr2 = mocker.Mock(spec=PullRequest)
    mock_git_pr2.id = 102
    mock_git_pr2.number = 102
    mock_git_pr2.title = "PR 102"
    mock_git_pr2.body = "No linked issue"
    mock_git_pr2.state = "closed"
    mock_git_pr2.created_at = datetime.now()
    mock_git_pr2.updated_at = datetime.now()
    mock_git_pr2.closed_at = None
    mock_git_pr2.merged_at = None
    mock_git_pr2.assignee = None
    mock_git_pr2.merge_commit_sha = "def456"
    mock_git_pr2.labels = []

    mock_git_commit1 = mocker.Mock(spec=Commit)
    mock_git_commit1.sha = "abc123"
    mock_git_commit1.commit.message = "Commit message 1"
    mock_git_commit1.author.login = "author1"

    mock_git_commit2 = mocker.Mock(spec=Commit)
    mock_git_commit2.sha = "def456"
    mock_git_commit2.commit.message = "Commit message 2"
    mock_git_commit2.author.login = "author2"

    return mock_git_pr1, mock_git_pr2, mock_git_commit1, mock_git_commit2


def setup_issues_no_pulls_no_commits(mocker):
    # Mock GitHub API objects
    mock_git_issue1 = mocker.Mock(spec=Issue)
    mock_git_issue1.id = 1
    mock_git_issue1.number = 1
    mock_git_issue1.title = "Issue 1"
    mock_git_issue1.body = "Body of issue 1"
    mock_git_issue1.state = "open"
    mock_git_issue1.created_at = datetime.now()
    mock_git_issue1.labels = []

    mock_git_issue2 = mocker.Mock(spec=Issue)
    mock_git_issue2.id = 2
    mock_git_issue2.number = 2
    mock_git_issue2.title = "Issue 2"
    mock_git_issue2.body = "Body of issue 2"
    mock_git_issue2.state = "closed"
    mock_git_issue2.created_at = datetime.now()
    mock_git_issue2.labels = []

    return mock_git_issue1, mock_git_issue2


def setup_issues_pulls_commits(mocker):
    # Mock GitHub API objects
    mock_git_issue1 = mocker.Mock(spec=Issue)
    mock_git_issue1.id = 1
    mock_git_issue1.number = 1
    mock_git_issue1.title = "Issue 1"
    mock_git_issue1.body = "Body of issue 1"
    mock_git_issue1.state = "open"
    mock_git_issue1.created_at = datetime.now()
    mock_git_issue1.labels = []

    mock_git_issue2 = mocker.Mock(spec=Issue)
    mock_git_issue2.id = 2
    mock_git_issue2.number = 2
    mock_git_issue2.title = "Issue 2"
    mock_git_issue2.body = "Body of issue 2"
    mock_git_issue2.state = "closed"
    mock_git_issue2.created_at = datetime.now()
    mock_git_issue2.labels = []

    mock_git_pr1 = mocker.Mock(spec=PullRequest)
    mock_git_pr1.id = 101
    mock_git_pr1.number = 101
    mock_git_pr1.title = "PR 101"
    mock_git_pr1.body = "Closes #1"
    mock_git_pr1.state = "closed"
    mock_git_pr1.created_at = datetime.now()
    mock_git_pr1.updated_at = datetime.now()
    mock_git_pr1.closed_at = None
    mock_git_pr1.merged_at = None
    mock_git_pr1.assignee = None
    mock_git_pr1.merge_commit_sha = "abc123"
    mock_git_pr1.labels = []

    mock_git_pr2 = mocker.Mock(spec=PullRequest)
    mock_git_pr2.id = 102
    mock_git_pr2.number = 102
    mock_git_pr2.title = "PR 102"
    mock_git_pr2.body = "Closes #2"
    mock_git_pr2.state = "closed"
    mock_git_pr2.created_at = datetime.now()
    mock_git_pr2.updated_at = datetime.now()
    mock_git_pr2.closed_at = None
    mock_git_pr2.merged_at = None
    mock_git_pr2.assignee = None
    mock_git_pr2.merge_commit_sha = "def456"
    mock_git_pr2.labels = []

    mock_git_commit1 = mocker.Mock(spec=Commit)
    mock_git_commit1.sha = "abc123"
    mock_git_commit1.commit.message = "Commit message 1"
    mock_git_commit1.author.login = "author1"

    mock_git_commit2 = mocker.Mock(spec=Commit)
    mock_git_commit2.sha = "def456"
    mock_git_commit2.commit.message = "Commit message 2"
    mock_git_commit2.author.login = "author2"

    return mock_git_issue1, mock_git_issue2, mock_git_pr1, mock_git_pr2, mock_git_commit1, mock_git_commit2


def test_generate_with_issues_and_pulls_and_commits(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker)
    issues = [issue1, issue2]
    pulls = [pr1, pr2]
    commit3 = mocker.Mock(spec=Commit)
    commit3.sha = "ghi789"
    commits = [commit1, commit2, commit3]

    records = RecordFactory.generate(mock_github_client, mock_repo, issues, pulls, commits)

    # Check if records for issues and PRs were created
    assert 1 in records
    assert 2 in records

    assert not records[1].skip
    assert not records[2].skip

    # Verify the record creation
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)

    # Verify that PRs are registered
    assert 1 == records[1].pulls_count
    assert 1 == records[2].pulls_count

    assert pr1 == records[1].pull_request(0)
    assert pr2 == records[2].pull_request(0)

    # Verify that commits are registered
    assert 1 == records[1].pull_request_commit_count(101)
    assert 1 == records[2].pull_request_commit_count(102)


def test_generate_with_issues_and_pulls_and_commits_with_skip_labels(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker)
    mock_label = mocker.Mock(spec=MockLabel)
    mock_label.name = "skip-release-notes"
    issue1.labels = [mock_label]
    pr2.labels = [mock_label]
    issues = [issue1, issue2]
    pulls = [pr1, pr2]
    commit3 = mocker.Mock(spec=Commit)
    commit3.sha = "ghi789"
    commits = [commit1, commit2, commit3]
    mocker.patch("release_notes_generator.builder.ActionInputs.get_skip_release_notes_labels", return_value=["skip-release-notes"])

    records = RecordFactory.generate(mock_github_client, mock_repo, issues, pulls, commits)

    # Check if records for issues and PRs were created
    assert 1 in records
    assert 2 in records

    # Verify the record creation
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)

    assert records[1].skip      # skip label appied to issue as the record was created from issue
    assert not records[2].skip  # skip label is present only on inner PR but record create from issues (leading)

    # Verify that PRs are registered
    # assert 1 == records[1].pulls_count
    assert 1 == records[2].pulls_count

    # assert pr1 == records[1].pull_request(0)
    assert pr2 == records[2].pull_request(0)

    # Verify that commits are registered
    # assert 1 == records[1].pull_request_commit_count(101)
    assert 1 == records[2].pull_request_commit_count(102)



def test_generate_with_no_commits(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    # pylint: disable=unused-variable
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker)
    issues = [issue1]
    pulls = [pr1, pr2]  # PR linked to a non-fetched issues (due to since condition)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 10
    mock_rate_limit.core.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit
    mock_repo.get_issue.return_value = issue2

    records = RecordFactory.generate(mock_github_client, mock_repo, issues, pulls, [])

    # Verify the record creation
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)

    # Verify that PRs are registered
    assert 1 == records[1].pulls_count
    assert 1 == records[2].pulls_count

    assert pr1 == records[1].pull_request(0)
    assert pr2 == records[2].pull_request(0)

    # Verify that commits not present
    assert 0 == records[1].pull_request_commit_count(1)
    assert 0 == records[2].pull_request_commit_count(2)


def test_generate_with_no_issues(mocker, request):
    mock_github_client = mocker.Mock(spec=Github)
    pr1, pr2, commit1, commit2 = setup_no_issues_pulls_commits(mocker)
    pulls = [pr1, pr2]
    commits = [commit1, commit2]

    records = RecordFactory.generate(mock_github_client, request.getfixturevalue("mock_repo"), [], pulls, commits)

    # Verify the record creation
    assert isinstance(records[101], Record)
    assert isinstance(records[102], Record)

    # Verify that PRs are registered
    assert 1 == records[101].pulls_count
    assert 1 == records[102].pulls_count

    assert pr1 == records[101].pull_request(0)
    assert pr2 == records[102].pull_request(0)

    # Verify that commits are registered
    assert 1 == records[101].pull_request_commit_count(101)
    assert 1 == records[102].pull_request_commit_count(102)

def test_generate_with_no_issues_skip_labels(mocker, request):
    mock_github_client = mocker.Mock(spec=Github)
    pr1, pr2, commit1, commit2 = setup_no_issues_pulls_commits(mocker)
    mock_label1 = mocker.Mock(spec=MockLabel)
    mock_label1.name = "skip-release-notes"
    pr1.labels = [mock_label1]
    mock_label2 = mocker.Mock(spec=MockLabel)
    mock_label2.name = "another-skip-label"
    pr2.labels = [mock_label2]
    pulls = [pr1, pr2]
    commits = [commit1, commit2]
    mocker.patch("release_notes_generator.builder.ActionInputs.get_skip_release_notes_labels", return_value=["skip-release-notes", "another-skip-label"])

    records = RecordFactory.generate(mock_github_client, request.getfixturevalue("mock_repo"), [], pulls, commits)

    # Verify the record creation
    assert isinstance(records[101], Record)
    assert isinstance(records[102], Record)

    assert records[101].skip
    assert records[102].skip

    # Verify that PRs are registered
    assert 1 == records[101].pulls_count
    assert 1 == records[102].pulls_count

    assert pr1 == records[101].pull_request(0)
    assert pr2 == records[102].pull_request(0)

    # Verify that commits are registered
    assert 1 == records[101].pull_request_commit_count(101)
    assert 1 == records[102].pull_request_commit_count(102)


def test_generate_with_no_pulls(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    issue1, issue2 = setup_issues_no_pulls_no_commits(mocker)
    issues = [issue1, issue2]

    records = RecordFactory.generate(mock_github_client, mock_repo, issues, [], [])

    # Verify the record creation
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)

    # Verify that PRs are registered
    assert 0 == records[1].pulls_count
    assert 0 == records[2].pulls_count


def test_generate_with_wrong_issue_number_in_pull_body_mention(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker)
    pr1.body = "Closes #100"
    issues = [issue1, issue2]
    pulls = [pr1, pr2]
    commits = [commit1, commit2]

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 10
    mock_rate_limit.core.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit
    mock_repo.get_issue.return_value = None

    records = RecordFactory.generate(mock_github_client, mock_repo, issues, pulls, commits)

    # Verify the record creation
    assert 3 == len(records)
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)
    assert isinstance(records[101], Record)

    # Verify that PRs are registered
    assert 0 == records[1].pulls_count
    assert 1 == records[2].pulls_count
    assert 1 == records[101].pulls_count
