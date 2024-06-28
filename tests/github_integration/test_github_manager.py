from unittest.mock import MagicMock, patch, Mock

import pytest
from github import Github
from github.Repository import Repository

from github_integration.github_manager import GithubManager


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

# @patch('github_manager.logging')

# def test_fetch_repository_not_found(logging_mock):
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     github_mock.get_repo.side_effect = Exception('Not Found')
#     repository_id = 'non_existent_repo'
#
#     result = github_manager.fetch_repository(repository_id)
#     assert result is None
#     logging_mock.error.assert_called_with(f"Repository not found: {repository_id}")
#
# def test_fetch_latest_release():
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     release_mock = Mock(spec=GitRelease)
#     repository_mock.get_latest_release.return_value = release_mock
#
#     result = github_manager.fetch_latest_release()
#     assert result == release_mock
#     repository_mock.get_latest_release.assert_called_once()
#
# @patch('github_manager.logging')
# def test_fetch_latest_release_not_found(logging_mock):
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     repository_mock.get_latest_release.side_effect = Exception('Not Found')
#
#     result = github_manager.fetch_latest_release()
#     assert result is None
#     logging_mock.error.assert_called_with(f"Latest release not found for {repository_mock.full_name}. 1st release for repository!")
#
# def test_fetch_issues():
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     issues_mock = [Mock(), Mock()]
#     repository_mock.get_issues.return_value = issues_mock
#
#     result = github_manager.fetch_issues()
#     assert len(result) == len(issues_mock)
#     repository_mock.get_issues.assert_called_with(state="all")
#
# def test_fetch_pull_requests():
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     pulls_mock = [Mock(), Mock()]
#     repository_mock.get_pulls.return_value = pulls_mock
#
#     result = github_manager.fetch_pull_requests()
#     assert len(result) == len(pulls_mock)
#     repository_mock.get_pulls.assert_called_with(state="closed")
#
# def test_fetch_commits():
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     commits_mock = [Mock(), Mock()]
#     repository_mock.get_commits.return_value = commits_mock
#
#     result = github_manager.fetch_commits()
#     assert len(result) == len(commits_mock)
#     repository_mock.get_commits.assert_called_once()
#
# def test_get_change_url_with_release():
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     release_mock = Mock(spec=GitRelease)
#     github_manager._GithubManager__git_release = release_mock
#     release_mock.tag_name = 'v1.0.0'
#     tag_name = 'v2.0.0'
#
#     result = github_manager.get_change_url(tag_name)
#     expected_url = f"https://github.com/{repository_mock.full_name}/compare/{release_mock.tag_name}...{tag_name}"
#     assert result == expected_url
#
# def test_get_change_url_without_release():
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     tag_name = 'v2.0.0'
#
#     result = github_manager.get_change_url(tag_name)
#     expected_url = f"https://github.com/{repository_mock.full_name}/commits/{tag_name}"
#     assert result == expected_url
#
# def test_get_repository_full_name():
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     repository_mock = Mock(spec=Repository)
#     github_manager._GithubManager__repository = repository_mock
#     repository_mock.full_name = 'test/full_name'
#
#     result = github_manager.get_repository_full_name()
#     assert result == 'test/full_name'
#
# @patch('github_manager.logging')
# def test_show_rate_limit(logging_mock):
#     github_manager = GithubManager()
#     github_mock = Mock(spec=Github)
#     github_manager.github = github_mock
#     rate_limit_mock = Mock()
#     rate_limit_mock.core.remaining = 50
#     rate_limit_mock.core.limit = 5000
#     github_mock.get_rate_limit.return_value = rate_limit_mock
#
#     github_manager.show_rate_limit()
#     logging_mock.debug.assert_called_with(f"Rate limit: {rate_limit_mock.core.remaining} remaining of {rate_limit_mock.core.limit}")


if __name__ == '__main__':
    pytest.main()
