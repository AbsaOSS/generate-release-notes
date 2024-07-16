import pytest
from github.PullRequest import PullRequest

from release_notes_generator.utils.pull_reuqest_utils import extract_issue_numbers_from_body


@pytest.fixture
def mock_pr(mocker):
    return mocker.Mock(spec=PullRequest)


# extract_issue_numbers_from_body

def test_extract_issue_numbers_from_body_no_issues(mock_pr):
    mock_pr.body = "This PR does not fix any issues."
    issue_numbers = extract_issue_numbers_from_body(mock_pr)
    assert issue_numbers == []


def test_extract_issue_numbers_from_body_single_issue(mock_pr):
    mock_pr.body = "This PR closes #123."
    issue_numbers = extract_issue_numbers_from_body(mock_pr)
    assert issue_numbers == [123]


def test_extract_issue_numbers_from_body_multiple_issues(mock_pr):
    mock_pr.body = "This PR fixes #123 and resolves #456."
    issue_numbers = extract_issue_numbers_from_body(mock_pr)
    assert issue_numbers == [123, 456]


def test_extract_issue_numbers_from_body_mixed_case_keywords(mock_pr):
    mock_pr.body = "This PR Fixes #123 and Resolves #456."
    issue_numbers = extract_issue_numbers_from_body(mock_pr)
    assert issue_numbers == [123, 456]


def test_extract_issue_numbers_from_body_no_body(mock_pr):
    mock_pr.body = None
    issue_numbers = extract_issue_numbers_from_body(mock_pr)
    assert issue_numbers == []


def test_extract_issue_numbers_from_body_complex_text_with_wrong_syntax(mock_pr):
    mock_pr.body = """
    This PR does a lot:
    - closes #123
    - fixes issue #456
    - resolves the bug in #789
    """
    issue_numbers = extract_issue_numbers_from_body(mock_pr)
    assert issue_numbers == [123]
