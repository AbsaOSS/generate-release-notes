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

from release_notes_generator.utils.gh_action import get_action_input, set_action_output, set_action_failed


# get_input

def test_get_input_with_hyphen(mocker):
    mock_getenv = mocker.patch('os.getenv', return_value='test_value')

    result = get_action_input('test-input', default=None)

    mock_getenv.assert_called_with('INPUT_TEST_INPUT', default=None)
    assert 'test_value' == result


def test_get_input_without_hyphen(mocker):
    mock_getenv = mocker.patch('os.getenv', return_value='another_test_value')

    result = get_action_input('anotherinput', default=None)

    mock_getenv.assert_called_with('INPUT_ANOTHERINPUT', default=None)
    assert 'another_test_value' == result


# set_output

def test_set_output_default(mocker):
    mocker.patch('os.getenv', return_value='default_output.txt')
    mock_open = mocker.patch('builtins.open', new_callable=mocker.mock_open)

    set_action_output('test-output', 'test_value')

    mock_open.assert_called_with('default_output.txt', 'a', encoding='utf-8')
    handle = mock_open()
    handle.write.assert_any_call('test-output<<EOF\n')
    handle.write.assert_any_call('test_value')
    handle.write.assert_any_call('EOF\n')


def test_set_output_custom_path(mocker):
    mocker.patch('os.getenv', return_value='custom_output.txt')
    mock_open = mocker.patch('builtins.open', new_callable=mocker.mock_open)

    set_action_output('custom-output', 'custom_value', 'default_output.txt')

    mock_open.assert_called_with('custom_output.txt', 'a', encoding='utf-8')
    handle = mock_open()
    handle.write.assert_any_call('custom-output<<EOF\n')
    handle.write.assert_any_call('custom_value')
    handle.write.assert_any_call('EOF\n')


def test_set_failed(mocker):
    mock_print = mocker.patch('builtins.print', return_value=None)
    mock_exit = mocker.patch('sys.exit', return_value=None)

    set_action_failed('failure message')

    mock_print.assert_called_with('::error::failure message')
    mock_exit.assert_called_with(1)
