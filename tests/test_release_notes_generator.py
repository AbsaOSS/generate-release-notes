import unittest
import pytest

from unittest.mock import Mock, patch
from release_notes_generator import validate_inputs, release_notes_generator, run


# validate_inputs

def test_validate_inputs():
    validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, False)

    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', '', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', '', '{"chapter": "content"}', True, False, 'skip', True, False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', 'invalid_json', True, False, 'skip', True, False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', 'not_bool', False, 'skip', True, False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, 'not_bool', 'skip', True, False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, '', True, False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', 'not_bool', False)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, 'not_bool')


# release_notes_generator

def test_release_notes_generator_success(mocker):
    # Mock the dependencies
    g = Mock()
    repository_id = "repo_id"
    tag_name = "v1.0"
    chapters_json = '{"chapters": []}'
    warnings = False
    published_at = False
    skip_release_notes_label = "skip"
    print_empty_chapters = False
    chapters_to_pr_without_issue = False

    mock_repository = Mock()
    mock_release = Mock()
    mock_issues = [Mock()]
    mock_pulls = [Mock()]
    mock_changelog_url = "http://example.com/changelog"
    mock_release_notes = "Release Notes"

    mocker.patch('src.release_notes_generator.get_gh_repository', return_value=mock_repository)
    mocker.patch('src.release_notes_generator.fetch_latest_release', return_value=mock_release)
    mocker.patch('src.release_notes_generator.fetch_closed_issues', return_value=mock_issues)
    mocker.patch('src.release_notes_generator.fetch_finished_pull_requests', return_value=mock_pulls)
    mocker.patch('src.release_notes_generator.generate_change_url', return_value=mock_changelog_url)
    mocker.patch('src.release_notes_generator.show_rate_limit')
    mocker.patch('src.release_notes_generator.ReleaseNotesBuilder.build', return_value=mock_release_notes)

    result = release_notes_generator(g, repository_id, tag_name, chapters_json, warnings, published_at,
                                    skip_release_notes_label, print_empty_chapters, chapters_to_pr_without_issue)

    assert result == mock_release_notes


# run

@patch('os.getenv')
@patch('src.release_notes_generator.get_input')
@patch('src.release_notes_generator.set_failed')
@patch('src.release_notes_generator.release_notes_generator')
def test_run_failed_verbose_true(mock_release_notes_generator, mock_set_failed, mock_get_input, mock_getenv):
    mock_get_input.side_effect = ['github-token', '', 'chapters', 'true', 'true', 'skip-release-notes-label', 'true', 'true', 'true']
    mock_getenv.return_value = 'owner/repo'
    mock_release_notes_generator.return_value = 'Release Notes'

    run()

    mock_get_input.assert_any_call('verbose')
    mock_getenv.assert_called_once_with('GITHUB_REPOSITORY')
    mock_release_notes_generator.assert_not_called()
    mock_set_failed.assert_called_once()


@patch('sys.exit')
def test_run_default_fail(mock_exit):
    run()

    mock_exit.assert_called_once()


if __name__ == '__main__':
    pytest.main()
