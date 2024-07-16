from release_notes_generator.utils.utils import get_change_url


# get_change_url

def test_get_change_url_no_repository():
    url = get_change_url(tag_name="v2.0.0")
    assert url == ""


def test_get_change_url_no_git_release(mock_repo):
    url = get_change_url(tag_name="v1.0.0", repository=mock_repo)
    assert url == "https://github.com/org/repo/commits/v1.0.0"


def test_get_change_url_with_git_release(mock_repo, mock_git_release):
    url = get_change_url(tag_name="v2.0.0", repository=mock_repo, git_release=mock_git_release)
    assert url == "https://github.com/org/repo/compare/v1.0.0...v2.0.0"
