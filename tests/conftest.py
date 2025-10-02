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

import copy
import pytest

from github import Github, IssueType
from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Rate import Rate
from github.Repository import Repository

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.chapters.service_chapters import ServiceChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.chapters.custom_chapters import CustomChapters
from release_notes_generator.model.sub_issue_record import SubIssueRecord
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.record_utils import get_id


# Test classes


class MockLabel:
    def __init__(self, name):
        self.name = name


def mock_safe_call_decorator(_rate_limiter):
    def wrapper(fn):
        if fn.__name__ == "get_issues_for_pr":
            return mock_get_issues_for_pr
        return fn
    return wrapper


def mock_get_issues_for_pr(pull_number: int) -> set[int]:
    # if pull_number == 150:
    #     return [451]
    return set()


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
    issue.repository.full_name = "org/repo"
    issue.type = None

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
    issue.repository.full_name = "org/repo"
    issue.type = None

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
    issue.get_sub_issues.return_value = []
    issue.repository.full_name = "org/repo"
    issue.closed_at = datetime.now()
    issue.html_url = "https://github.com/org/repo/issues/121"
    issue.type = None

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
    issue.repository.full_name = "org/repo"
    issue.closed_at = datetime.now()
    issue.html_url = "https://github.com/org/repo/issues/122"
    issue.type = None

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
    issue.repository.full_name = "org/repo"
    issue.closed_at = datetime.now()

    label1 = mocker.Mock(spec=MockLabel)
    label1.name = "skip-release-notes"
    label2 = mocker.Mock(spec=MockLabel)
    label2.name = "bug"
    issue.get_labels.return_value = [label1, label2]

    return issue


