from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock

import pytest
from github import Github
from github.GitRelease import GitRelease
from github.Repository import Repository

from action.action_inputs import ActionInputs
from github_integration.github_manager import GithubManager
from github_integration.model.issue import Issue


# Mock classes

class MockPullRequest:
    def __init__(self, body):
        self.body = body


# singleton

def test_singleton():
    manager1 = GithubManager()
    manager2 = GithubManager()
    assert manager1 is manager2


# GithubManager.fetch_repository

def test_fetch_repository():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock

    repository_mock = Mock(spec=Repository)
    github_mock.get_repo.return_value = repository_mock

    repository_id = 'test_repo'

    result = GithubManager().fetch_repository(repository_id)

    assert repository_mock == result
    github_mock.get_repo.assert_called_with(repository_id)


@patch('github_integration.github_manager.logging')
def test_fetch_repository_not_found(logging_mock):
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    github_mock.get_repo.side_effect = Exception('Not Found')
    repository_id = 'non_existent_repo'

    result = GithubManager().fetch_repository(repository_id)

    assert result is None
    logging_mock.error.assert_called_with(f"Repository not found: {repository_id}")


@patch('github_integration.github_manager.logging')
def test_fetch_repository_exception(logging_mock):
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    github_mock.get_repo.side_effect = Exception('Unexpected error')
    repository_id = 'non_existent_repo'

    result = GithubManager().fetch_repository(repository_id)

    assert result is None
    logging_mock.error.assert_called_with(f"Fetching repository failed for {repository_id}: Unexpected error")


# GithubManager.fetch_latest_release

def test_fetch_latest_release():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    release_mock = Mock(spec=GitRelease)
    repository_mock.get_latest_release.return_value = release_mock

    result = GithubManager().fetch_latest_release()

    assert release_mock == result
    repository_mock.get_latest_release.assert_called_once()


def test_fetch_latest_release_no_repository():
    result = GithubManager().reset().fetch_latest_release()

    assert result is None


@patch('github_integration.github_manager.logging')
def test_fetch_latest_release_not_found(logging_mock):
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    repository_mock.get_latest_release.side_effect = Exception('Not Found')

    result = GithubManager().fetch_latest_release()

    assert result is None
    logging_mock.error.assert_called_with(f"Latest release not found for {repository_mock.full_name}. 1st release for repository!")


@patch('github_integration.github_manager.logging')
def test_fetch_latest_release_exception(logging_mock):
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    repository_mock.get_latest_release.side_effect = Exception('Unexpected error')
    repository_mock.full_name = "owner/test"

    result = GithubManager().fetch_latest_release()

    assert result is None
    logging_mock.error.assert_called_with(f"Fetching latest release failed for owner/test: Unexpected error. Expected first release for repository.")


# GithubManager.fetch_issue

def test_fetch_issue_success():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    issue_number = 123
    issue_mock = Mock()
    issue_mock.number = issue_number
    repository_mock.get_issue.return_value = issue_mock

    result = GithubManager().fetch_issue(issue_number)

    assert issue_number == result.number
    repository_mock.get_issue.assert_called_with(issue_number)


def test_fetch_issue_success_no_repository():
    result = GithubManager().reset().fetch_issue(123)

    assert result is None


def test_fetch_issue_success_failed():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    issue_number = 123
    repository_mock.get_issue.side_effect = Exception('Unexpected error')

    result = GithubManager().fetch_issue(issue_number)

    assert result is None
    repository_mock.get_issue.assert_called_with(issue_number)


# GithubManager.fetch_issues

def test_fetch_issues_without_git_release():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    issues_mock = [Mock(), Mock()]
    repository_mock.get_issues.return_value = issues_mock

    result = GithubManager().fetch_issues()

    assert len(issues_mock) == len(result)
    repository_mock.get_issues.assert_called_with(state="all", since=None)      # get all state of issues in 'one' call


def test_fetch_issues_without_git_release_no_repository():
    result = GithubManager().reset().fetch_issues()

    assert len(result) == 0


def test_fetch_issues_with_git_release():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    git_release_mock = Mock()
    git_release_mock.created_at = datetime(2023, 1, 1)
    git_release_mock.published_at = datetime(2023, 1, 2)
    GithubManager()._GithubManager__git_release = git_release_mock
    issues_mock = [Mock(), Mock()]
    repository_mock.get_issues.return_value = issues_mock

    result = GithubManager().fetch_issues()

    assert len(issues_mock) == len(result)
    repository_mock.get_issues.assert_called_with(state="all", since=git_release_mock.published_at)


def test_fetch_issues_with_git_release_failed():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    git_release_mock = Mock()
    git_release_mock.created_at = datetime(2023, 1, 1)
    git_release_mock.published_at = datetime(2023, 1, 2)
    GithubManager()._GithubManager__git_release = git_release_mock
    repository_mock.get_issues.side_effect = Exception('Unexpected error')

    result = GithubManager().fetch_issues()

    assert len(result) == 0
    repository_mock.get_issues.assert_called_with(state="all", since=git_release_mock.published_at)


