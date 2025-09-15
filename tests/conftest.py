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

from datetime import datetime, timedelta

import pytest

from github import Github, IssueType
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Rate import Rate
from github.Repository import Repository

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.chapters.service_chapters import ServiceChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.chapters.custom_chapters import CustomChapters
from release_notes_generator.model.sub_issue_record import SubIssueRecord
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter


# Test classes


class MockLabel:
    def __init__(self, name):
        self.name = name


# Fixtures for Custom Chapters
@pytest.fixture
def custom_chapters():
    chapters = CustomChapters()
    chapters.chapters = {
        "Chapter 1": Chapter("Chapter 1", ["bug", "enhancement"]),
        "Chapter 2": Chapter("Chapter 2", ["feature"]),
    }
    return chapters


@pytest.fixture
def custom_chapters_not_print_empty_chapters():
    chapters = CustomChapters()
    chapters.chapters = {
        "Epics": Chapter("Epics", ["epic"]),
        "Chapter 1": Chapter("Chapter 1 🛠", ["bug", "enhancement"]),
        "Chapter 2": Chapter("Chapter 2 🎉", ["feature"]),
    }
    chapters.print_empty_chapters = False
    return chapters


# Fixtures for Service Chapters
@pytest.fixture
def service_chapters():
    return ServiceChapters(sort_ascending=True, print_empty_chapters=True, user_defined_labels=["bug", "enhancement"])


# Fixtures for GitHub Repository
@pytest.fixture
def mock_repo(mocker):
    repo = mocker.Mock(spec=Repository)
    repo.full_name = "org/repo"
    return repo


# Fixtures for GitHub Release(s)
@pytest.fixture
def mock_git_release(mocker):
    release = mocker.Mock(spec=GitRelease)
    release.tag_name = "v1.0.0"
    return release


@pytest.fixture
def mock_git_releases(mocker):
    release_1 = mocker.Mock(spec=GitRelease)
    release_1.tag_name = "v1.0.0"
    release_1.draft = False
    release_1.prerelease = False
    release_2 = mocker.Mock(spec=GitRelease)
    release_2.tag_name = "v2.0.0"
    release_2.draft = False
    release_2.prerelease = False
    return [release_1, release_2]


@pytest.fixture
def rate_limiter(mocker, request):
    mock_github_client = mocker.Mock(spec=Github)
    mock_github_client.get_rate_limit.return_value = request.getfixturevalue("mock_rate_limiter")
    return GithubRateLimiter(mock_github_client)


@pytest.fixture
def mock_rate_limiter(mocker):
    mock_rate = mocker.Mock(spec=Rate)
    mock_rate.reset = datetime.now() + timedelta(hours=1)

    mock = mocker.Mock(spec=GithubRateLimiter)
    mock.rate = mock_rate
    mock.rate.remaining = 10

    return mock


