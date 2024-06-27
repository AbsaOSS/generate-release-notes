import pytest


class MockIssue:
    def __init__(self, id, title, labels, is_closed, linked_pr_id):
        self.id = id
        self.title = title
        self.labels = labels
        self.is_closed = is_closed
        self.linked_pr_id = linked_pr_id


# get_gh_repository

# @patch('github.Github.get_repo')
# def test_get_gh_repository_found(mock_get_repo):
#     g = Github()
#     repo_id = 'test/repo'
#
#     mock_repo = MagicMock(spec=Repository)
#     mock_get_repo.return_value = mock_repo
#
#     result = get_gh_repository(g, repo_id)
#
#     mock_get_repo.assert_called_with(repo_id)
#     assert mock_repo == result
#
#
# @patch('github.Github.get_repo')
# def test_get_gh_repository_not_found_exception(mock_get_repo, caplog):
#     g = Github()
#     repo_id = 'test/repo'
#
#     mock_get_repo.side_effect = Exception("Not Found")
#
#     with caplog.at_level(logging.ERROR):
#         result = get_gh_repository(g, repo_id)
#
#     assert result is None
#     assert "Repository not found" in caplog.text
#     assert repo_id in caplog.text
#
#
# @patch('github.Github.get_repo')
# def test_get_gh_repository_exception(mock_get_repo, caplog):
#     g = Github()
#     repo_id = 'test/repo'
#
#     mock_get_repo.side_effect = Exception("Other error")
#
#     with caplog.at_level(logging.ERROR):
#         result = get_gh_repository(g, repo_id)
#
#     assert result is None
#     assert "Fetching repository failed for test/repo" in caplog.text
#     assert "Other error" in caplog.text
#
#
# # fetch_latest_release
#
# def test_fetch_latest_release_found():
#     mock_release = Mock(spec=GitRelease)
#     mock_release.tag_name = "v1.0.0"
#     mock_release.created_at = datetime(2023, 1, 1)
#     mock_release.published_at = datetime(2023, 1, 2)
#
#     mock_repo = Mock(spec=Repository)
#     mock_repo.get_latest_release.return_value = mock_release
#
#     release = fetch_latest_release(mock_repo)
#
#     assert mock_release == release
#     assert "v1.0.0" == release.tag_name
#     assert datetime(2023, 1, 1) == release.created_at
#     assert datetime(2023, 1, 2) == release.published_at
#
#
# def test_fetch_latest_release_not_found(caplog):
#     # Mock the Repository object to raise an exception
#     mock_repo = Mock(spec=Repository)
#     mock_repo.get_latest_release.side_effect = Exception("Not Found")
#
#     with caplog.at_level(logging.ERROR):
#         release = fetch_latest_release(mock_repo)
#
#     assert release is None
#     assert "Latest release not found" in caplog.text
#     assert "not found" in caplog.text
#
#
# def test_fetch_latest_release_exception(caplog):
#     # Mock the Repository object to raise a different exception
#     mock_repo = Mock(spec=Repository)
#     mock_repo.get_latest_release.side_effect = Exception("Some other error")
#
#     with caplog.at_level(logging.ERROR):
#         release = fetch_latest_release(mock_repo)
#
#     assert release is None
#     assert "Fetching latest release failed" in caplog.text
#     assert "Some other error" in caplog.text
#
#
# # fetch_closed_issues
#
# def test_fetch_closed_issues_with_release(caplog):
#     mock_release = Mock(spec=GitRelease)
#     mock_release.published_at = datetime(2023, 1, 2)
#
#     mock_label = Mock()
#     mock_label.name = "bug"
#
#     mock_issue = Mock(spec=GithubIssue)
#     mock_issue.id = 1
#     mock_issue.title = "Issue 1"
#     mock_issue.labels = [mock_label]
#     mock_issue.number = 1
#     mock_issue.pull_request = None
#     mock_issue.body = "Dummy body"
#     mock_issue.state = "closed"
#
#     mock_repo = Mock(spec=Repository)
#     mock_repo.get_issues.return_value = [mock_issue]
#     mock_repo.full_name = "test/repo"
#
#     with caplog.at_level(logging.DEBUG):
#         issues = fetch_all_issues(mock_repo, mock_release)
#
#     assert 1 == len(issues)
#     assert 1 == issues[0].id
#     assert 1 == issues[0].number
#     assert "Issue 1" == issues[0].title
#     assert ["bug"] == issues[0].labels
#     assert issues[0].is_closed is True
#     assert "Found 1 issues for test/repo" in caplog.text
#
#
# def test_fetch_closed_issues_without_release(caplog):
#     mock_issue = Mock(spec=GithubIssue)
#     mock_issue.title = "Issue 1"
#     mock_issue.number = 1
#     mock_issue.body = "Dummy body"
#     mock_issue.state = "closed"
#     mock_issue.labels = ["bug"]
#
#     mock_repo = Mock(spec=Repository)
#     mock_repo.get_issues.return_value = [mock_issue]
#     mock_repo.full_name = "test/repo"
#
#     with caplog.at_level(logging.DEBUG):
#         issues = fetch_all_issues(mock_repo, None)
#
#     assert 1 == len(issues)
#     assert 1 == issues[0].number
#     assert "Issue 1" == issues[0].title
#     assert ["bug"] == issues[0].labels
#     assert "Found 1 issues for test/repo" in caplog.text
#
#
# # fetch_finished_pull_requests
#
# def test_fetch_finished_pull_requests_multiple_pulls(caplog):
#     mock_label_1 = Mock()
#     mock_label_1.name = "bug"
#     mock_label_2 = Mock()
#     mock_label_2.name = "enhancement"
#
#     mock_pull1 = Mock(spec=GithubPullRequest)
#     mock_pull1.number = 1
#     mock_pull1.title = "PR 1"
#     mock_pull1.body = "Dummy body\n\nRelease notes:\n- First release note\n- Second release note"
#     mock_pull1.state = "closed"
#     mock_pull1.created_at = datetime(2023, 1, 1)
#     mock_pull1.updated_at = datetime(2023, 1, 2)
#     mock_pull1.closed_at = datetime(2023, 1, 3)
#     mock_pull1.merged_at = None
#
#     mock_pull2 = Mock(spec=GithubPullRequest)
#     mock_pull2.id = 2
#     mock_pull2.number = 2
#     mock_pull2.title = "PR 2"
#     mock_pull2.body = "Dummy body"
#     mock_pull2.state = "closed"
#     mock_pull2.created_at = datetime(2023, 1, 5)
#     mock_pull2.updated_at = datetime(2023, 1, 6)
#     mock_pull2.closed_at = datetime(2023, 1, 7)
#     mock_pull2.merged_at = None
#
#     mock_repo = Mock(spec=Repository)
#     mock_repo.get_pulls.return_value = [PullRequest(mock_pull1), PullRequest(mock_pull2)]
#     mock_repo.full_name = "test/repo"
#
#     with caplog.at_level(logging.DEBUG):
#         pull_requests = fetch_finished_pull_requests(mock_repo)
#
#     assert 2 == len(pull_requests)
#     assert 1 == pull_requests[0].number
#     assert "PR 1" == pull_requests[0].title
#     assert 2 == pull_requests[1].number
#     assert "PR 2" == pull_requests[1].title
#     assert "Found 2 PRs for test/repo" in caplog.text
#
#
# # generate_change_url
#
# def test_generate_change_url_with_release(caplog):
#     mock_release = Mock(spec=GitRelease)
#     mock_release.tag_name = "v1.0.0"
#
#     mock_repo = Mock(spec=Repository)
#     mock_repo.full_name = "owner/repo"
#
#     tag_name = "v1.1.0"
#     expected_url = f"https://github.com/owner/repo/compare/v1.0.0...v1.1.0"
#
#     with caplog.at_level(logging.DEBUG):
#         url = generate_change_url(mock_repo, mock_release, tag_name)
#
#     assert expected_url == url
#     assert f"Changelog URL: {expected_url}" in caplog.text
#
#
# def test_generate_change_url_without_release(caplog):
#     mock_repo = Mock(spec=Repository)
#     mock_repo.full_name = "owner/repo"
#
#     tag_name = "v1.1.0"
#     expected_url = f"https://github.com/owner/repo/commits/v1.1.0"
#
#     with caplog.at_level(logging.DEBUG):
#         url = generate_change_url(mock_repo, None, tag_name)
#
#     assert expected_url == url
#     assert f"Changelog URL: {expected_url}" in caplog.text
#
#
# # show_rate_limit
#
# def test_show_rate_limit_not_reached(caplog):
#     mock_core_rate = Mock(spec=Rate)
#     mock_core_rate.remaining = 15
#     mock_core_rate.limit = 60
#
#     mock_rate_limit = Mock(spec=RateLimit)
#     mock_rate_limit.core = mock_core_rate
#
#     mock_github = Mock(spec=Github)
#     mock_github.get_rate_limit.return_value = mock_rate_limit
#
#     with caplog.at_level(logging.DEBUG):
#         show_rate_limit(mock_github)
#
#     assert "Rate limit: 15 remaining of 60" in caplog.text
#
#
# @patch("time.sleep", return_value=None)
# def test_show_rate_limit_reached(mock_sleep, caplog):
#     mock_core_rate = Mock(spec=Rate)
#     mock_core_rate.remaining = 5
#     mock_core_rate.limit = 60
#     mock_core_rate.reset = datetime.utcnow() + timedelta(minutes=5)
#
#     mock_rate_limit = Mock(spec=RateLimit)
#     mock_rate_limit.core = mock_core_rate
#
#     mock_github = Mock(spec=Github)
#     mock_github.get_rate_limit.return_value = mock_rate_limit
#
#     with caplog.at_level(logging.DEBUG):
#         show_rate_limit(mock_github)
#
#     assert "Rate limit reached. Sleeping for " in caplog.text
#     assert mock_sleep.called


if __name__ == '__main__':
    pytest.main()
