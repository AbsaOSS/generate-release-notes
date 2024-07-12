import logging

import pytest

from unittest.mock import Mock, patch

from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit

from release_notes.model.record import Record
from utils.constants import Constants


class MockLabel:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def mock_repo():
    return Mock(spec=Repository)


@pytest.fixture
def mock_issue_open():
    issue = Mock(spec=Issue)
    issue.state = Constants.ISSUE_STATE_OPEN
    label1 = Mock(spec=MockLabel)
    label1.name = 'label1'
    label2 = Mock(spec=MockLabel)
    label2.name = 'label2'
    issue.labels = [label1, label2]
    issue.number = 122
    return issue


@pytest.fixture
def mock_issue_closed():
    issue = Mock(spec=Issue)
    issue.state = Constants.ISSUE_STATE_CLOSED
    label1 = Mock(spec=MockLabel)
    label1.name = 'label1'
    label2 = Mock(spec=MockLabel)
    label2.name = 'label2'
    issue.labels = [label1, label2]
    issue.title = 'Fix the bug'
    issue.number = 122
    return issue


@pytest.fixture
def mock_pull():
    pull = Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = "Release notes:\n- Fixed bug\n- Improved performance\n"
    label1 = Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 123
    pull.merge_commit_sha = 'merge_commit_sha'
    pull.title = 'Fixed bug'
    return pull


@pytest.fixture
def mock_pull_no_rls_notes():
    pull = Mock(spec=PullRequest)
    pull.state = Constants.PR_STATE_CLOSED
    pull.body = None
    label1 = Mock(spec=MockLabel)
    label1.name = 'label1'
    pull.labels = [label1]
    pull.number = 123
    pull.title = 'Fixed bug'
    return pull


@pytest.fixture
def record_with_issue_open(mock_repo, mock_issue_open):
    return Record(repo=mock_repo, issue=mock_issue_open)


@pytest.fixture
def record_with_issue_closed(mock_repo, mock_issue_closed, mock_pull):
    rec = Record(repo=mock_repo, issue=mock_issue_closed)
    rec.register_pull_request(mock_pull)
    mock_repo.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_issue_closed_no_rls_notes(mock_repo, mock_issue_closed, mock_pull):
    rec = Record(repo=mock_repo, issue=mock_issue_closed)
    rec.register_pull_request(mock_pull)
    mock_pull.body = "Fixed bug"
    mock_repo.full_name = 'org/repo'
    return rec


@pytest.fixture
def record_with_pull_closed(mock_repo, mock_pull):
    record = Record(repo=mock_repo)
    mock_repo.full_name = 'org/repo'
    record.register_pull_request(mock_pull)
    return record


@pytest.fixture
def record_with_pull_closed_no_rls_notes(mock_repo, mock_pull_no_rls_notes):
    record = Record(repo=mock_repo)
    record.register_pull_request(mock_pull_no_rls_notes)
    return record


# cover property methods - simple ones
def test_record_properties_with_issue_open(mock_issue_open, record_with_issue_open):
    assert mock_issue_open == record_with_issue_open.issue
    assert record_with_issue_open.is_issue
    assert not record_with_issue_open.is_pr
    assert record_with_issue_open.is_open_issue
    mock_issue_open.state = Constants.ISSUE_STATE_CLOSED
    assert record_with_issue_open.is_closed_issue
    assert record_with_issue_open.is_closed
    assert not record_with_issue_open.is_merged_pr
    assert ['label1', 'label2'] == record_with_issue_open.labels
    assert 0 == record_with_issue_open.pulls_count
    assert record_with_issue_open.pr_links is None
    assert record_with_issue_open.pull_request() is None
    assert 122 == record_with_issue_open.number


def test_record_properties_with_pull(mock_pull, record_with_pull_closed):
    assert [mock_pull] == record_with_pull_closed.pulls
    assert not record_with_pull_closed.is_present_in_chapters
    record_with_pull_closed.increment_present_in_chapters()
    assert record_with_pull_closed.is_present_in_chapters
    assert record_with_pull_closed.is_pr
    assert not record_with_pull_closed.is_issue
    mock_pull.state = Constants.PR_STATE_CLOSED
    assert record_with_pull_closed.is_closed
    mock_pull.merged_at = Mock()
    mock_pull.closed_at = Mock()
    assert record_with_pull_closed.is_merged_pr
    assert ['label1'] == record_with_pull_closed.labels
    assert record_with_pull_closed.pull_request(index=5) is None
    assert mock_pull == record_with_pull_closed.pull_request()
    assert 123 == record_with_pull_closed.number


# authors & contributors - not supported now by code
def test_record_properties_authors_contributors(record_with_pull_closed):
    assert record_with_pull_closed.authors is None
    assert record_with_pull_closed.contributors is None


# get_rls_notes

