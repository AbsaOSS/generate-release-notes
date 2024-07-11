import pytest
from unittest.mock import Mock

from utils.pull_reuqest_utils import extract_issue_numbers_from_body


@pytest.fixture
def pr_mock():
    return Mock()


# extract_issue_numbers_from_body

def test_extract_issue_numbers_from_body_no_issues(pr_mock):
    pr_mock.body = "This PR does not fix any issues."
    issue_numbers = extract_issue_numbers_from_body(pr_mock)
    assert issue_numbers == []


def test_extract_issue_numbers_from_body_single_issue(pr_mock):
    pr_mock.body = "This PR closes #123."
    issue_numbers = extract_issue_numbers_from_body(pr_mock)
    assert issue_numbers == [123]


def test_extract_issue_numbers_from_body_multiple_issues(pr_mock):
    pr_mock.body = "This PR fixes #123 and resolves #456."
    issue_numbers = extract_issue_numbers_from_body(pr_mock)
    assert issue_numbers == [123, 456]


def test_extract_issue_numbers_from_body_mixed_case_keywords(pr_mock):
    pr_mock.body = "This PR Fixes #123 and Resolves #456."
    issue_numbers = extract_issue_numbers_from_body(pr_mock)
    assert issue_numbers == [123, 456]


def test_extract_issue_numbers_from_body_no_body(pr_mock):
    pr_mock.body = None
    issue_numbers = extract_issue_numbers_from_body(pr_mock)
    assert issue_numbers == []


def test_extract_issue_numbers_from_body_complex_text_with_wrong_syntax(pr_mock):
    pr_mock.body = """
    This PR does a lot:
    - closes #123
    - fixes issue #456
    - resolves the bug in #789
    """
    issue_numbers = extract_issue_numbers_from_body(pr_mock)
    assert issue_numbers == [123]
