import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from github_integration.github_manager import GithubManager
from github_integration.model.commit import Commit
from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.model.record import Record
from release_notes.record_factory import RecordFactory


def setup_no_issues_pulls_commits():
    mock_git_pr1 = Mock()
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
    mock_git_pr1.get_labels = Mock(return_value=[])

    mock_git_pr2 = Mock()
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
    mock_git_pr2.get_labels = Mock(return_value=[])

    mock_git_commit1 = Mock()
    mock_git_commit1.sha = "abc123"
    mock_git_commit1.commit.message = "Commit message 1"
    mock_git_commit1.author.login = "author1"

    mock_git_commit2 = Mock()
    mock_git_commit2.sha = "def456"
    mock_git_commit2.commit.message = "Commit message 2"
    mock_git_commit2.author.login = "author2"

    # Creating Issue, PullRequest, and Commit instances
    pr1 = PullRequest(mock_git_pr1)
    pr2 = PullRequest(mock_git_pr2)

    commit1 = Commit(mock_git_commit1)
    commit2 = Commit(mock_git_commit2)

    return pr1, pr2, commit1, commit2


def setup_issues_no_pulls_no_commits():
    # Mock GitHub API objects
    mock_git_issue1 = Mock()
    mock_git_issue1.id = 1
    mock_git_issue1.number = 1
    mock_git_issue1.title = "Issue 1"
    mock_git_issue1.body = "Body of issue 1"
    mock_git_issue1.state = "open"
    mock_git_issue1.created_at = datetime.now()

    mock_git_issue2 = Mock()
    mock_git_issue2.id = 2
    mock_git_issue2.number = 2
    mock_git_issue2.title = "Issue 2"
    mock_git_issue2.body = "Body of issue 2"
    mock_git_issue2.state = "closed"
    mock_git_issue2.created_at = datetime.now()

    # Creating Issue, PullRequest, and Commit instances
    issue1 = Issue(mock_git_issue1)
    issue2 = Issue(mock_git_issue2)

    return issue1, issue2


def setup_issues_pulls_commits():
    # Mock GitHub API objects
    mock_git_issue1 = Mock()
    mock_git_issue1.id = 1
    mock_git_issue1.number = 1
    mock_git_issue1.title = "Issue 1"
    mock_git_issue1.body = "Body of issue 1"
    mock_git_issue1.state = "open"
    mock_git_issue1.created_at = datetime.now()

    mock_git_issue2 = Mock()
    mock_git_issue2.id = 2
    mock_git_issue2.number = 2
    mock_git_issue2.title = "Issue 2"
    mock_git_issue2.body = "Body of issue 2"
    mock_git_issue2.state = "closed"
    mock_git_issue2.created_at = datetime.now()

    mock_git_pr1 = Mock()
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
    mock_git_pr1.get_labels = Mock(return_value=[])

    mock_git_pr2 = Mock()
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
    mock_git_pr2.get_labels = Mock(return_value=[])

    mock_git_commit1 = Mock()
    mock_git_commit1.sha = "abc123"
    mock_git_commit1.commit.message = "Commit message 1"
    mock_git_commit1.author.login = "author1"

    mock_git_commit2 = Mock()
    mock_git_commit2.sha = "def456"
    mock_git_commit2.commit.message = "Commit message 2"
    mock_git_commit2.author.login = "author2"

    # Creating Issue, PullRequest, and Commit instances
    issue1 = Issue(mock_git_issue1)
    issue2 = Issue(mock_git_issue2)

    pr1 = PullRequest(mock_git_pr1)
    pr2 = PullRequest(mock_git_pr2)

    commit1 = Commit(mock_git_commit1)
    commit2 = Commit(mock_git_commit2)

    return issue1, issue2, pr1, pr2, commit1, commit2


def test_generate_with_issues_and_pulls_and_commits():
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits()
    issues = [issue1, issue2]
    pulls = [pr1, pr2]
    commits = [commit1, commit2]

    records = RecordFactory.generate(issues, pulls, commits)

    # Check if records for issues and PRs were created
    assert 1 in records
    assert 2 in records

    # Verify the record creation
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)

    # Verify that PRs are registered
    assert 1 == records[1].pulls_count
    assert 1 == records[2].pulls_count

    assert pr1 == records[1].pull_request(0)
    assert pr2 == records[2].pull_request(0)

    # Verify that commits are registered
    assert 1 == records[1].pull_request(0).commits_count()
    assert 1 == records[2].pull_request(0).commits_count()


def test_generate_with_missing_issues():
    issue1, issue2, pr1, pr2, commit1, commit2 = setup_issues_pulls_commits()
    issues = [issue1]
    pulls = [pr1, pr2]  # PR linked to a non-fetched issues (due to since condition)

    with patch.object(GithubManager(), 'fetch_issue', return_value=issue2):
        records = RecordFactory.generate(issues, pulls, [])

    # Verify the record creation
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)

    # Verify that PRs are registered
    assert 1 == records[1].pulls_count
    assert 1 == records[2].pulls_count

    assert pr1 == records[1].pull_request(0)
    assert pr2 == records[2].pull_request(0)

    # Verify that commits are registered
    assert 0 == records[1].pull_request(0).commits_count()
    assert 0 == records[2].pull_request(0).commits_count()


def test_generate_with_no_issues():
    pr1, pr2, commit1, commit2 = setup_no_issues_pulls_commits()
    pulls = [pr1, pr2]
    commits = [commit1, commit2]

    records = RecordFactory.generate([], pulls, commits)

    # Verify the record creation
    assert isinstance(records[101], Record)
    assert isinstance(records[102], Record)

    # Verify that PRs are registered
    assert 1 == records[101].pulls_count
    assert 1 == records[102].pulls_count

    assert pr1 == records[101].pull_request(0)
    assert pr2 == records[102].pull_request(0)

    # Verify that commits are registered
    assert 1 == records[101].pull_request(0).commits_count()
    assert 1 == records[102].pull_request(0).commits_count()


def test_generate_with_no_pulls():
    issue1, issue2 = setup_issues_no_pulls_no_commits()
    issues = [issue1, issue2]

    records = RecordFactory.generate(issues, [], [])

    # Verify the record creation
    assert isinstance(records[1], Record)
    assert isinstance(records[2], Record)

    # Verify that PRs are registered
    assert 0 == records[1].pulls_count
    assert 0 == records[2].pulls_count


if __name__ == '__main__':
    pytest.main()
