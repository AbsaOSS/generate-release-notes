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
from typing import cast

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Commit import Commit

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.record.factory.default_record_factory import DefaultRecordFactory


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
    mock_git_pr1.get_labels.return_value = []

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
    mock_git_pr2.get_labels.return_value = []

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
    mock_git_issue1.get_labels.return_value = []
    mock_git_issue1.repository.full_name = "org/repo"

    mock_git_issue2 = mocker.Mock(spec=Issue)
    mock_git_issue2.id = 2
    mock_git_issue2.number = 2
    mock_git_issue2.title = "Issue 2"
    mock_git_issue2.body = "Body of issue 2"
    mock_git_issue2.state = "closed"
    mock_git_issue2.created_at = datetime.now()
    mock_git_issue2.get_labels.return_value = []
    mock_git_issue2.repository.full_name = "org/repo"

    return mock_git_issue1, mock_git_issue2


def setup_issues_pulls_commits(mocker, mock_repo):
    # Mock GitHub API objects
    mock_git_issue1 = mocker.Mock(spec=Issue)
    mock_git_issue1.id = 1
    mock_git_issue1.number = 1
    mock_git_issue1.title = "Issue 1"
    mock_git_issue1.body = "Body of issue 1"
    mock_git_issue1.state = "open"
    mock_git_issue1.created_at = datetime.now()
    mock_git_issue1.get_labels.return_value = []
    mock_git_issue1.repository.full_name = "org/repo"

    mock_git_issue2 = mocker.Mock(spec=Issue)
    mock_git_issue2.id = 2
    mock_git_issue2.number = 2
    mock_git_issue2.title = "Issue 2"
    mock_git_issue2.body = "Body of issue 2"
    mock_git_issue2.state = "closed"
    mock_git_issue2.created_at = datetime.now()
    mock_git_issue2.get_labels.return_value = []
    mock_git_issue2.repository.full_name = "org/repo"

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
    mock_git_pr1.get_labels.return_value = []

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
    mock_git_pr2.get_labels.return_value = []

    mock_git_commit1 = mocker.Mock(spec=Commit)
    mock_git_commit1.sha = "abc123"
    mock_git_commit1.commit.message = "Commit message 1"
    mock_git_commit1.author.login = "author1"
    mock_git_commit1.repository = mock_repo

    mock_git_commit2 = mocker.Mock(spec=Commit)
    mock_git_commit2.sha = "def456"
    mock_git_commit2.commit.message = "Commit message 2"
    mock_git_commit2.author.login = "author2"
    mock_git_commit2.repository = mock_repo

    return mock_git_issue1, mock_git_issue2, mock_git_pr1, mock_git_pr2, mock_git_commit1, mock_git_commit2

def mock_safe_call_decorator(_rate_limiter):
    def wrapper(fn):
        if fn.__name__ == "get_issues_for_pr":
            return mock_get_issues_for_pr
        return fn
    return wrapper

def mock_get_issues_for_pr(pull_number: int) -> list[str]:
    if pull_number == 101:
        return ['org/repo#1']
    elif pull_number == 102:
        return ['org/repo#2']
    return []

def test_generate_with_issues_and_pulls_and_commits(mocker, mock_repo):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator)
    mock_github_client = mocker.Mock(spec=Github)
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit

    data = MinedData(mock_repo)
    data.issues = [issue1]
    data.pull_requests = [pr1]
    commit3 = mocker.Mock(spec=Commit)
    commit3.sha = "ghi789"
    commit3.repository = mock_repo
    data.commits = [commit1, commit2, commit3]

    records = DefaultRecordFactory(mock_github_client, mock_repo).generate(data)

    # Check if records for issues and PRs were created
    assert len(records) == 3

    assert 'org/repo#1' in records
    assert not records['org/repo#1'].skip

    # Verify the record creation
    assert records['org/repo#1'].__class__ is IssueRecord
    rec_i1 = cast(IssueRecord, records['org/repo#1'])

    # Verify that PRs are registered
    assert 1 == rec_i1.pull_requests_count()
    assert pr1 == rec_i1.get_pull_request(101)

    # Verify that commits are registered
    assert commit1 == rec_i1.get_commit(101, 'abc123')

