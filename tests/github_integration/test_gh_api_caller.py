import pytest

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from github import (Github, Issue as GithubIssue, PullRequest as GithubPullRequest, RateLimit, Rate, GitRelease,
                    Repository)
from github.GitRelease import GitRelease
from github.Repository import Repository
from github_integration.gh_api_caller import (get_gh_repository, fetch_latest_release, fetch_closed_issues,
                                              fetch_finished_pull_requests, generate_change_url, show_rate_limit)


class MockIssue:
    def __init__(self, id, title, labels, is_closed, linked_pr_id):
        self.id = id
        self.title = title
        self.labels = labels
        self.is_closed = is_closed
        self.linked_pr_id = linked_pr_id


# get_gh_repository

@patch('github.Github.get_repo')
def test_get_gh_repository_found(mock_get_repo):
    g = Github()
    repo_id = 'test/repo'

    mock_repo = MagicMock(spec=Repository)
    mock_get_repo.return_value = mock_repo

    result = get_gh_repository(g, repo_id)

    mock_get_repo.assert_called_with(repo_id)
    assert result == mock_repo


@patch('github.Github.get_repo')
def test_get_gh_repository_not_found(mock_get_repo, capfd):
    g = Github()
    repo_id = 'test/repo'

    mock_get_repo.side_effect = Exception("Not Found")

    result = get_gh_repository(g, repo_id)

    assert result is None
    captured = capfd.readouterr()
    assert "Repository not found" in captured.out
    assert "not found" in captured.out


@patch('github.Github.get_repo')
def test_get_gh_repository_exception(mock_get_repo, capfd):
    g = Github()
    repo_id = 'test/repo'

    mock_get_repo.side_effect = Exception("Other error")

    result = get_gh_repository(g, repo_id)

    assert result is None
    captured = capfd.readouterr()
    assert "Fetching repository failed for test/repo" in captured.out
    assert "Other error" in captured.out


# fetch_latest_release

def test_fetch_latest_release_found():
    mock_release = Mock(spec=GitRelease)
    mock_release.tag_name = "v1.0.0"
    mock_release.created_at = datetime(2023, 1, 1)
    mock_release.published_at = datetime(2023, 1, 2)

    mock_repo = Mock(spec=Repository)
    mock_repo.get_latest_release.return_value = mock_release

    release = fetch_latest_release(mock_repo)

    assert release == mock_release
    assert release.tag_name == "v1.0.0"
    assert release.created_at == datetime(2023, 1, 1)
    assert release.published_at == datetime(2023, 1, 2)


def test_fetch_latest_release_not_found(capfd):
    # Mock the Repository object to raise an exception
    mock_repo = Mock(spec=Repository)
    mock_repo.get_latest_release.side_effect = Exception("Not Found")

    release = fetch_latest_release(mock_repo)

    assert release is None
    captured = capfd.readouterr()
    assert "Latest release not found" in captured.out
    assert "not found" in captured.out


def test_fetch_latest_release_exception(capfd):
    # Mock the Repository object to raise a different exception
    mock_repo = Mock(spec=Repository)
    mock_repo.get_latest_release.side_effect = Exception("Some other error")

    release = fetch_latest_release(mock_repo)

    assert release is None
    captured = capfd.readouterr()
    assert "Fetching latest release failed" in captured.out
    assert "Some other error" in captured.out


# fetch_closed_issues

def test_fetch_closed_issues_with_release(capfd):
    mock_release = Mock(spec=GitRelease)
    mock_release.published_at = datetime(2023, 1, 2)

    mock_label = Mock()
    mock_label.name = "bug"

    mock_issue = Mock(spec=GithubIssue)
    mock_issue.id = 1
    mock_issue.title = "Issue 1"
    mock_issue.labels = [mock_label]
    mock_issue.pull_request = None

    mock_repo = Mock(spec=Repository)
    mock_repo.get_issues.return_value = [mock_issue]
    mock_repo.full_name = "test/repo"

    issues = fetch_closed_issues(mock_repo, mock_release)

    assert len(issues) == 1
    assert issues[0].id == 1
    assert issues[0].title == "Issue 1"
    assert issues[0].labels == ["bug"]
    assert issues[0].is_closed is True
    assert issues[0].linked_pr_id is None

    captured = capfd.readouterr()
    assert "Found 1 closed issues for test/repo" in captured.out


def test_fetch_closed_issues_without_release(capfd):
    mock_label = Mock()
    mock_label.name = "bug"

    mock_issue = Mock(spec=GithubIssue)
    mock_issue.id = 1
    mock_issue.title = "Issue 1"
    mock_issue.labels = [mock_label]

    mock_repo = Mock(spec=Repository)
    mock_repo.get_issues.return_value = [mock_issue]
    mock_repo.full_name = "test/repo"

    issues = fetch_closed_issues(mock_repo, None)

    assert len(issues) == 1
    assert issues[0].id == 1
    assert issues[0].title == "Issue 1"
    assert issues[0].labels == ["bug"]

    captured = capfd.readouterr()
    assert "Found 1 closed issues for test/repo" in captured.out


