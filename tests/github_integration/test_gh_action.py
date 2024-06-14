import pytest

from unittest.mock import patch, mock_open
from github_integration.gh_action import get_input, set_output, set_failed


@patch('os.getenv')
def test_get_input_with_hyphen(mock_getenv):
    mock_getenv.return_value = 'test_value'
    result = get_input('test-input')
    mock_getenv.assert_called_with('INPUT_TEST_INPUT', '')
    assert result == 'test_value'


@patch('os.getenv')
def test_get_input_without_hyphen(mock_getenv):
    mock_getenv.return_value = 'another_test_value'
    result = get_input('anotherinput')
    mock_getenv.assert_called_with('INPUT_ANOTHERINPUT', '')
    assert result == 'another_test_value'


@patch('os.getenv')
@patch('builtins.open', new_callable=mock_open)
def test_set_output_default(mock_open, mock_getenv):
    mock_getenv.return_value = 'default_output.txt'
    set_output('test-output', 'test_value')
    mock_open.assert_called_with('default_output.txt', 'a')
    mock_open().write.assert_called_with('test-output=test_value\n')


@patch('os.getenv')
@patch('builtins.open', new_callable=mock_open)
def test_set_output_env_variable(mock_open, mock_getenv):
    mock_getenv.return_value = 'github_output.txt'
    set_output('test-output', 'test_value')
    mock_open.assert_called_with('github_output.txt', 'a')
    mock_open().write.assert_called_with('test-output=test_value\n')


@patch('builtins.print')
@patch('sys.exit')
def test_set_failed(mock_exit, mock_print):
    set_failed('failure message')
    mock_print.assert_called_with('::error::failure message')
    mock_exit.assert_called_with(1)


if __name__ == '__main__':
    pytest.main()
