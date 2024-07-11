from unittest.mock import Mock

import pytest
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes.model.chapter import Chapter
from release_notes.model.record import Record
from release_notes.model.service_chapters import ServiceChapters
from utils.constants import Constants


class MockLabel:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def service_chapters():
    return ServiceChapters(
        sort_ascending=True,
        print_empty_chapters=True,
        user_defined_labels=['bug', 'enhancement']
    )


@pytest.fixture
def mock_repo():
    mock_repo = Mock(spec=Repository)
    mock_repo.full_name = 'org/repo'
    return mock_repo


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
def mock_issue_open():
    issue = Mock(spec=Issue)
    issue.state = Constants.ISSUE_STATE_OPEN
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
def record_with_issue_no_pull(mock_repo, mock_issue_closed):
    return Record(repo=mock_repo, issue=mock_issue_closed)


@pytest.fixture
def record_with_open_issue_closed_pull(mock_repo, mock_issue_open, mock_pull):
    rec = Record(repo=mock_repo, issue=mock_issue_open)
    rec.register_pull_request(mock_pull)
    return rec


@pytest.fixture
def record_with_open_issue_no_pull(mock_repo, mock_issue_open, mock_pull):
    rec = Record(repo=mock_repo, issue=mock_issue_open)
    return rec


@pytest.fixture
def record_without_issue_only_pull_merged(mock_repo, mock_pull):
    rec = Record(repo=mock_repo)
    rec.register_pull_request(mock_pull)
    return rec


@pytest.fixture
def record_without_issue_only_pull_merged_with_issue_mentions(mock_repo, mock_pull):
    rec = Record(repo=mock_repo)
    rec.register_pull_request(mock_pull)
    mock_pull.body = "Release notes:\n- Fixed bug\n- Improved performance\n\nFixes #123"
    return rec


@pytest.fixture
def record_without_issue_only_pull_closed(mock_repo, mock_pull):
    rec = Record(repo=mock_repo)
    rec.register_pull_request(mock_pull)
    mock_pull.merged_at = None
    mock_pull.closed_at = Mock()
    return rec


# __init__

def test_initialization(service_chapters):
    assert service_chapters.sort_ascending is True
    assert service_chapters.print_empty_chapters is True
    assert service_chapters.user_defined_labels == ['bug', 'enhancement']
    assert isinstance(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS], Chapter)


# populate

def test_populate_closed_issue(service_chapters, record_with_issue_no_pull):
    service_chapters.populate({1: record_with_issue_no_pull})

    assert 1 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 1 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)


def test_populate_merged_pr(service_chapters, record_without_issue_only_pull_merged):
    service_chapters.populate({2: record_without_issue_only_pull_merged})

    assert 1 == len(service_chapters.chapters[service_chapters.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)


def test_populate_closed_pr(service_chapters, record_without_issue_only_pull_closed):
    service_chapters.populate({2: record_without_issue_only_pull_closed})

    assert 1 == len(service_chapters.chapters[service_chapters.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)


def test_populate_not_closed_issue(service_chapters, record_with_open_issue_closed_pull):
    service_chapters.populate({1: record_with_open_issue_closed_pull})
    print(service_chapters.to_string())

    assert 1 == len(service_chapters.chapters[service_chapters.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)


def test_populate_not_closed_issue_without_pull(service_chapters, record_with_open_issue_no_pull):
    service_chapters.populate({1: record_with_open_issue_no_pull})
    print(service_chapters.to_string())

    assert 0 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.OTHERS_NO_TOPIC].rows)


def test_populate_no_issue_with_pull(service_chapters, record_without_issue_only_pull_merged_with_issue_mentions):
    service_chapters.populate({1: record_without_issue_only_pull_merged_with_issue_mentions})
    print(service_chapters.to_string())

    assert 1 == len(service_chapters.chapters[service_chapters.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)