# Fixtures for GitHub Issue(s)
@pytest.fixture
def mock_issue_open(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_OPEN
    issue.number = 122
    issue.title = "I1 open"
    issue.state_reason = None
    issue.body = "I1 open"

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "label2"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_issue_open_2(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_OPEN
    issue.number = 123
    issue.title = "I2 open"
    issue.state_reason = None
    issue.body = "I2 open"

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "label2"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_issue_closed(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_CLOSED
    issue.title = "Fix the bug"
    issue.number = 121
    issue.body = "Some issue body text"

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "label2"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_issue_closed_i1_bug(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_CLOSED
    issue.title = "I1+bug"
    issue.number = 122
    issue.body = "Some issue body text\nRelease Notes:\n- Fixed bug\n- Improved performance\n+ More nice code\n  * Awesome architecture"

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "bug"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_issue_closed_i1_bug_and_skip(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_CLOSED
    issue.title = "I1+bug"
    issue.number = 122

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "skip-release-notes"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "bug"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_open_hierarchy_issue_epic(mocker):
    issue_type = mocker.Mock(spec=IssueType)
    issue_type.name = "Epic"

    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_OPEN
    issue.number = 200
    issue.title = "HI200 open"
    issue.state_reason = None
    issue.body = "I200 open/nRelease Notes:\n- Epic level release note"
    issue.type = issue_type
    issue.created_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "label2"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_open_hierarchy_issue_feature(mocker):
    issue_type = mocker.Mock(spec=IssueType)
    issue_type.name = "Feature"

    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_OPEN
    issue.number = 201
    issue.title = "HI201 open"
    issue.state_reason = None
    issue.body = "HI201 open/nRelease Notes:\n- Feature level release note"
    issue.type = issue_type
    issue.created_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "label3"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_closed_issue_type_task(mocker):
    issue_type = mocker.Mock(spec=IssueType)
    issue_type.name = "Task"

    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_CLOSED
    issue.title = "Do this task"
    issue.number = 202
    issue.body = "Some issue body text"
    issue.type = issue_type
    issue.created_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "label2"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_closed_issue_type_none(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_CLOSED
    issue.title = "Do this issue"
    issue.number = 204
    issue.body = "Some sub issue body text"
    issue.type = None
    issue.created_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "label2"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_closed_issue_type_bug(mocker):
    issue_type = mocker.Mock(spec=IssueType)
    issue_type.name = "Bug"

    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_CLOSED
    issue.title = "Fix the bug"
    issue.number = 203
    issue.body = "Some issue body text\nRelease Notes:\n- Fixed bug\n- Improved performance\n+ More nice code\n  * Awesome architecture"
    issue.type = issue_type
    issue.created_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "bug"
    issue.get_labels.return_value = [label1, label2]

    return issue


# Fixtures for GitHub Pull Request(s)
@pytest.fixture
def mock_pull_closed(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = "Release Notes:\n- Fixed bug\n- Improved performance\n+ More nice code\n  * Awesome architecture"
    pull.url = "http://example.com/pull/123"
    pull.number = 123
    pull.merge_commit_sha = "merge_commit_sha"
    pull.title = "Fixed bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


@pytest.fixture
def mock_pull_closed_with_skip_label(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = "Release Notes:\n- Fixed bug\n- Improved performance\n+ More nice code\n  * Awesome architecture"
    pull.url = "http://example.com/pull/123"
    pull.number = 123
    pull.merge_commit_sha = "merge_commit_sha"
    pull.title = "Fixed bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "skip-release-notes"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "another-skip-label"
    pull.get_labels.return_value = [label1, label2]

    return pull


@pytest.fixture
def mock_pull_closed_with_rls_notes_101(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = "Release Notes:\n- PR 101 1st release note\n- PR 101 2nd release note\n"
    pull.url = "http://example.com/pull/101"
    pull.number = 101
    pull.merge_commit_sha = "merge_commit_sha"
    pull.title = "Fixed bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


@pytest.fixture
def mock_pull_closed_with_rls_notes_102(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = "Release Notes:\n- PR 102 1st release note\n- PR 102 2nd release note\n"
    pull.url = "http://example.com/pull/102"
    pull.number = 102
    pull.merge_commit_sha = "merge_commit_sha"
    pull.title = "Fixed bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


@pytest.fixture
def mock_pull_merged_with_rls_notes_101(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = "Closes #122\n\nRelease Notes:\n- PR 101 1st release note\n- PR 101 2nd release note\n"
    pull.url = "http://example.com/pull/101"
    pull.number = 101
    pull.merge_commit_sha = "merge_commit_sha"
    pull.title = "Fixed bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = datetime.now()
    pull.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


@pytest.fixture
def mock_pull_merged_with_rls_notes_102(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = "Closes #123\n\nRelease Notes:\n- PR 102 1st release note\n- PR 102 2nd release note\n"
    pull.url = "http://example.com/pull/102"
    pull.number = 102
    pull.merge_commit_sha = "merge_commit_sha"
    pull.title = "Fixed bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = datetime.now()
    pull.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


@pytest.fixture
def mock_pull_merged(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = "Release Notes:\n- Fixed bug\n- Improved performance\n"
    pull.url = "http://example.com/pull/123"
    pull.number = 123
    pull.merge_commit_sha = "merge_commit_sha"
    pull.title = "Fixed bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = datetime.now()
    pull.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


@pytest.fixture
def mock_pull_open(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_OPEN
    pull.body = "Release Notes:\n- Fixed bug\n- Improved performance\n"
    pull.url = "http://example.com/pull/123"
    pull.number = 123
    pull.merge_commit_sha = None
    pull.title = "Fix bug"
    pull.created_at = datetime.now()
    pull.updated_at = datetime.now()
    pull.merged_at = None
    pull.closed_at = None

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


@pytest.fixture
def mock_pull_no_rls_notes(mocker):
    pull = mocker.Mock(spec=PullRequest)
    pull.state = PullRequestRecord.PR_STATE_CLOSED
    pull.body = None
    pull.number = 123
    pull.title = "Fixed bug"

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "label1"
    pull.get_labels.return_value = [label1]

    return pull


# Fixtures for GitHub Commit(s)
@pytest.fixture
def mock_commit(mocker):
    commit = mocker.Mock()
    commit.author.login = "author"
    commit.sha = "merge_commit_sha"
    commit.commit.message = "Fixed bug"
    return commit

# Fixtures for Record(s)
@pytest.fixture
def record_with_issue_open_no_pull(request):
    return IssueRecord(issue=request.getfixturevalue("mock_issue_open"))

@pytest.fixture
def record_with_issue_closed_no_pull(request):
    return IssueRecord(issue=request.getfixturevalue("mock_issue_closed"))

@pytest.fixture
def record_with_pr_only(request):
    return PullRequestRecord(pull=request.getfixturevalue("mock_pull_merged_with_rls_notes_101"))

@pytest.fixture
def record_with_direct_commit(request):
    return CommitRecord(commit=request.getfixturevalue("mock_commit"))

@pytest.fixture
def record_with_issue_closed_one_pull(request):
    rec = IssueRecord(issue=request.getfixturevalue("mock_issue_closed"))
    rec.register_pull_request(request.getfixturevalue("mock_pull_closed"))
    return rec


@pytest.fixture
def record_with_issue_closed_one_pull_merged(request):
    rec = IssueRecord(issue=request.getfixturevalue("mock_issue_closed_i1_bug"))
    rec.register_pull_request(request.getfixturevalue("mock_pull_merged"))
    return rec


@pytest.fixture
def record_with_issue_closed_one_pull_merged_skip(request):
    rec = IssueRecord(issue=request.getfixturevalue("mock_issue_closed_i1_bug_and_skip"), skip=True)
    rec.register_pull_request(request.getfixturevalue("mock_pull_merged"))
    return rec


@pytest.fixture
def record_with_issue_closed_two_pulls(request):
    rec = IssueRecord(issue=request.getfixturevalue("mock_issue_closed_i1_bug"))        # TODO - renamed from mock_issue_closed_i2_bug
    rec.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_101"))
    rec.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_102"))
    return rec

@pytest.fixture
def record_with_hierarchy_issues(request):
    rec_epic_issue = HierarchyIssueRecord(issue=request.getfixturevalue("mock_open_hierarchy_issue_epic"))     # nr:200
    rec_epic_issue._labels = ["epic"]  # override labels to have epic label
    rec_feature_issue = HierarchyIssueRecord(request.getfixturevalue("mock_open_hierarchy_issue_feature"))    # nr:201
    rec_feature_issue.level = 1
    rec_epic_issue.sub_hierarchy_issues[rec_feature_issue.issue.number] = rec_feature_issue

    rec_task_issue = SubIssueRecord(request.getfixturevalue("mock_closed_issue_type_task")) # nr:202
    rec_feature_issue.sub_issues[rec_task_issue.issue.number] = rec_task_issue

    # add sub_issue
    rec_sub_issue_no_type = SubIssueRecord(request.getfixturevalue("mock_closed_issue_type_none")) # nr:204
    rec_feature_issue.sub_issues[rec_sub_issue_no_type.issue.number] = rec_sub_issue_no_type

    # add pr to sub_issue
    sub_issue_merged_pr = request.getfixturevalue("mock_pull_merged_with_rls_notes_102")  # nr:205
    sub_issue_merged_pr.number = 205   # simulate PR closing sub-issue nr:204
    sub_issue_merged_pr.body = "Closes #204\n\nRelease Notes:\n- Sub issue 204 closed by merged PR"
    sub_issue_merged_pr.title = "Sub issue 204 closed by merged PR"
    rec_sub_issue_no_type.register_pull_request(sub_issue_merged_pr)

    rec_bug_issue = SubIssueRecord(request.getfixturevalue("mock_closed_issue_type_bug"))   # nr:203
    rec_feature_issue.sub_issues[rec_bug_issue.issue.number] = rec_bug_issue

    # not description keyword used - registration simulate API way (relation)
    rec_task_issue.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_101"))
    rec_bug_issue.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_102"))

    return rec_epic_issue


@pytest.fixture
def record_with_issue_open_one_pull_closed(request):
    rec = IssueRecord(issue=request.getfixturevalue("mock_issue_open"))
    rec.register_pull_request(request.getfixturevalue("mock_pull_closed"))
    return rec


@pytest.fixture
def record_with_issue_open_two_pulls_closed(request):
    rec = IssueRecord(issue=request.getfixturevalue("mock_issue_open"))
    rec.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_101"))
    rec.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_102"))
    return rec


@pytest.fixture
def record_with_two_issue_open_two_pulls_closed(request):
    rec_1 = IssueRecord(issue=request.getfixturevalue("mock_issue_open"))
    rec_1.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_101"))
    rec_2 = IssueRecord(issue=request.getfixturevalue("mock_issue_open_2"))
    rec_2.register_pull_request(request.getfixturevalue("mock_pull_closed_with_rls_notes_102"))

    records = dict()
    records[rec_1.record_id] = rec_1
    records[rec_2.record_id] = rec_2

    return records


@pytest.fixture
def pull_request_record_no_rls_notes(request):
    rec = IssueRecord(issue=request.getfixturevalue("mock_issue_closed"))
    rec.register_pull_request(mock_pull_closed_fixture := request.getfixturevalue("mock_pull_no_rls_notes"))
    mock_pull_closed_fixture.body = "Fixed bug"
    return rec


@pytest.fixture
def pull_request_record_merged(request):
    record = PullRequestRecord(pull=request.getfixturevalue("mock_pull_merged"))
    record.register_commit(request.getfixturevalue("mock_commit"))
    return record


@pytest.fixture
def pull_request_record_open(request):
    record = PullRequestRecord(pull=request.getfixturevalue("mock_pull_open"))
    record.register_commit(request.getfixturevalue("mock_commit"))
    return record


@pytest.fixture
def issue_request_record_with_merged_pr_with_issue_mentioned(request):
    mock_issue_open_fixture = request.getfixturevalue("mock_issue_open_2")
    record = IssueRecord(issue=mock_issue_open_fixture)
    mock_pull_merged_fixture = request.getfixturevalue("mock_pull_merged")
    mock_pull_merged_fixture.body = "Release Notes:\n- Fixed bug\n- Improved performance\n\nFixes #123"
    record.register_pull_request(mock_pull_merged_fixture)
    record.register_commit(mock_pull_merged_fixture, request.getfixturevalue("mock_commit"))
    return record


@pytest.fixture
def pull_request_record_closed(request):
    record = PullRequestRecord(pull=request.getfixturevalue("mock_pull_closed"))
    record.register_commit(request.getfixturevalue("mock_commit"))
    return record


@pytest.fixture
def pull_request_record_closed_with_skip_label(request):
    record = PullRequestRecord(
        pull=request.getfixturevalue("mock_pull_closed_with_skip_label"),
        skip=True,
    )
    record.register_commit(request.getfixturevalue("mock_commit"))
    return record


@pytest.fixture
def pull_request_record_closed_no_rls_notes(request):
    record = PullRequestRecord(pull=request.getfixturevalue("mock_pull_no_rls_notes"))
    return record


@pytest.fixture
def mock_logging_setup(mocker):
    """Fixture to mock the basic logging setup using pytest-mock."""
    mock_log_config = mocker.patch("logging.basicConfig")
    yield mock_log_config