def test_generate_with_issues_and_pulls_and_commits_with_skip_labels(mocker, mock_repo):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.ActionInputs.get_skip_release_notes_labels", return_value=["skip-release-notes"])
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator)
    mock_github_client = mocker.Mock(spec=Github)
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker, mock_repo)

    # Define mock labels
    mock_label = mocker.Mock()
    mock_label.name = "skip-release-notes"
    issue1.get_labels.return_value = [mock_label]
    pr2.get_labels.return_value = [mock_label]

    commit3 = mocker.Mock(spec=Commit)
    commit3.sha = "ghi789"
    commit3.repository.full_name = "org/repo"

    data = MinedData(mock_repo)
    data.issues = [issue1, issue2]
    data.pull_requests = [pr1, pr2]
    data.commits = [commit1, commit2, commit3]

    records = DefaultRecordFactory(mock_github_client, mock_repo).generate(data)

    # Check if records for issues and PRs were created
    assert len(records) == 3

    assert 'org/repo#1' in records
    assert 'org/repo#2' in records
    assert 'ghi789' in records

    # Verify the record creation
    assert isinstance(records['org/repo#1'], IssueRecord)
    assert isinstance(records['org/repo#2'], IssueRecord)
    assert isinstance(records['ghi789'], CommitRecord)

    assert records['org/repo#1'].skip      # skip label applied to issue as the record was created from issue
    assert not records['org/repo#2'].skip  # skip label is present only on inner PR but record create from issues (leading)

    rec_i1 = cast(IssueRecord, records['org/repo#1'])
    rec_i2 = cast(IssueRecord, records['org/repo#2'])

    # Verify that PRs are registered
    assert 1 == rec_i1.pull_requests_count()
    assert 1 == rec_i2.pull_requests_count()

    assert pr1 == rec_i1.get_pull_request(101)
    assert pr2 == rec_i2.get_pull_request(102)

    # Verify that commits are registered
    assert commit1 == rec_i1.get_commit(101, 'abc123')
    assert commit2 == rec_i2.get_commit(102, 'def456')
    assert commit3 == cast(CommitRecord, records['ghi789']).commit


def test_generate_with_no_commits(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    data = MinedData(mock_repo)
    # pylint: disable=unused-variable
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker, mock_repo)
    data.issues = [issue1]
    data.pull_requests = [pr1]  # PR linked to a non-fetched issues (due to since condition)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit
    mock_repo.get_issue.return_value = issue2

    data.commits = []  # No commits
    mocker.patch("release_notes_generator.record.factory.default_record_factory.get_issues_for_pr", return_value=['org/repo#2'])
    records = DefaultRecordFactory(mock_github_client, mock_repo).generate(data)

    assert 2 == len(records)

    # Verify the record creation
    assert isinstance(records['org/repo#1'], IssueRecord)
    assert isinstance(records['org/repo#2'], IssueRecord)

    rec_issue1 = cast(IssueRecord,records['org/repo#1'])
    rec_issue2 = cast(IssueRecord,records['org/repo#2'])

    # Verify that PRs are registered
    assert 1 == rec_issue1.pull_requests_count()
    assert 1 == rec_issue2.pull_requests_count()

    assert pr1 == rec_issue2.get_pull_request(101)

