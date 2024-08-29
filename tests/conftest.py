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

import pytest

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Rate import Rate
from github.RateLimit import RateLimit
from github.Repository import Repository

from release_notes_generator.model.service_chapters import ServiceChapters
from release_notes_generator.model.record import Record
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.utils.constants import Constants
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter


# Test classes

# pylint: disable=too-few-public-methods
class MockLabel:
    def __init__(self, name):
        self.name = name


# Fixtures for Custom Chapters
@pytest.fixture
def custom_chapters():
    chapters = CustomChapters()
    chapters.chapters = {
        'Chapter 1': Chapter('Chapter 1', ['bug', 'enhancement']),
        'Chapter 2': Chapter('Chapter 2', ['feature'])
    }
    return chapters


@pytest.fixture
def custom_chapters_not_print_empty_chapters():
    chapters = CustomChapters()
    chapters.chapters = {
        'Chapter 1': Chapter('Chapter 1 🛠', ['bug', 'enhancement']),
        'Chapter 2': Chapter('Chapter 2 🎉', ['feature'])
    }
    chapters.print_empty_chapters = False
    return chapters


# Fixtures for Service Chapters
@pytest.fixture
def service_chapters():
    return ServiceChapters(
        sort_ascending=True,
        print_empty_chapters=True,
        user_defined_labels=['bug', 'enhancement']
    )


# Fixtures for GitHub Repository
@pytest.fixture
def mock_repo(mocker):
    repo = mocker.Mock(spec=Repository)
    repo.full_name = 'org/repo'
    return repo


# Fixtures for GitHub Release(s)
@pytest.fixture
def mock_git_release(mocker):
    release = mocker.Mock()
    release.tag_name = "v1.0.0"
    return release


@pytest.fixture
def rate_limiter(mocker, request):
    mock_github_client = mocker.Mock(spec=Github)
    mock_github_client.get_rate_limit.return_value = request.getfixturevalue('mock_rate_limiter')
    return GithubRateLimiter(mock_github_client)


@pytest.fixture
def mock_rate_limiter(mocker):
    mock_rate = mocker.Mock(spec=Rate)
    mock_rate.timestamp = mocker.Mock(return_value=time.time() + 3600)

    mock_core = mocker.Mock(spec=RateLimit)
    mock_core.reset = mock_rate

    mock = mocker.Mock(spec=GithubRateLimiter)
    mock.core = mock_core
    mock.core.remaining = 10

    return mock


