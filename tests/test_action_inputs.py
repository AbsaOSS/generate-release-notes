#
# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from release_notes_generator.action_inputs import ActionInputs

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


def apply_mocks(case, mocker):
    patchers = []
    for key, value in case.items():
        patcher = mocker.patch(f'release_notes_generator.action_inputs.ActionInputs.{key}', return_value=value)
        patcher.start()
        patchers.append(patcher)
    return patchers


def stop_mocks(patchers):
    for patcher in patchers:
        patcher.stop()


def test_validate_inputs_success(mocker):
    patchers = apply_mocks(success_case, mocker)
    try:
        ActionInputs.validate_inputs()
    finally:
        stop_mocks(patchers)


@pytest.mark.parametrize('method, value, expected_error', failure_cases)
def test_validate_inputs_failure(method, value, expected_error, mocker):
    case = success_case.copy()
    case[method] = value
    patchers = apply_mocks(case, mocker)
    try:
        with pytest.raises(ValueError, match=expected_error):
            ActionInputs.validate_inputs()
    finally:
        stop_mocks(patchers)


def test_get_github_repository(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='owner/repo')
    assert 'owner/repo' == ActionInputs.get_github_repository()


def test_get_github_token(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input',
                 return_value='fake-token')
    assert ActionInputs.get_github_token() == 'fake-token'


def test_get_tag_name(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='v1.0.0')
    assert ActionInputs.get_tag_name() == 'v1.0.0'


def test_get_chapters_json(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='{"chapters": []}')
    assert ActionInputs.get_chapters_json() == '{"chapters": []}'


def test_get_warnings(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='true')
    assert ActionInputs.get_warnings() is True


def test_get_published_at(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='false')
    assert ActionInputs.get_published_at() is False


def test_get_skip_release_notes_label(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='')
    assert ActionInputs.get_skip_release_notes_label() == 'skip-release-notes'


def test_get_print_empty_chapters(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='true')
    assert ActionInputs.get_print_empty_chapters() is True


def test_get_chapters_to_pr_without_issue(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='false')
    assert ActionInputs.get_chapters_to_pr_without_issue() is False


def test_get_verbose_verbose_by_action_input(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='true')
    mocker.patch('os.getenv', return_value=0)
    assert ActionInputs.get_verbose() is True


def test_get_verbose_verbose_by_workflow_debug(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='false')
    mocker.patch('os.getenv', return_value=1)
    assert ActionInputs.get_verbose() is True


def test_get_verbose_verbose_by_both(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='true')
    mocker.patch('os.getenv', return_value=1)
    assert ActionInputs.get_verbose() is True


def test_get_verbose_not_verbose(mocker):
    mocker.patch('release_notes_generator.action_inputs.get_action_input', return_value='false')
    mocker.patch('os.getenv', return_value=0)
    assert ActionInputs.get_verbose() is False
