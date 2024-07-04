from unittest.mock import patch
import pytest

from action.action_inputs import ActionInputs

# Data-driven test cases
success_case = {
    'get_github_repository': 'owner/repo_name',
    'get_tag_name': 'tag_name',
    'get_chapters_json': '{"chapter": "content"}',
    'get_warnings': True,
    'get_published_at': False,
    'get_skip_release_notes_label': 'skip',
    'get_print_empty_chapters': True,
    'get_chapters_to_pr_without_issue': False,
    'get_verbose': True,
}

failure_cases = [
    ('get_github_repository', '', "Owner must be a non-empty string."),
    ('get_github_repository', 'owner/', "Repo name must be a non-empty string."),
    ('get_tag_name', '', "Tag name must be a non-empty string."),
    ('get_chapters_json', 'invalid_json', "Chapters JSON must be a valid JSON string."),
    ('get_warnings', 'not_bool', "Warnings must be a boolean."),
    ('get_published_at', 'not_bool', "Published at must be a boolean."),
    ('get_skip_release_notes_label', '', "Skip release notes label must be a non-empty string."),
    ('get_print_empty_chapters', 'not_bool', "Print empty chapters must be a boolean."),
    ('get_chapters_to_pr_without_issue', 'not_bool', "Chapters to PR without issue must be a boolean."),
    ('get_verbose', 'not_bool', "Verbose logging must be a boolean."),
]


def apply_mocks(case):
    patchers = []
    for key, value in case.items():
        patcher = patch(f'action.action_inputs.ActionInputs.{key}', return_value=value)
        patcher.start()
        patchers.append(patcher)
    return patchers


def stop_mocks(patchers):
    for patcher in patchers:
        patcher.stop()


def test_validate_inputs_success():
    patchers = apply_mocks(success_case)
    try:
        ActionInputs.validate_inputs()
    finally:
        stop_mocks(patchers)


@pytest.mark.parametrize('method, value, expected_error', failure_cases)
def test_validate_inputs_failure(method, value, expected_error):
    case = success_case.copy()
    case[method] = value
    patchers = apply_mocks(case)
    try:
        with pytest.raises(ValueError, match=expected_error):
            ActionInputs.validate_inputs()
    finally:
        stop_mocks(patchers)


@patch('action.action_inputs.get_action_input', return_value='owner/repo_name')
def test_get_github_repository(mock_get_action_input):
    assert ActionInputs.get_github_repository() == 'owner/repo_name'


@patch('action.action_inputs.get_action_input', return_value='token')
def test_get_github_token(mock_get_action_input):
    assert ActionInputs.get_github_token() == 'token'


@patch('action.action_inputs.get_action_input', return_value='v1.0.0')
def test_get_tag_name(mock_get_action_input):
    assert ActionInputs.get_tag_name() == 'v1.0.0'


@patch('action.action_inputs.get_action_input', return_value='{"chapter": "content"}')
def test_get_chapters_json(mock_get_action_input):
    assert ActionInputs.get_chapters_json() == '{"chapter": "content"}'


@patch('action.action_inputs.get_action_input', return_value='true')
def test_get_warnings(mock_get_action_input):
    assert ActionInputs.get_warnings() is True


@patch('action.action_inputs.get_action_input', return_value='true')
def test_get_published_at(mock_get_action_input):
    assert ActionInputs.get_published_at() is True


@patch('action.action_inputs.get_action_input', return_value='skip')
def test_get_skip_release_notes_label(mock_get_action_input):
    assert ActionInputs.get_skip_release_notes_label() == 'skip'


@patch('action.action_inputs.get_action_input', return_value='true')
def test_get_print_empty_chapters(mock_get_action_input):
    assert ActionInputs.get_print_empty_chapters() is True


@patch('action.action_inputs.get_action_input', return_value='true')
def test_get_chapters_to_pr_without_issue(mock_get_action_input):
    assert ActionInputs.get_chapters_to_pr_without_issue() is True


@patch('action.action_inputs.get_action_input', return_value='true')
def test_get_verbose(mock_get_action_input):
    assert ActionInputs.get_verbose() is True


if __name__ == '__main__':
    pytest.main()