def test_fetch_finished_pull_requests_multiple_pulls(capfd):
    mock_pull1 = Mock(spec=GithubPullRequest)
    mock_pull1.id = 1
    mock_pull1.title = "PR 1"
    mock_pull1.labels = [Mock(name="bug")]
    mock_pull1.issue_url = "https://api.github.com/repos/owner/repo/issues/123"

    mock_pull2 = Mock(spec=GithubPullRequest)
    mock_pull2.id = 2
    mock_pull2.title = "PR 2"
    mock_pull2.labels = [Mock(name="enhancement")]
    mock_pull2.issue_url = "https://api.github.com/repos/owner/repo/issues/456"

    mock_repo = Mock(spec=Repository)
    mock_repo.get_pulls.return_value = [mock_pull1, mock_pull2]
    mock_repo.full_name = "test/repo"

    pull_requests = fetch_finished_pull_requests(mock_repo)

    assert len(pull_requests) == 2
    assert pull_requests[0].id == 1
    assert pull_requests[0].title == "PR 1"
    assert pull_requests[0].linked_issue_id == "123"
    assert pull_requests[1].id == 2
    assert pull_requests[1].title == "PR 2"
    assert pull_requests[1].linked_issue_id == "456"

    captured = capfd.readouterr()
    assert "Found 2 PRs for test/repo" in captured.out


def test_fetch_finished_pull_requests_no_issue_url(capfd):
    mock_pull = Mock(spec=GithubPullRequest)
    mock_pull.id = 1
    mock_pull.title = "PR 1"
    mock_pull.labels = [Mock(name="bug")]
    mock_pull.issue_url = None

    mock_repo = Mock(spec=Repository)
    mock_repo.get_pulls.return_value = [mock_pull]
    mock_repo.full_name = "test/repo"

    pull_requests = fetch_finished_pull_requests(mock_repo)

    assert len(pull_requests) == 1
    assert pull_requests[0].id == 1
    assert pull_requests[0].title == "PR 1"
    assert pull_requests[0].linked_issue_id is None

    captured = capfd.readouterr()
    assert "Found 1 PRs for test/repo" in captured.out


# generate_change_url

def test_generate_change_url_with_release(capfd):
    mock_release = Mock(spec=GitRelease)
    mock_release.tag_name = "v1.0.0"

    mock_repo = Mock(spec=Repository)
    mock_repo.owner = "owner"
    mock_repo.name = "repo"

    tag_name = "v1.1.0"
    expected_url = f"https://github.com/owner/repo/compare/v1.0.0...v1.1.0"

    url = generate_change_url(mock_repo, mock_release, tag_name)

    assert url == expected_url

    captured = capfd.readouterr()
    assert f"Changelog URL: {expected_url}" in captured.out


def test_generate_change_url_without_release(capfd):
    mock_repo = Mock(spec=Repository)
    mock_repo.owner = "owner"
    mock_repo.name = "repo"

    tag_name = "v1.1.0"
    expected_url = f"https://github.com/owner/repo/commits/v1.1.0"

    url = generate_change_url(mock_repo, None, tag_name)

    assert url == expected_url

    captured = capfd.readouterr()
    assert f"Changelog URL: {expected_url}" in captured.out


# show_rate_limit

def test_show_rate_limit_not_reached(capfd):
    mock_core_rate = Mock(spec=Rate)
    mock_core_rate.remaining = 15
    mock_core_rate.limit = 60

    mock_rate_limit = Mock(spec=RateLimit)
    mock_rate_limit.core = mock_core_rate

    mock_github = Mock(spec=Github)
    mock_github.get_rate_limit.return_value = mock_rate_limit

    show_rate_limit(mock_github)

    captured = capfd.readouterr()
    assert "Rate limit: 15 remaining of 60" in captured.out


@patch("time.sleep", return_value=None)
def test_show_rate_limit_reached(mock_sleep, capfd):
    mock_core_rate = Mock(spec=Rate)
    mock_core_rate.remaining = 5
    mock_core_rate.limit = 60
    mock_core_rate.reset = datetime.utcnow() + timedelta(minutes=5)

    mock_rate_limit = Mock(spec=RateLimit)
    mock_rate_limit.core = mock_core_rate

    mock_github = Mock(spec=Github)
    mock_github.get_rate_limit.return_value = mock_rate_limit

    show_rate_limit(mock_github)

    captured = capfd.readouterr()
    assert "Rate limit reached. Sleeping for " in captured.out
    assert mock_sleep.called


if __name__ == '__main__':
    pytest.main()