# Fixtures for GitHub Issue(s)
@pytest.fixture
def mock_issue_open(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = Constants.ISSUE_STATE_OPEN
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = 'label2'
    issue.labels = [label1, label2]
    issue.number = 122
    issue.title = "I1 open"
    issue.state_reason = None
    return issue


@pytest.fixture
def mock_issue_open_2(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = Constants.ISSUE_STATE_OPEN
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = 'label2'
    issue.labels = [label1, label2]
    issue.number = 123
    issue.title = "I2 open"
    issue.state_reason = None
    return issue


@pytest.fixture
def mock_issue_closed(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = Constants.ISSUE_STATE_CLOSED
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = 'label2'
    issue.labels = [label1, label2]
    issue.title = 'Fix the bug'
    issue.number = 121
    return issue


@pytest.fixture
def mock_issue_closed_i1_bug(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = Constants.ISSUE_STATE_CLOSED
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = 'bug'
    issue.labels = [label1, label2]
    issue.title = 'I1+bug'
    issue.number = 122
    return issue


# Fixtures for GitHub Pull Request(s)
@pytest.fixture
def mock_pull_closed(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = "Release notes:\n- Fixed bug\n- Improved performance\n"
    pull.url = "http://example.com/pull/123"
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 123
    pull.merge_commit_sha = 'merge_commit_sha'
    pull.title = 'Fixed bug'
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = datetime.now()
    return pull


@pytest.fixture
def mock_pull_closed_with_rls_notes_101(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = "Release notes:\n- PR 101 1st release note\n- PR 101 2nd release note\n"
    pull.url = "http://example.com/pull/101"
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 101
    pull.merge_commit_sha = 'merge_commit_sha'
    pull.title = 'Fixed bug'
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = datetime.now()
    return pull


@pytest.fixture
def mock_pull_closed_with_rls_notes_102(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = "Release notes:\n- PR 102 1st release note\n- PR 102 2nd release note\n"
    pull.url = "http://example.com/pull/102"
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 102
    pull.merge_commit_sha = 'merge_commit_sha'
    pull.title = 'Fixed bug'
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = datetime.now()
    return pull


@pytest.fixture
def mock_pull_merged_with_rls_notes_101(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = "Closes #122\n\nRelease notes:\n- PR 101 1st release note\n- PR 101 2nd release note\n"
    pull.url = "http://example.com/pull/101"
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 101
    pull.merge_commit_sha = 'merge_commit_sha'
    pull.title = 'Fixed bug'
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = datetime.now()
    pull.closed_at = datetime.now()
    return pull


@pytest.fixture
def mock_pull_merged_with_rls_notes_102(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = "Closes #123\n\nRelease notes:\n- PR 102 1st release note\n- PR 102 2nd release note\n"
    pull.url = "http://example.com/pull/102"
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 102
    pull.merge_commit_sha = 'merge_commit_sha'
    pull.title = 'Fixed bug'
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = datetime.now()
    pull.closed_at = datetime.now()
    return pull


@pytest.fixture
def mock_pull_merged(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = "Release notes:\n- Fixed bug\n- Improved performance\n"
    pull.url = "http://example.com/pull/123"
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 123
    pull.merge_commit_sha = 'merge_commit_sha'
    pull.title = 'Fixed bug'
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = datetime.now()
    pull.closed_at = datetime.now()
    return pull


@pytest.fixture
def mock_pull_open(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_OPEN
    pull.body = "Release notes:\n- Fixed bug\n- Improved performance\n"
    pull.url = "http://example.com/pull/123"
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 123
    pull.merge_commit_sha = None
    pull.title = 'Fix bug'
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = None
    return pull


@pytest.fixture
def mock_pull_no_rls_notes(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = None
    label1 = mocker.Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 123
    pull.title = 'Fixed bug'
    return pull


# Fixtures for GitHub Commit(s)
@pytest.fixture
def mock_commit(mocker):
    commit = mocker.Mock()
    commit.author = 'author'
    commit.sha = 'merge_commit_sha'
    return commit


# Fixtures for Record(s)
@pytest.fixture
def record_with_issue_open_no_pull(request):
    mock_repo_fixture = request.getfixturevalue('mock_repo')
    return Record(repo=mock_repo_fixture,
                  issue=request.getfixturevalue('mock_issue_open'))


@pytest.fixture
def record_with_issue_closed_no_pull(request):
    rec = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')),
                 issue=request.getfixturevalue('mock_issue_closed'))
    mock_repo_fixture.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_issue_closed_one_pull(request):
    rec = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')),
                 issue=request.getfixturevalue('mock_issue_closed'))
    rec.register_pull_request(request.getfixturevalue('mock_pull_closed'))
    mock_repo_fixture.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_issue_closed_one_pull_merged(request):
    rec = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')),
                 issue=request.getfixturevalue('mock_issue_closed_i1_bug'))
    rec.register_pull_request(request.getfixturevalue('mock_pull_merged'))
    mock_repo_fixture.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_issue_closed_two_pulls(request):
    rec = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')),
                 issue=request.getfixturevalue('mock_issue_closed_i1_bug'))
    rec.register_pull_request(request.getfixturevalue('mock_pull_closed_with_rls_notes_101'))
    rec.register_pull_request(request.getfixturevalue('mock_pull_closed_with_rls_notes_102'))
    mock_repo_fixture.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_issue_open_one_pull_closed(request):
    rec = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')),
                 issue=request.getfixturevalue('mock_issue_open'))
    rec.register_pull_request(request.getfixturevalue('mock_pull_closed'))
    mock_repo_fixture.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_issue_open_two_pulls_closed(request):
    rec = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')),
                 issue=request.getfixturevalue('mock_issue_open'))
    rec.register_pull_request(request.getfixturevalue('mock_pull_closed_with_rls_notes_101'))
    rec.register_pull_request(request.getfixturevalue('mock_pull_closed_with_rls_notes_102'))
    mock_repo_fixture.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_two_issue_open_two_pulls_closed(request):
    rec1 = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')))
    rec1.register_pull_request(request.getfixturevalue('mock_pull_merged_with_rls_notes_101'))

    rec2 = Record(repo=mock_repo_fixture)
    rec2.register_pull_request(request.getfixturevalue('mock_pull_merged_with_rls_notes_102'))
    mock_repo_fixture.full_name = 'org/repo'

    records = {}
    records[rec1.number] = rec1
    records[rec2.number] = rec2

    return records


@pytest.fixture
def record_with_issue_closed_one_pull_no_rls_notes(request):
    rec = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')),
                 issue=request.getfixturevalue('mock_issue_closed'))
    rec.register_pull_request(mock_pull_closed_fixture := request.getfixturevalue('mock_pull_no_rls_notes'))
    mock_pull_closed_fixture.body = "Fixed bug"
    mock_repo_fixture.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_no_issue_one_pull_merged(request):
    record = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')))
    mock_repo_fixture.full_name = 'org/repo'
    record.register_pull_request(request.getfixturevalue('mock_pull_merged'))
    record.register_commit(request.getfixturevalue('mock_commit'))
    return record


@pytest.fixture
def record_with_no_issue_one_pull_open(request):
    record = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')))
    mock_repo_fixture.full_name = 'org/repo'
    record.register_pull_request(request.getfixturevalue('mock_pull_open'))
    record.register_commit(request.getfixturevalue('mock_commit'))
    return record


@pytest.fixture
def record_with_no_issue_one_pull_merged_with_issue_mentioned(request):
    record = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')))
    mock_repo_fixture.full_name = 'org/repo'
    mock_pull_merged_fixture = request.getfixturevalue('mock_pull_merged')
    mock_pull_merged_fixture.body = "Release notes:\n- Fixed bug\n- Improved performance\n\nFixes #123"
    record.register_pull_request(mock_pull_merged_fixture)
    record.register_commit(request.getfixturevalue('mock_commit'))
    return record


@pytest.fixture
def record_with_no_issue_one_pull_closed(request):
    record = Record(repo=(mock_repo_fixture := request.getfixturevalue('mock_repo')))
    mock_repo_fixture.full_name = 'org/repo'
    mock_repo_fixture.draft = False
    record.register_pull_request(request.getfixturevalue('mock_pull_closed'))
    record.register_commit(request.getfixturevalue('mock_commit'))
    return record


@pytest.fixture
def record_with_no_issue_one_pull_closed_no_rls_notes(request):
    record = Record(repo=request.getfixturevalue('mock_repo'))
    record.register_pull_request(request.getfixturevalue('mock_pull_no_rls_notes'))
    return record
