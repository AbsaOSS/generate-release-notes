import unittest
from datetime import datetime, timedelta

import pytest

from unittest.mock import Mock, patch
from release_notes_generator import validate_inputs, release_notes_generator, run


# validate_inputs

def test_validate_inputs():
    validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, False, True)

    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', '', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', '', '{"chapter": "content"}', True, False, 'skip', True, False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', 'invalid_json', True, False, 'skip', True, False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', 'not_bool', False, 'skip', True, False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, 'not_bool', 'skip', True, False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, '', True, False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', 'not_bool', False, True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, 'not_bool', True)
    with unittest.TestCase().assertRaises(ValueError):
        validate_inputs('owner', 'repo_name', 'tag_name', '{"chapter": "content"}', True, False, 'skip', True, False, 'not_bool')


if __name__ == '__main__':
    pytest.main()
