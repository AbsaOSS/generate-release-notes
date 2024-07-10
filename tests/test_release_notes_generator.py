import pytest
from unittest.mock import Mock, patch

from github import Github

from release_notes.model.custom_chapters import CustomChapters
from release_notes_generator import generate_release_notes, run


@pytest.fixture
def mock_github_manager():
    with patch('github_integration.github_manager.GithubManager', autospec=True) as mock_manager:
        instance = mock_manager.return_value
        yield instance


# generate_release_notes tests

def test_generate_release_notes_repository_not_found(mock_github_manager):
    github_mock = Mock(spec=Github)
    github_mock.get_repo.return_value = None

    custom_chapters = CustomChapters(print_empty_chapters=True)

    with patch('github_integration.github_manager.GithubManager', return_value=mock_github_manager):
        release_notes = generate_release_notes(github_mock, custom_chapters)

    assert release_notes is None


# run tests

def test_run_failure(mock_github_manager):
    with patch('sys.exit') as mock_exit:
        run()

        mock_exit.assert_called_once()


if __name__ == '__main__':
    pytest.main()
