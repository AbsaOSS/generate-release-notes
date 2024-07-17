import time
from datetime import datetime

from github import Github

from release_notes_generator.generator import ReleaseNotesGenerator
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

    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate_release_notes()

    assert release_notes is None


def test_generate_release_notes_latest_release_not_found(mocker, mock_repo, mock_issue_closed_i1_bug,
                                                         mock_pull_closed_with_rls_notes_101, mock_commit):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo
    mock_repo.created_at = datetime.now()
    mock_repo.get_issues.return_value = [mock_issue_closed_i1_bug]
    mock_repo.get_pulls.return_value = [mock_pull_closed_with_rls_notes_101]
    mock_repo.get_commits.return_value = [mock_commit]

    github_mock.get_repo().get_latest_release.return_value = None

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 10
    mock_rate_limit.core.reset.timestamp.return_value = time.time() + 3600
    github_mock.get_rate_limit.return_value = mock_rate_limit

    custom_chapters = CustomChapters(print_empty_chapters=True)

    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate_release_notes()

    assert release_notes is not None