def test_generate_with_no_commits_with_wrong_issue_number_in_pull_body_mention(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    data = MinedData(mock_repo)
    # pylint: disable=unused-variable
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits(mocker, mock_repo)
    pr1.body = "Closes #2"
    data.issues = [issue1]
    data.pull_requests = [pr1]  # PR linked to a non-fetched issues (due to since condition)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit
    mock_repo.get_issue.return_value = issue2

    data.commits = []  # No commits
    mocker.patch("release_notes_generator.record.factory.default_record_factory.get_issues_for_pr", return_value=['org/repo#2'])
    records = DefaultRecordFactory(mock_github_client, mock_repo).generate(data)

    assert 2 == len(records)

    # Verify the record creation
    assert isinstance(records['org/repo#1'], IssueRecord)
    assert isinstance(records['org/repo#2'], IssueRecord)

    rec_issue1 = cast(IssueRecord, records['org/repo#1'])
    rec_issue2 = cast(IssueRecord, records['org/repo#2'])

    # Verify that PRs are registered
    assert 0 == rec_issue1.pull_requests_count()
    assert 1 == rec_issue2.pull_requests_count()

    assert pr1 == rec_issue2.get_pull_request(101)

def mock_safe_call_decorator_no_issues(_rate_limiter):
    def wrapper(fn):
        if getattr(fn, "__name__", None) == "get_issues_for_pr":
            return mock_get_issues_for_pr_no_issues
        return fn
    return wrapper

def mock_get_issues_for_pr_no_issues(pull_number: int) -> list[str]:
    return []


def test_generate_with_no_issues(mocker, mock_repo, request):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator_no_issues)
    mock_github_client = mocker.Mock(spec=Github)
    data = MinedData(mock_repo)
    pr1, pr2, commit1, commit2 = setup_no_issues_pulls_commits(mocker)
    data.pull_requests = [pr1, pr2]
    data.commits = [commit1, commit2]
    data.issues = []  # No issues

    records = DefaultRecordFactory(mock_github_client, mock_repo).generate(data)

    # Verify the record creation
    assert 2 == len(records)

    assert isinstance(records['org/repo#101'], PullRequestRecord)
    assert isinstance(records['org/repo#102'], PullRequestRecord)

    rec_pr1 = cast(PullRequestRecord, records['org/repo#101'])
    rec_pr2 = cast(PullRequestRecord, records['org/repo#102'])

    # Verify that PRs are registered
    assert pr1 == rec_pr1.pull_request
    assert pr2 == rec_pr2.pull_request

    # Verify that commits are registered
    assert 1 == rec_pr1.commits_count()
    assert 1 == rec_pr2.commits_count()
    assert commit1 == rec_pr1.get_commit('abc123')
    assert commit2 == rec_pr2.get_commit('def456')

def test_generate_with_no_issues_skip_labels(mocker, mock_repo, request):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.ActionInputs.get_skip_release_notes_labels", return_value=["skip-release-notes", "another-skip-label"])
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator_no_issues)
    mock_github_client = mocker.Mock(spec=Github)
    data = MinedData(mock_repo)
    pr1, pr2, commit1, commit2 = setup_no_issues_pulls_commits(mocker)

    # Define mock labels
    mock_label1 = mocker.Mock()
    mock_label1.name = "skip-release-notes"
    mock_label2 = mocker.Mock()
    mock_label2.name = "another-skip-label"
    pr1.get_labels.return_value = [mock_label1]
    pr2.get_labels.return_value = [mock_label2]

    data.pull_requests = [pr1, pr2]
    data.commits = [commit1, commit2]

    data.issues = []  # No issues

    records = DefaultRecordFactory(mock_github_client, mock_repo).generate(data)

    # Verify the record creation
    assert 2 == len(records)

    assert isinstance(records['org/repo#101'], PullRequestRecord)
    assert isinstance(records['org/repo#102'], PullRequestRecord)

    assert records['org/repo#101'].skip
    assert records['org/repo#102'].skip

    rec_pr1 = cast(PullRequestRecord, records['org/repo#101'])
    rec_pr2 = cast(PullRequestRecord, records['org/repo#102'])

    # Verify that PRs are registered
    assert 1 == rec_pr1.commits_count()
    assert 1 == rec_pr2.commits_count()

    assert commit1 == rec_pr1.get_commit('abc123')
    assert commit2 == rec_pr2.get_commit('def456')


def test_generate_with_no_pulls(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    data = MinedData(mock_repo)
    issue1, issue2 = setup_issues_no_pulls_no_commits(mocker)
    data.issues = [issue1, issue2]
    data.pull_requests = []  # No pull requests
    data.commits = []  # No commits
    records = DefaultRecordFactory(mock_github_client, mock_repo).generate(data)

    # Verify the record creation
    assert 2 == len(records)
    assert isinstance(records['org/repo#1'], IssueRecord)
    assert isinstance(records['org/repo#2'], IssueRecord)

    # Verify that PRs are registered
    assert 0 == cast(IssueRecord, records['org/repo#1']).pull_requests_count()
    assert 0 == cast(IssueRecord, records['org/repo#2']).pull_requests_count()


def mock_safe_call_decorator_wrong_issue_number(_rate_limiter):
    def wrapper(fn):
        if fn.__name__ == "get_issues_for_pr":
            return mock_get_issues_for_pr_with_wrong_issue_number
        return fn
    return wrapper

def mock_get_issues_for_pr_with_wrong_issue_number(pull_number: int) -> list[int]:
    if pull_number == 101:
        return []
    elif pull_number == 102:
        return [2]
    return []