@pytest.fixture
def mock_open_sub_issue(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_OPEN
    issue.number = 400
    issue.title = "SI400 open"
    issue.state_reason = None
    issue.body = "I400 open\nRelease Notes:\n- Hierarchy level release note"
    issue.type = None
    issue.created_at = datetime.now()
    issue.closed_at = None
    issue.repository.full_name = "org/repo"

    issue.get_labels.return_value = []
    issue.get_sub_issues.return_value = []

    return (issue)


@pytest.fixture
def mock_closed_sub_issue(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_CLOSED
    issue.number = 450
    issue.title = "SI450 closed"
    issue.state_reason = None
    issue.body = "I450 closed\nRelease Notes:\n- Hierarchy level release note"
    issue.type = None
    issue.created_at = datetime.now()
    issue.closed_at = datetime.now()
    issue.repository.full_name = "org/repo"

    issue.get_labels.return_value = []
    issue.get_sub_issues.return_value = []

    return issue


@pytest.fixture
def mock_open_hierarchy_issue(mocker):
    issue = mocker.Mock(spec=Issue)
    issue.state = IssueRecord.ISSUE_STATE_OPEN
    issue.number = 300
    issue.title = "HI300 open"
    issue.state_reason = None
    issue.body = "I300 open\nRelease Notes:\n- Hierarchy level release note"
    issue.type = None
    issue.created_at = datetime.now()
    issue.closed_at = None
    issue.repository.full_name = "org/repo"

    issue.get_labels.return_value = []
    issue.get_sub_issues.return_value = []

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
    issue.body = "I200 open\nRelease Notes:\n- Epic level release note"
    issue.type = issue_type
    issue.created_at = datetime.now()
    issue.closed_at = None
    issue.repository.full_name = "org/repo"

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
    issue.body = "HI201 open\nRelease Notes:\n- Feature level release note"
    issue.type = issue_type
    issue.created_at = datetime.now()
    issue.closed_at = None
    issue.repository.full_name = "org/repo"

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
    issue.closed_at = datetime.now()
    issue.repository.full_name = "org/repo"

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
    issue.closed_at = datetime.now()
    issue.repository.full_name = "org/repo"

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
    issue.closed_at = datetime.now()
    issue.repository.full_name = "org/repo"

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
    pull.html_url = "http://example.com/pull/101"

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
    pull.html_url = "http://example.com/pull/102"

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
    pull.url = "http://example.com/pull/124"
    pull.number = 124
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
    commit = mocker.Mock(spec=Commit)
    commit.author.login = "author"
    commit.sha = "merge_commit_sha"
    commit.commit.message = "Fixed bug"
    commit.repository.full_name = "org/repo"
    return commit


@pytest.fixture
def mined_data_isolated_record_types_no_labels_no_type_defined(
        mock_repo, mock_issue_closed, mock_pull_closed, mock_pull_merged, mock_commit,
        mock_open_hierarchy_issue, mock_open_sub_issue, mock_closed_sub_issue
):
    #   - single issue record (closed)
    #   - single hierarchy issue record - two sub-issues without PRs
    #   - single hierarchy issue record - two sub-issues with PRs - no commits
    #   - single hierarchy issue record - two sub-issues with PRs - with commits
    #   - single hierarchy issue record - one sub hierarchy issues - two sub-issues with PRs - with commits
    #   - single pull request record (closed, merged)
    #   - single direct commit record
    data = MinedData(mock_repo)

    # single issue record (closed)
    solo_closed_issue = copy.deepcopy(mock_issue_closed)        # 121
    solo_closed_issue.body += "\nRelease Notes:\n- Solo issue release note"
    solo_closed_issue.get_labels.return_value = []
    data.parents_sub_issues[get_id(solo_closed_issue, mock_repo)] = []

    # single hierarchy issue record - two sub-issues without PRs
    hi_two_sub_issues_no_prs = copy.deepcopy(mock_open_hierarchy_issue)
    hi_two_sub_issues_no_prs.number = 301
    hi_two_sub_issues_no_prs.title = "HI301 open"
    hi_two_sub_issues_no_prs.body = "I301 open\nRelease Notes:\n- Hierarchy level release note"
    sub_issue_1 = copy.deepcopy(mock_open_sub_issue)
    sub_issue_2 = copy.deepcopy(mock_closed_sub_issue)
    data.parents_sub_issues[si1 := get_id(sub_issue_1, mock_repo)] = []
    data.parents_sub_issues[si2 := get_id(sub_issue_2, mock_repo)] = []
    data.parents_sub_issues[get_id(hi_two_sub_issues_no_prs, mock_repo)] = [si1, si2]

    # single hierarchy issue record - two sub-issues with PRs - no commits
    hi_two_sub_issues_with_prs = copy.deepcopy(mock_open_hierarchy_issue)
    hi_two_sub_issues_with_prs.number = 302
    hi_two_sub_issues_with_prs.title = "HI302 open"
    hi_two_sub_issues_with_prs.body = "I302 open\nRelease Notes:\n- Hierarchy level release note"
    sub_issue_3 = copy.deepcopy(mock_open_sub_issue)
    sub_issue_3.number = 401
    sub_issue_3.title = "SI401 open"
    sub_issue_3.body = "I401 open\nRelease Notes:\n- Hierarchy level release note"
    sub_issue_4 = copy.deepcopy(mock_closed_sub_issue)
    sub_issue_4.number = 451
    sub_issue_4.title = "SI451 closed"
    sub_issue_4.body = "I451 open\nRelease Notes:\n- Hierarchy level release note"
    mock_pr_closed_2 = copy.deepcopy(mock_pull_closed)
    mock_pr_closed_2.url = "http://example.com/pull/150"
    mock_pr_closed_2.number = 150
    mock_pr_closed_2.merge_commit_sha = "merge_commit_sha_150"
    mock_pr_closed_2.get_labels.return_value = []
    mock_pr_closed_2.body += "\nCloses #451"
    data.parents_sub_issues[si3 := get_id(sub_issue_3, mock_repo)] = []
    data.parents_sub_issues[si4 := get_id(sub_issue_4, mock_repo)] = []
    data.parents_sub_issues[get_id(hi_two_sub_issues_with_prs, mock_repo)] = [si3, si4]

    # single hierarchy issue record - two sub-issues with PRs - with commits
    hi_two_sub_issues_with_prs_with_commit = copy.deepcopy(mock_open_hierarchy_issue)
    hi_two_sub_issues_with_prs_with_commit.number = 303
    hi_two_sub_issues_with_prs_with_commit.title = "HI303 open"
    hi_two_sub_issues_with_prs_with_commit.body = "I303 open\nRelease Notes:\n- Hierarchy level release note"
    sub_issue_5 = copy.deepcopy(mock_open_sub_issue)
    sub_issue_5.number = 402
    sub_issue_5.title = "SI402 open"
    sub_issue_5.body = "I402 open\nRelease Notes:\n- Hierarchy level release note"
    sub_issue_6 = copy.deepcopy(mock_closed_sub_issue)
    sub_issue_6.number = 452
    sub_issue_6.title = "SI452 closed"
    sub_issue_6.body = "I452 open\nRelease Notes:\n- Hierarchy level release note"
    mock_pr_closed_3 = copy.deepcopy(mock_pull_closed)
    mock_pr_closed_3.url = "http://example.com/pull/151"
    mock_pr_closed_3.number = 151
    mock_pr_closed_3.merge_commit_sha = "merge_commit_sha_151"
    mock_pr_closed_3.get_labels.return_value = []
    mock_pr_closed_3.body += "\nCloses #452"
    mock_commit_1 = copy.deepcopy(mock_commit)
    mock_commit_1.sha = "merge_commit_sha_151"
    mock_commit_1.commit.message = "Fixed bug in PR 151"
    data.parents_sub_issues[si5 := get_id(sub_issue_5, mock_repo)] = []
    data.parents_sub_issues[si6 := get_id(sub_issue_6, mock_repo)] = []
    data.parents_sub_issues[get_id(hi_two_sub_issues_with_prs_with_commit, mock_repo)] = [si5, si6]

    # single hierarchy issue record - one sub hierarchy issues - two sub-issues with PRs - with commits
    hi_one_sub_hierarchy_two_sub_issues_with_prs_with_commit = copy.deepcopy(mock_open_hierarchy_issue)
    hi_one_sub_hierarchy_two_sub_issues_with_prs_with_commit.number = 304
    hi_one_sub_hierarchy_two_sub_issues_with_prs_with_commit.title = "HI304 open"
    hi_one_sub_hierarchy_two_sub_issues_with_prs_with_commit.body = "I304 open\nRelease Notes:\n- Hierarchy level release note"
    sub_hierarchy_issue = copy.deepcopy(mock_open_hierarchy_issue)
    sub_hierarchy_issue.number = 350
    sub_hierarchy_issue.title = "HI350 open"
    sub_hierarchy_issue.body = "I350 open\nRelease Notes:\n- Sub-hierarchy level release note"
    sub_issue_7 = copy.deepcopy(mock_open_sub_issue)
    sub_issue_7.number = 403
    sub_issue_7.title = "SI403 open"
    sub_issue_7.body = "I403 open\nRelease Notes:\n- Hierarchy level release note"
    sub_issue_8 = copy.deepcopy(mock_closed_sub_issue)
    sub_issue_8.number = 453
    sub_issue_8.title = "SI453 closed"
    sub_issue_8.body = "I453 open\nRelease Notes:\n- Hierarchy level release note"
    mock_pr_closed_4 = copy.deepcopy(mock_pull_closed)
    mock_pr_closed_4.url = "http://example.com/pull/152"
    mock_pr_closed_4.number = 152
    mock_pr_closed_4.merge_commit_sha = "merge_commit_sha_152"
    mock_pr_closed_4.get_labels.return_value = []
    mock_pr_closed_4.body += "\nCloses #453"
    mock_commit_2 = copy.deepcopy(mock_commit)
    mock_commit_2.sha = "merge_commit_sha_152"
    mock_commit_2.commit.message = "Fixed bug in PR 152"
    data.parents_sub_issues[si7 := get_id(sub_issue_7, mock_repo)] = []
    data.parents_sub_issues[si8 := get_id(sub_issue_8, mock_repo)] = []
    data.parents_sub_issues[shi := get_id(sub_hierarchy_issue, mock_repo)] = [si7, si8]
    data.parents_sub_issues[get_id(hi_one_sub_hierarchy_two_sub_issues_with_prs_with_commit, mock_repo)] = [shi]

    # single pull request record (closed, merged)
    mock_pr_closed_1 = copy.deepcopy(mock_pull_closed)      # 123
    mock_pr_closed_1.get_labels.return_value = []
    mock_pr_merged_1 = copy.deepcopy(mock_pull_merged)      # 124
    mock_pr_merged_1.get_labels.return_value = []

    # single direct commit record
    mock_commit_3 = copy.deepcopy(mock_commit)
    mock_commit_3.sha = "merge_commit_sha_direct"
    mock_commit_3.commit.message = "Direct commit example"

    data.issues = {solo_closed_issue: mock_repo,
                   hi_two_sub_issues_no_prs: mock_repo,
                   hi_two_sub_issues_with_prs: mock_repo,
                   hi_two_sub_issues_with_prs_with_commit: mock_repo,
                   hi_one_sub_hierarchy_two_sub_issues_with_prs_with_commit: mock_repo,    # index 4
                   sub_issue_1: mock_repo, sub_issue_2: mock_repo,                         # index 5,6
                   sub_issue_3: mock_repo, sub_issue_4: mock_repo,                         # index 7,8
                   sub_issue_5: mock_repo, sub_issue_6: mock_repo,                         # index 9,10
                   sub_issue_7: mock_repo, sub_issue_8: mock_repo,                         # index 11,12
                   sub_hierarchy_issue: mock_repo}                                         # index 13
    data.pull_requests = {mock_pr_closed_1: mock_repo, mock_pr_merged_1: mock_repo,
                          mock_pr_closed_2: mock_repo, mock_pr_closed_3: mock_repo,
                          mock_pr_closed_4: mock_repo}
    data.commits = {mock_commit_1: mock_repo, mock_commit_2: mock_repo, mock_commit_3: mock_repo}

    return data


@pytest.fixture
def mined_data_isolated_record_types_with_labels_no_type_defined(mocker, mined_data_isolated_record_types_no_labels_no_type_defined):
    data = mined_data_isolated_record_types_no_labels_no_type_defined

    l_enh = mocker.Mock(spec=MockLabel)
    l_enh.name = "enhancement"
    l_epic = mocker.Mock(spec=MockLabel)
    l_epic.name = "epic"
    l_feature = mocker.Mock(spec=MockLabel)
    l_feature.name = "feature"
    l_api = mocker.Mock(spec=MockLabel)
    l_api.name = "API"
    l_bug = mocker.Mock(spec=MockLabel)
    l_bug.name = "bug"

    iks = list(data.issues.keys())
    iks[0].get_labels.return_value = [l_enh]

    iks[1].get_labels.return_value = [l_epic]       # 301
    iks[2].get_labels.return_value = [l_epic]       # 302
    iks[3].get_labels.return_value = [l_epic]       # 303
    iks[4].get_labels.return_value = [l_epic]       # 304

    iks[13].get_labels.return_value = [l_feature]   # 350

    iks[5].get_labels.return_value = [l_api]
    iks[6].get_labels.return_value = [l_api]
    iks[7].get_labels.return_value = [l_api]
    iks[8].get_labels.return_value = [l_api]
    iks[9].get_labels.return_value = [l_api]
    iks[10].get_labels.return_value = [l_api]
    iks[11].get_labels.return_value = [l_api]
    iks[12].get_labels.return_value = [l_api]

    pks = list(data.pull_requests.keys())
    pks[0].get_labels.return_value = [l_bug]
    pks[4].get_labels.return_value = [l_bug]

    return data


@pytest.fixture
def mined_data_isolated_record_types_no_labels_with_type_defined(mocker, mined_data_isolated_record_types_no_labels_no_type_defined):
    data = mined_data_isolated_record_types_no_labels_no_type_defined

    t_epic = mocker.Mock(spec=IssueType)
    t_epic.name = "Epic"
    t_feature = mocker.Mock(spec=IssueType)
    t_feature.name = "Feature"
    t_task = mocker.Mock(spec=IssueType)
    t_task.name = "Task"
    t_bug = mocker.Mock(spec=IssueType)
    t_bug.name = "Bug"

    l_epic = mocker.Mock(spec=MockLabel)
    l_epic.name = "epic"
    l_feature = mocker.Mock(spec=MockLabel)
    l_feature.name = "feature"
    l_task = mocker.Mock(spec=MockLabel)
    l_task.name = "task"

    iks = list(data.issues.keys())
    iks[0].type = t_feature
    iks[0].get_labels.return_value = [l_feature]

    iks[1].type = t_epic       # 301
    iks[1].get_labels.return_value = [l_epic]
    iks[2].type = t_epic       # 302
    iks[2].get_labels.return_value = [l_epic]
    iks[3].type = t_epic       # 303
    iks[3].get_labels.return_value = [l_epic]
    iks[4].type = t_epic       # 304
    iks[4].get_labels.return_value = [l_epic]

    iks[13].type = t_feature   # 350
    iks[13].get_labels.return_value = [l_feature]

    iks[5].type = t_task
    iks[5].get_labels.return_value = [l_task]
    iks[6].type = t_task
    iks[6].get_labels.return_value = [l_task]
    iks[7].type = t_task
    iks[7].get_labels.return_value = [l_task]
    iks[8].type = t_task
    iks[8].get_labels.return_value = [l_task]
    iks[9].type = t_task
    iks[9].get_labels.return_value = [l_task]
    iks[10].type = t_task
    iks[10].get_labels.return_value = [l_task]
    iks[11].type = t_task
    iks[11].get_labels.return_value = [l_task]
    iks[12].type = t_task
    iks[12].get_labels.return_value = [l_task]

    return data


@pytest.fixture
def mined_data_isolated_record_types_with_labels_with_type_defined(mocker, mined_data_isolated_record_types_with_labels_no_type_defined):
    data = mined_data_isolated_record_types_with_labels_no_type_defined

    t_epic = mocker.Mock(spec=IssueType)
    t_epic.name = "Epic"
    t_feature = mocker.Mock(spec=IssueType)
    t_feature.name = "Feature"
    t_task = mocker.Mock(spec=IssueType)
    t_task.name = "Task"
    t_bug = mocker.Mock(spec=IssueType)
    t_bug.name = "Bug"

    iks = list(data.issues.keys())
    iks[0].type = t_bug

    iks[1].type = t_epic       # 301
    iks[2].type = t_epic       # 302
    iks[3].type = t_epic       # 303
    iks[4].type = t_epic       # 304

    iks[13].type = t_feature   # 350

    iks[5].type = t_task
    iks[6].type = t_task
    iks[7].type = t_task
    iks[8].type = t_task
    iks[9].type = t_task
    iks[10].type = t_task
    iks[11].type = t_task
    iks[12].type = t_task

    return data


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
    rec_epic_issue = HierarchyIssueRecord(
        issue=request.getfixturevalue("mock_open_hierarchy_issue_epic"),
        issue_labels=["epic"]
    )  # nr:200

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
