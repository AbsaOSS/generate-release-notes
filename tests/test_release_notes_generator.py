from unittest.mock import patch
import pytest
from release_notes_generator import validate_inputs

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
        patcher = patch(f'release_notes_generator.ActionInputs.{key}', return_value=value)
        patcher.start()
        patchers.append(patcher)
    return patchers


def stop_mocks(patchers):
    for patcher in patchers:
        patcher.stop()


def test_validate_inputs_success():
    patchers = apply_mocks(success_case)
    try:
        validate_inputs()
    finally:
        stop_mocks(patchers)


@pytest.mark.parametrize('method, value, expected_error', failure_cases)
def test_validate_inputs_failure(method, value, expected_error):
    case = success_case.copy()
    case[method] = value
    patchers = apply_mocks(case)
    try:
        with pytest.raises(ValueError, match=expected_error):
            validate_inputs()
    finally:
        stop_mocks(patchers)


if __name__ == '__main__':
    pytest.main()
