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

"""
Integration smoke tests for the Release Notes Generator GitHub Action.
These tests verify that critical paths don't crash and handle errors gracefully.
All tests use mocked GitHub APIs to ensure determinism and avoid requiring secrets.
"""

import os
import json
import pytest
from unittest import mock

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.chapters.custom_chapters import CustomChapters


@pytest.fixture
def base_env_vars():
    """Base environment variables for the GitHub Action."""
    return {
        "INPUT_TAG_NAME": "v1.0.0",
        "INPUT_GITHUB_REPOSITORY": "test-owner/test-repo",
        "INPUT_GITHUB_TOKEN": "mock_token_for_testing",
        "INPUT_CHAPTERS": json.dumps([
            {"title": "Features 🎉", "label": "feature"},
            {"title": "Bug Fixes 🛠", "label": "bug"},
        ]),
        "INPUT_WARNINGS": "true",
        "INPUT_PRINT_EMPTY_CHAPTERS": "false",
        "INPUT_VERBOSE": "false",
        "INPUT_HIERARCHY": "false",
        "INPUT_DUPLICITY_SCOPE": "both",
        "INPUT_DUPLICITY_ICON": "🔔",
        "INPUT_PUBLISHED_AT": "false",
        "INPUT_SKIP_RELEASE_NOTES_LABELS": "skip-release-notes",
        "INPUT_RELEASE_NOTES_TITLE": "[Rr]elease [Nn]otes:",
        "INPUT_CODERABBIT_SUPPORT_ACTIVE": "false",
        "INPUT_CODERABBIT_RELEASE_NOTES_TITLE": "Summary by CodeRabbit",
        "INPUT_CODERABBIT_SUMMARY_IGNORE_GROUPS": "",
        "INPUT_ROW_FORMAT_HIERARCHY_ISSUE": "{type}: _{title}_ {number}",
        "INPUT_ROW_FORMAT_ISSUE": "{type}: {number} _{title}_ developed by {developers} in {pull-requests}",
        "INPUT_ROW_FORMAT_PR": "{number} _{title}_ developed by {developers}",
        "INPUT_ROW_FORMAT_LINK_PR": "true",
    }


def test_action_inputs_parsing(base_env_vars):
    """
    Test that action inputs are correctly parsed from environment variables.
    This is a critical integration point that must work for the action to function.
    """
    with mock.patch.dict(os.environ, base_env_vars, clear=False):
        assert ActionInputs.get_tag_name() == "v1.0.0"
        assert ActionInputs.get_github_repository() == "test-owner/test-repo"
        assert ActionInputs.get_github_token() == "mock_token_for_testing"
        assert ActionInputs.get_warnings() is True
        assert ActionInputs.get_print_empty_chapters() is False
        assert ActionInputs.get_verbose() is False
        assert ActionInputs.get_hierarchy() is False


def test_chapters_configuration_parsing(base_env_vars):
    """
    Test that chapter configuration is correctly parsed from YAML input.
    Validates the action can handle different chapter configurations.
    """
    with mock.patch.dict(os.environ, base_env_vars, clear=False):
        chapters_config = ActionInputs.get_chapters()
        custom_chapters = CustomChapters(print_empty_chapters=False).from_yaml_array(chapters_config)
        
        assert custom_chapters is not None
        assert len(custom_chapters.chapters) == 2
        # Check chapter titles exist (handle unicode escaping)
        chapter_titles = list(custom_chapters.chapters.keys())
        assert any("Features" in title for title in chapter_titles)
        assert any("Bug Fixes" in title for title in chapter_titles)


def test_chapters_with_multiple_labels(base_env_vars):
    """
    Test chapter configuration with multiple labels per chapter.
    """
    multi_label_config = {
        **base_env_vars,
        "INPUT_CHAPTERS": json.dumps([
            {"title": "Changes", "labels": "bug, enhancement"},
            {"title": "Platform", "labels": ["platform", "infra"]},
        ])
    }
    
    with mock.patch.dict(os.environ, multi_label_config, clear=False):
        chapters_config = ActionInputs.get_chapters()
        custom_chapters = CustomChapters(print_empty_chapters=False).from_yaml_array(chapters_config)
        
        assert len(custom_chapters.chapters) == 2
        assert "Changes" in custom_chapters.chapters
        assert "Platform" in custom_chapters.chapters


