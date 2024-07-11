import pytest
from unittest.mock import Mock

from utils.utils import get_change_url


@pytest.fixture
def repo_mock():
    repo = Mock()
    repo.full_name = "test/repo"
    return repo


@pytest.fixture
def git_release_mock():
    release = Mock()
    release.tag_name = "v1.0.0"
    return release


# get_change_url

def test_get_change_url_no_repository():
    url = get_change_url(tag_name="v2.0.0")
    assert url == ""


def test_get_change_url_no_git_release(repo_mock):
    url = get_change_url(tag_name="v1.0.0", repository=repo_mock)
    assert url == "https://github.com/test/repo/commits/v1.0.0"


def test_get_change_url_with_git_release(repo_mock, git_release_mock):
    url = get_change_url(tag_name="v2.0.0", repository=repo_mock, git_release=git_release_mock)
    assert url == "https://github.com/test/repo/compare/v1.0.0...v2.0.0"