# GithubManager.fetch_pull_requests

def test_fetch_pull_requests():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    pulls_mock = [Mock(body="PR body 1"), Mock(body="PR body 2")]
    repository_mock.get_pulls.return_value = pulls_mock

    result = GithubManager().fetch_pull_requests()

    assert len(pulls_mock) == len(result)
    repository_mock.get_pulls.assert_called_with(state="closed")


# GithubManager.fetch_commits

def test_fetch_commits():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    commits_mock = [Mock(), Mock()]
    repository_mock.get_commits.return_value = commits_mock

    result = GithubManager().fetch_commits()

    assert len(commits_mock) == len(result)
    repository_mock.get_commits.assert_called_once()


# GithubManager.fetch_commits

def test_get_change_url_with_release():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    release_mock = Mock(spec=GitRelease)
    GithubManager()._GithubManager__git_release = release_mock
    release_mock.tag_name = 'v1.0.0'
    tag_name = 'v2.0.0'
    expected_url = f"https://github.com/{repository_mock.full_name}/compare/{release_mock.tag_name}...{tag_name}"

    result = GithubManager().get_change_url(tag_name)

    assert expected_url == result


def test_get_change_url_without_release():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    repository_mock.full_name = 'owner/test'
    GithubManager()._GithubManager__repository = repository_mock
    GithubManager()._GithubManager__git_release = None
    tag_name = 'v1.0.0'
    expected_url = f"https://github.com/{repository_mock.full_name}/commits/{tag_name}"

    result = GithubManager().get_change_url(tag_name)

    assert expected_url == result


def test_get_change_url_no_repository():
    result = GithubManager().reset().get_change_url('v1.0.0')

    assert result == ""


# GithubManager.repository_full_name

def test_get_repository_full_name():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    repository_mock = Mock(spec=Repository)
    GithubManager()._GithubManager__repository = repository_mock
    repository_mock.full_name = 'test/full_name'

    result = GithubManager().get_repository_full_name()

    assert 'test/full_name' == result


def test_get_repository_full_name_without_repository():
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    GithubManager()._GithubManager__repository = None

    result = GithubManager().get_repository_full_name()

    assert result is None


# GithubManager.show_rate_limit

@patch('github_integration.github_manager.logging')
def test_show_rate_limit_threshold_not_reached(logging_mock):
    logging_mock.getLogger.return_value.isEnabledFor.return_value = True
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    rate_limit_mock = Mock()
    rate_limit_mock.core.remaining = 4000
    rate_limit_mock.core.limit = 5000
    github_mock.get_rate_limit.return_value = rate_limit_mock

    GithubManager().show_rate_limit()

    logging_mock.debug.assert_called_with(f"Rate limit: {rate_limit_mock.core.remaining} remaining of {rate_limit_mock.core.limit}")


@patch('github_integration.github_manager.logging')
@patch('time.sleep', return_value=None)
@patch('github_integration.github_manager.datetime')
def test_show_rate_limit_threshold_reached(datetime_mock, time_sleep_mock, logging_mock):
    logging_mock.getLogger.return_value.isEnabledFor.return_value = True
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    rate_limit_mock = Mock()
    rate_limit_mock.core.remaining = 50
    rate_limit_mock.core.limit = 5000
    now = datetime.utcnow()
    reset_time = now + timedelta(seconds=60)
    rate_limit_mock.core.reset = reset_time
    github_mock.get_rate_limit.return_value = rate_limit_mock
    datetime_mock.utcnow.return_value = now

    GithubManager().show_rate_limit()

    logging_mock.debug.assert_called_with(f"Rate limit reached. Sleeping for {70.0} seconds.")
    time_sleep_mock.assert_called_with(70.0)


@patch('github_integration.github_manager.logging')
def test_show_rate_limit_log_level_info(logging_mock):
    logging_mock.getLogger.return_value.isEnabledFor.return_value = False

    GithubManager().show_rate_limit()

    logging_mock.debug.assert_not_called()
    logging_mock.error.assert_not_called()


@patch('github_integration.github_manager.logging')
def test_show_rate_limit_no_github(logging_mock):
    logging_mock.getLogger.return_value.isEnabledFor.return_value = True

    GithubManager().github = None
    GithubManager().show_rate_limit()

    logging_mock.error.assert_called_with(f"GitHub object is not set.")
    assert GithubManager().github is None
    assert GithubManager().repository is None
    assert GithubManager().git_release is None


@patch('github_integration.github_manager.logging')
def test_show_rate_limit_failed(logging_mock):
    github_mock = Mock(spec=Github)
    GithubManager().github = github_mock
    github_mock.get_rate_limit.side_effect = Exception('Unexpected error')

    GithubManager().show_rate_limit()


if __name__ == '__main__':
    pytest.main()