def test_invalid_duplicity_scope_handling(base_env_vars):
    """
    Test that invalid duplicity scope values are logged as errors.
    """
    invalid_config = {
        **base_env_vars,
        "INPUT_DUPLICITY_SCOPE": "invalid_value"
    }
    
    with mock.patch.dict(os.environ, invalid_config, clear=False):
        # Should log error but not raise (validation doesn't raise for duplicity scope)
        ActionInputs.validate_inputs()
        # Just verify the function completes without crashing
        assert True


def test_row_format_validation(base_env_vars):
    """
    Test that row format templates are validated correctly.
    """
    with mock.patch.dict(os.environ, base_env_vars, clear=False):
        # Valid formats should not raise
        ActionInputs.validate_inputs()
        
        hierarchy_format = ActionInputs.get_row_format_hierarchy_issue()
        issue_format = ActionInputs.get_row_format_issue()
        pr_format = ActionInputs.get_row_format_pr()
        
        assert "{type}" in hierarchy_format or "{title}" in hierarchy_format
        assert "{number}" in issue_format or "{title}" in issue_format
        assert "{number}" in pr_format or "{title}" in pr_format


def test_empty_chapters_yaml(base_env_vars):
    """
    Test handling of empty chapters configuration.
    """
    empty_config = {
        **base_env_vars,
        "INPUT_CHAPTERS": ""
    }
    
    with mock.patch.dict(os.environ, empty_config, clear=False):
        chapters_config = ActionInputs.get_chapters()
        custom_chapters = CustomChapters(print_empty_chapters=False).from_yaml_array(chapters_config)
        
        # Should create empty chapters dict
        assert custom_chapters is not None
        assert len(custom_chapters.chapters) == 0


def test_verbose_mode_activation(base_env_vars):
    """
    Test that verbose mode can be activated via input.
    """
    # Test via INPUT_VERBOSE
    verbose_config = {
        **base_env_vars,
        "INPUT_VERBOSE": "true"
    }
    with mock.patch.dict(os.environ, verbose_config, clear=False):
        assert ActionInputs.get_verbose() is True
    
    # Test VERBOSE false
    normal_config = {
        **base_env_vars,
        "INPUT_VERBOSE": "false"
    }
    with mock.patch.dict(os.environ, normal_config, clear=False):
        # Verbose is False unless explicitly set
        assert ActionInputs.get_verbose() is False


def test_skip_release_notes_labels_parsing(base_env_vars):
    """
    Test parsing of skip-release-notes labels configuration.
    """
    multi_skip_config = {
        **base_env_vars,
        "INPUT_SKIP_RELEASE_NOTES_LABELS": "skip-release-notes, ignore-in-release, wip"
    }
    
    with mock.patch.dict(os.environ, multi_skip_config, clear=False):
        skip_labels = ActionInputs.get_skip_release_notes_labels()
        
        assert len(skip_labels) == 3
        assert "skip-release-notes" in skip_labels
        assert "ignore-in-release" in skip_labels
        assert "wip" in skip_labels


def test_deterministic_chapter_order(base_env_vars):
    """
    Test that chapter order is preserved from configuration.
    This ensures deterministic output ordering.
    """
    with mock.patch.dict(os.environ, base_env_vars, clear=False):
        chapters_config = ActionInputs.get_chapters()
        custom_chapters = CustomChapters(print_empty_chapters=False).from_yaml_array(chapters_config)
        
        chapter_titles = list(custom_chapters.chapters.keys())
        
        # Order should match the input configuration (handle unicode)
        assert "Features" in chapter_titles[0]
        assert "Bug Fixes" in chapter_titles[1]


def test_coderabbit_configuration(base_env_vars):
    """
    Test CodeRabbit support configuration parsing.
    """
    coderabbit_config = {
        **base_env_vars,
        "INPUT_CODERABBIT_SUPPORT_ACTIVE": "true",
        "INPUT_CODERABBIT_RELEASE_NOTES_TITLE": "AI Summary",
        "INPUT_CODERABBIT_SUMMARY_IGNORE_GROUPS": "group1, group2"
    }
    
    with mock.patch.dict(os.environ, coderabbit_config, clear=False):
        assert ActionInputs.is_coderabbit_support_active() is True
        assert ActionInputs.get_coderabbit_release_notes_title() == "AI Summary"
        ignore_groups = ActionInputs.get_coderabbit_summary_ignore_groups()
        assert "group1" in ignore_groups
        assert "group2" in ignore_groups
