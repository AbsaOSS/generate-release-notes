import time

from github import Github

from generator import generate_release_notes, run
from release_notes_generator.model.custom_chapters import CustomChapters


# generate_release_notes tests

def test_generate_release_notes_repository_not_found(mocker):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = None

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 10
    mock_rate_limit.core.reset.timestamp.return_value = time.time() + 3600
    github_mock.get_rate_limit.return_value = mock_rate_limit

    custom_chapters = CustomChapters(print_empty_chapters=True)

    release_notes = generate_release_notes(github_mock, custom_chapters)

    assert release_notes is None


# run tests

def test_run_failure(mocker):
    mock_exit = mocker.patch('sys.exit', return_value=None)

    run()

    mock_exit.assert_called_once()