def test_get_rls_notes(record_with_pull_closed):
    expected_notes = "  - Fixed bug\n  - Improved performance"
    assert record_with_pull_closed.get_rls_notes == expected_notes


# contains_release_notes

def test_contains_release_notes_success(record_with_pull_closed):
    assert record_with_pull_closed.contains_release_notes
    assert record_with_pull_closed.contains_release_notes


def test_contains_release_notes_fail(record_with_pull_closed_no_rls_notes):
    assert not record_with_pull_closed_no_rls_notes.contains_release_notes


# pr_contains_issue_mentions

@patch('release_notes.model.record.extract_issue_numbers_from_body')
def test_pr_contains_issue_mentions(mock_extract_issue_numbers_from_body, record_with_pull_closed):
    mock_extract_issue_numbers_from_body.return_value = [123]
    assert record_with_pull_closed.pr_contains_issue_mentions

    mock_extract_issue_numbers_from_body.return_value = []
    assert not record_with_pull_closed.pr_contains_issue_mentions


# pr_links

def test_pr_links(record_with_pull_closed):
    expected_links = "[#123](https://github.com/org/repo/pull/123)"
    assert record_with_pull_closed.pr_links == expected_links


# register_commit

def test_register_commit_success(record_with_pull_closed):
    commit = Mock(spec=Commit)
    commit.sha = "merge_commit_sha"
    record_with_pull_closed.register_commit(commit)
    assert commit in record_with_pull_closed._Record__pull_commits[123]


def test_register_commit_failure(record_with_pull_closed, caplog):
    commit = Mock(spec=Commit)
    commit.sha = "unknown_sha"
    with caplog.at_level(logging.ERROR):
        record_with_pull_closed.register_commit(commit)
        assert f"Commit {commit.sha} not registered in any PR of record 123" in caplog.text


# to_chapter_row

def test_to_chapter_row_with_pull(record_with_pull_closed):
    expected_row = "PR: #123 _Fixed bug_\n  - Fixed bug\n  - Improved performance"
    assert expected_row == record_with_pull_closed.to_chapter_row()


def test_to_chapter_row_with_issue(record_with_issue_closed):
    expected_row = "#122 _Fix the bug_ in [#123](https://github.com/org/repo/pull/123)\n  - Fixed bug\n  - Improved performance"
    assert expected_row == record_with_issue_closed.to_chapter_row()


def test_to_chapter_row_with_pull_no_rls_notes(record_with_pull_closed_no_rls_notes):
    expected_row = "PR: #123 _Fixed bug_"
    assert expected_row == record_with_pull_closed_no_rls_notes.to_chapter_row()


def test_to_chapter_row_with_issue_no_rls_notes(record_with_issue_closed_no_rls_notes):
    expected_row = "#122 _Fix the bug_ in [#123](https://github.com/org/repo/pull/123)"
    assert expected_row == record_with_issue_closed_no_rls_notes.to_chapter_row()


# contains_labels

def test_contains_labels_with_issue(record_with_issue_open):
    # Test with labels present in the issue
    assert record_with_issue_open.contains_min_one_label(['label1'])
    assert record_with_issue_open.contains_min_one_label(['label2'])
    assert record_with_issue_open.contains_min_one_label(['label1', 'label2'])

    # Test with labels not present in the issue
    assert not record_with_issue_open.contains_min_one_label(['label3'])
    assert record_with_issue_open.contains_min_one_label(['label1', 'label3'])
    assert not record_with_issue_open.contain_all_labels(['label1', 'label3'])


def test_contains_labels_with_pull(mock_pull, record_with_pull_closed):
    # Test with labels present in the pull request
    assert record_with_pull_closed.contains_min_one_label(['label1'])

    # Test with labels not present in the pull request
    assert not record_with_pull_closed.contains_min_one_label(['label2'])
    assert record_with_pull_closed.contains_min_one_label(['label1', 'label2'])
    assert not record_with_pull_closed.contain_all_labels(['label1', 'label2'])


# present_in_chapters

def test_present_in_chapters_initial(record_with_pull_closed):
    # Test initial value
    assert record_with_pull_closed.present_in_chapters() == 0


def test_present_in_chapters_increment(record_with_pull_closed):
    # Test after increment
    record_with_pull_closed.increment_present_in_chapters()
    assert record_with_pull_closed.present_in_chapters() == 1
    record_with_pull_closed.increment_present_in_chapters()
    assert record_with_pull_closed.present_in_chapters() == 2


# is_commit_sha_present

def test_is_commit_sha_present_true(record_with_pull_closed):
    # Test with a commit SHA that is present
    assert record_with_pull_closed.is_commit_sha_present('merge_commit_sha')


def test_is_commit_sha_present_false(record_with_pull_closed):
    # Test with a commit SHA that is not present
    assert not record_with_pull_closed.is_commit_sha_present('unknown_sha')
