import pytest

from unittest.mock import patch, mock_open
from github_integration.gh_action import get_action_input, set_action_output, set_action_failed


# get_input

@patch('os.getenv')
def test_get_input_with_hyphen(mock_getenv):
    mock_getenv.return_value = 'test_value'
    result = get_action_input('test-input')
    mock_getenv.assert_called_with('INPUT_TEST_INPUT', '')
    assert result == 'test_value'


@patch('os.getenv')
def test_get_input_without_hyphen(mock_getenv):
    mock_getenv.return_value = 'another_test_value'
    result = get_action_input('anotherinput')
    mock_getenv.assert_called_with('INPUT_ANOTHERINPUT', '')
    assert result == 'another_test_value'


# set_output

@patch('os.getenv')
@patch('builtins.open', new_callable=mock_open)
def test_set_output_default(mock_open, mock_getenv):
    mock_getenv.return_value = 'default_output.txt'
    set_action_output('test-output', 'test_value')
    mock_open.assert_called_with('default_output.txt', 'a')
    handle = mock_open()
    handle.write.assert_any_call('test-output<<EOF\n')
    handle.write.assert_any_call('test_value')
    handle.write.assert_any_call('EOF\n')


@patch('os.getenv')
@patch('builtins.open', new_callable=mock_open)
def test_set_output_custom_path(mock_open, mock_getenv):
    mock_getenv.return_value = 'custom_output.txt'
    set_action_output('custom-output', 'custom_value', 'default_output.txt')
    mock_open.assert_called_with('custom_output.txt', 'a')
    handle = mock_open()
    handle.write.assert_any_call('custom-output<<EOF\n')
    handle.write.assert_any_call('custom_value')
    handle.write.assert_any_call('EOF\n')


@patch('builtins.print')
@patch('sys.exit')
def test_set_failed(mock_exit, mock_print):
    set_action_failed('failure message')
    mock_print.assert_called_with('::error::failure message')
    mock_exit.assert_called_with(1)


if __name__ == '__main__':
    pytest.main()
