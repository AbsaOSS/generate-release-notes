from unittest.mock import Mock

import pytest
from github.Issue import Issue
from github.Repository import Repository

from release_notes.model.record import Record
from github.PullRequest import PullRequest

from release_notes.record_formatter import RecordFormatter


# TODO: create test fixtures module to share fixtures
class MockLabel:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def mock_issue():
    mock_issue = Mock(spec=Issue)
    mock_issue.number = 123
    mock_issue.title = "Issue Title"
    label1 = Mock(spec=MockLabel)
    label1.name = 'label1'
    label2 = Mock(spec=MockLabel)
    label2.name = 'label2'
    mock_issue.labels = [label1, label2]
    return mock_issue


@pytest.fixture
def mock_pull():
    mock_pull = Mock(spec=PullRequest)
    mock_pull.number = 1
    mock_pull.url = "http://example.com/pull/1"
    mock_pull.title = "Pull Request Title"
    return mock_pull


@pytest.fixture
def mock_repo():
    mock_repo = Mock(spec=Repository)
    mock_repo.full_name = "mock/repo"
    return mock_repo


@pytest.fixture
def record_with_issue(mock_repo, mock_issue):
    return Record(repo=mock_repo, issue=mock_issue)


@pytest.fixture
def record_without_issue(mock_repo, mock_pull):
    rec = Record(mock_repo)
    rec.register_pull_request(mock_pull)
    return rec


def test_format_record_with_issue(record_with_issue):
    formatter = RecordFormatter()

    formatted = formatter.format(record_with_issue)

    # TODO - known bug will be solve in related Issue
    # expected_output = "- #123 _Issue Title_ implemented by developers in [#1](http://example.com/pull/1)\n  - release notes 1\n  - release notes 2"
    expected_output = "- #123 _Issue Title_ implemented by developers in \n  - release notes 1\n  - release notes 2"

    assert expected_output == formatted


# TODO - following tests could be used when topic will be implemented
# def test_format_record_without_issue(record_without_issue):
#     formatter = RecordFormatter()
#     formatted = formatter.format(record_without_issue)
#     expected_output = "- #1 _Pull Request Title_ implemented by developers in [#1](http://example.com/pull/1), [#2](http://example.com/pull/2)\n  - release notes 1\n  - release notes 2"
#     assert formatted == expected_output
#
#
# def test_format_pulls():
#     formatter = RecordFormatter()
#     pulls = [PullRequest(number=1, url="http://example.com/pull/1"), PullRequest(number=2, url="http://example.com/pull/2")]
#     formatted_pulls = formatter._format_pulls(pulls)
#     expected_output = "[#1](http://example.com/pull/1), [#2](http://example.com/pull/2)"
#     assert formatted_pulls == expected_output
#
#
# def test_format_developers(record_with_issue):
#     formatter = RecordFormatter()
#     developers = formatter._format_developers(record_with_issue)
#     assert developers == "developers"
#
#
# def test_format_release_note_rows(record_with_issue):
#     formatter = RecordFormatter()
#     release_note_rows = formatter._format_release_note_rows(record_with_issue)
#     expected_output = "  - release notes 1\n  - release notes 2"
#     assert release_note_rows == expected_output
