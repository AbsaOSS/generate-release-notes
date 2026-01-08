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

import logging
import pytest
from release_notes_generator.action_inputs import ActionInputs

success_case = {
    "get_github_repository": "owner/repo_name",
    "get_tag_name": "tag_name",
    "get_from_tag_name": "from_tag_name",
    "get_chapters": [{"title": "Title", "label": "Label"}],
    "get_hierarchy": False,
    "get_duplicity_scope": "custom",
    "get_duplicity_icon": "\U0001f501",
    "get_warnings": True,
    "get_published_at": False,
    "get_skip_release_notes_labels": ["skip"],
    "get_print_empty_chapters": True,
    "get_verbose": True,
    "get_release_notes_title": "Success value",
    "is_coderabbit_support_active": "true",
    "get_coderabbit_release_notes_title": "Another Success value",
    "get_coderabbit_summary_ignore_groups": "",
}

failure_cases = [
    ("get_github_repository", "", "Owner and Repo must be a non-empty string."),
    ("get_github_repository", "owner/", "Owner and Repo must be a non-empty string."),
    ("get_tag_name", "", "Tag name must be a non-empty string."),
    ("get_from_tag_name", 1, "From tag name must be a string."),
    ("get_chapters", [], "Chapters must be a valid yaml array and not empty."),
    ("get_warnings", "not_bool", "Warnings must be a boolean."),
    ("get_published_at", "not_bool", "Published at must be a boolean."),
    ("get_print_empty_chapters", "not_bool", "Print empty chapters must be a boolean."),
    ("get_verbose", "not_bool", "Verbose logging must be a boolean."),
    ("get_duplicity_icon", "", "Duplicity icon must be a non-empty string and have a length of 1."),
    ("get_duplicity_icon", "Oj", "Duplicity icon must be a non-empty string and have a length of 1."),
    ("get_row_format_issue", "", "Issue row format must be a non-empty string."),
    ("get_row_format_pr", "", "PR Row format must be a non-empty string."),
    ("get_release_notes_title", "", "Release Notes title must be a non-empty string and have non-zero length."),
    ("get_coderabbit_release_notes_title", "", "CodeRabbit Release Notes title must be a non-empty string and have non-zero length."),
    ("get_coderabbit_summary_ignore_groups", [""], "CodeRabbit summary ignore groups must be a non-empty string and have non-zero length."),
    ("get_hidden_service_chapters", [""], "Hidden service chapters must be a non-empty string and have non-zero length."),
    ("get_row_format_link_pr", "not_bool", "'row-format-link-pr' value must be a boolean."),
    ("get_hierarchy", "not_bool", "Hierarchy must be a boolean."),
]

def apply_mocks(case, mocker):
    patchers = []
    for key, value in case.items():
        patcher = mocker.patch(f"release_notes_generator.action_inputs.ActionInputs.{key}", return_value=value)
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
        assert ActionInputs.is_from_tag_name_defined()
    finally:
        stop_mocks(patchers)

@pytest.mark.parametrize("method, value, expected_error", failure_cases)
def test_validate_inputs_failure(method, value, expected_error, mocker):
    case = success_case.copy()
    case[method] = value
    patchers = apply_mocks(case, mocker)
    try:
        mock_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
        mock_exit = mocker.patch("sys.exit")
        ActionInputs.validate_inputs()
        mock_error.assert_called_with(expected_error)
        mock_exit.assert_called_once_with(1)
    finally:
        stop_mocks(patchers)

def test_get_github_repository(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="owner/repo")
    assert "owner/repo" == ActionInputs.get_github_repository()

def test_get_github_token(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="fake-token")
    assert ActionInputs.get_github_token() == "fake-token"

def test_get_tag_name_version_full(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="v1.0.0")
    assert ActionInputs.get_tag_name() == "v1.0.0"

def test_get_tag_name_version_shorted_with_v(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="v1.2")
    assert ActionInputs.get_tag_name() == "v1.2.0"

def test_get_tag_name_version_shorted_no_v(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="1.2")
    assert ActionInputs.get_tag_name() == "v1.2.0"

def test_get_tag_name_empty(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_tag_name() == ""

def test_get_tag_name_invalid_format(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="v1.2.beta")
    with pytest.raises(ValueError) as excinfo:
        ActionInputs.get_tag_name()
    assert "Invalid version tag format: 'v1.2.beta'. Expected vMAJOR.MINOR[.PATCH], e.g. 'v0.2' or 'v0.2.0'." in str(excinfo.value)

def test_get_tag_from_name_version_full(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="v1.0.0")
    assert ActionInputs.get_from_tag_name() == "v1.0.0"

def test_get_from_tag_name_version_shorted_with_v(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="v1.2")
    assert ActionInputs.get_from_tag_name() == "v1.2.0"

def test_get_from_tag_name_version_shorted_no_v(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="1.2")
    assert ActionInputs.get_from_tag_name() == "v1.2.0"

def test_get_from_tag_name_empty(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_from_tag_name() == ""

def test_get_from_tag_name_invalid_format(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="v1.2.beta")
    with pytest.raises(ValueError) as excinfo:
        ActionInputs.get_from_tag_name()
    assert "Invalid version tag format: 'v1.2.beta'. Expected vMAJOR.MINOR[.PATCH], e.g. 'v0.2' or 'v0.2.0'." in str(excinfo.value)

def test_get_chapters_success(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="[{\"title\": \"Title\", \"label\": \"Label\"}]")
    assert ActionInputs.get_chapters() == [{"title": "Title", "label": "Label"}]

def test_get_chapters_exception(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="wrong value")
    assert [] == ActionInputs.get_chapters()

def test_get_chapters_yaml_error(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="[{\"title\": \"Title\" \"label\": \"Label\"}]")
    assert [] == ActionInputs.get_chapters()

def test_get_warnings(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="true")
    assert ActionInputs.get_warnings() is True

def test_get_published_at(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="false")
    assert ActionInputs.get_published_at() is False

def test_get_skip_release_notes_label(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="skip-release-notes")
    assert ActionInputs.get_skip_release_notes_labels() == ["skip-release-notes"]

def test_get_skip_release_notes_label_not_defined(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_skip_release_notes_labels() == ["skip-release-notes"]

def test_get_skip_release_notes_labels(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="skip-release-notes, another-skip-label")
    assert ActionInputs.get_skip_release_notes_labels() == ["skip-release-notes", "another-skip-label"]

def test_get_skip_release_notes_labels_no_space(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="skip-release-notes,another-skip-label")
    assert ActionInputs.get_skip_release_notes_labels() == ["skip-release-notes", "another-skip-label"]

def test_get_print_empty_chapters(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="true")
    assert ActionInputs.get_print_empty_chapters() is True

def test_get_verbose_verbose_by_action_input(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="true")
    mocker.patch("os.getenv", return_value=0)
    assert ActionInputs.get_verbose() is True

def test_get_verbose_verbose_by_workflow_debug(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="false")
    mocker.patch("os.getenv", return_value="1")
    assert ActionInputs.get_verbose() is True

def test_get_verbose_verbose_by_both(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="true")
    mocker.patch("os.getenv", return_value=1)
    assert ActionInputs.get_verbose() is True

def test_get_verbose_not_verbose(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="false")
    mocker.patch("os.getenv", return_value=0)
    assert ActionInputs.get_verbose() is False

def test_get_duplicity_scope_wrong_value(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="huh")
    mock_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    assert ActionInputs.get_duplicity_scope() == "BOTH"
    mock_error.assert_called_with("Error: '%s' is not a valid DuplicityType.", "HUH")

def test_detect_row_format_invalid_keywords_no_invalid_keywords(caplog):
    caplog.set_level(logging.ERROR)
    row_format = "{number} _{title}_ in {pull-requests}"
    ActionInputs._detect_row_format_invalid_keywords(row_format)
    assert len(caplog.records) == 0

def test_detect_row_format_invalid_keywords_with_invalid_keywords(caplog):
    caplog.set_level(logging.ERROR)
    row_format = "{number} _{title}_ in {pull-requests} {invalid_key} {another_invalid}"
    ActionInputs._detect_row_format_invalid_keywords(row_format)
    assert len(caplog.records) == 2
    expected_errors = [
        "Invalid `invalid_key` detected in `Issue` row format keyword(s) found: invalid_key, another_invalid. Will be removed from string.",
        "Invalid `another_invalid` detected in `Issue` row format keyword(s) found: invalid_key, another_invalid. Will be removed from string."
    ]
    actual_errors = [record.getMessage() for record in caplog.records]
    assert actual_errors == expected_errors

def test_get_row_format_hierarchy_issue_cleans_invalid_keywords(mocker, caplog):
    caplog.set_level(logging.ERROR)
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value="{type}: _{title}_ {number} {invalid}",
    )
    fmt = ActionInputs.get_row_format_hierarchy_issue()
    assert "{invalid}" not in fmt

def test_clean_row_format_invalid_keywords_no_keywords():
    expected_row_format = "{number} _{title}_ in {pull-requests}"
    actual_format = ActionInputs._detect_row_format_invalid_keywords(expected_row_format, clean=True)
    assert expected_row_format == actual_format

def test_clean_row_format_invalid_keywords_nested_braces():
    row_format = "{number} _{title}_ in {pull-requests} {invalid_key} {another_invalid}"
    expected_format = "{number} _{title}_ in {pull-requests}  "
    actual_format = ActionInputs._detect_row_format_invalid_keywords(row_format, clean=True)
    assert expected_format == actual_format

def test_release_notes_title_default():
    assert ActionInputs.get_release_notes_title() == "[Rr]elease [Nn]otes:"

def test_release_notes_title_custom(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Custom Title")
    assert ActionInputs.get_release_notes_title() == "Custom Title"

def test_coderabbit_support_active_default(mocker):
    assert not ActionInputs.is_coderabbit_support_active()

def test_coderabbit_release_notes_title_default():
    assert ActionInputs.get_coderabbit_release_notes_title() == "Summary by CodeRabbit"

def test_coderabbit_release_notes_title_custom(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Custom Title")
    assert ActionInputs.get_coderabbit_release_notes_title() == "Custom Title"

def test_coderabbit_summary_ignore_groups_default():
    assert ActionInputs.get_coderabbit_summary_ignore_groups() == []

def test_coderabbit_summary_ignore_groups_custom(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Group1\nGroup2")
    assert ActionInputs.get_coderabbit_summary_ignore_groups() == ["Group1", "Group2"]

def test_coderabbit_summary_ignore_groups_int_input(mocker):
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=1)
    assert ActionInputs.get_coderabbit_summary_ignore_groups() == []
    mock_log_error.assert_called_once()
    assert "coderabbit_summary_ignore_groups' is not a valid string" in mock_log_error.call_args[0][0]

def test_coderabbit_summary_ignore_groups_empty_group_input(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=",")
    # Note: this is not valid input which is catched by the validation_inputs() method
    assert ActionInputs.get_coderabbit_summary_ignore_groups() == ['', '']

def test_get_hidden_service_chapters_default(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_hidden_service_chapters() == []

def test_get_hidden_service_chapters_single_comma_separated(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Direct Commits ⚠️")
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️"]

def test_get_hidden_service_chapters_multiple_comma_separated(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Direct Commits ⚠️, Others - No Topic ⚠️")
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️", "Others - No Topic ⚠️"]

def test_get_hidden_service_chapters_newline_separated(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Direct Commits ⚠️\nOthers - No Topic ⚠️")
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️", "Others - No Topic ⚠️"]

def test_get_hidden_service_chapters_with_extra_whitespace(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="  Direct Commits ⚠️  ,  Others - No Topic ⚠️  ")
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️", "Others - No Topic ⚠️"]

def test_get_hidden_service_chapters_int_input(mocker):
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=123)
    assert ActionInputs.get_hidden_service_chapters() == []
    mock_log_error.assert_called_once()
    assert "hidden-service-chapters' is not a valid string" in mock_log_error.call_args[0][0]

# Mirrored test file for release_notes_generator/generator.py
# Extracted from previous aggregated test_release_notes_generator.py

import time
from datetime import datetime, timedelta
from github import Github
from release_notes_generator.generator import ReleaseNotesGenerator
from release_notes_generator.chapters.custom_chapters import CustomChapters
from release_notes_generator.utils.constants import ROW_FORMAT_ISSUE

def test_generate_release_notes_repository_not_found(mocker):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = None
    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    github_mock.get_rate_limit.return_value = mock_rate_limit
    custom_chapters = CustomChapters(print_empty_chapters=True)
    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()
    assert release_notes is None

def test_generate_release_notes_latest_release_not_found(
    mocker,
    mock_repo,
    mock_issue_closed,
    mock_issue_closed_i1_bug,
    mock_pull_closed_with_rls_notes_101,
    mock_pull_closed_with_rls_notes_102,
    mock_commit,
):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo
    mock_repo.created_at = datetime.now() - timedelta(days=10)
    mock_repo.get_issues.return_value = [mock_issue_closed, mock_issue_closed_i1_bug]
    mock_repo.get_pulls.return_value = [mock_pull_closed_with_rls_notes_101, mock_pull_closed_with_rls_notes_102]
    mock_repo.get_commits.return_value = [mock_commit]
    mock_repo.get_release.return_value = None
    mock_repo.get_releases.return_value = []
    mock_issue_closed.created_at = mock_repo.created_at + timedelta(days=2)
    mock_issue_closed_i1_bug.created_at = mock_repo.created_at + timedelta(days=7)
    mock_issue_closed_i1_bug.closed_at = mock_repo.created_at + timedelta(days=6)
    mock_pull_closed_with_rls_notes_101.merged_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_102.merged_at = mock_repo.created_at + timedelta(days=7)
    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit
    mocker.patch("release_notes_generator.record.factory.default_record_factory.get_issues_for_pr", return_value=None)
    custom_chapters = CustomChapters(print_empty_chapters=True)
    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()
    assert release_notes is not None
    assert "- N/A: #121 _Fix the bug_" in release_notes
    assert "- N/A: #122 _I1+bug_" in release_notes
    assert "- PR: #101 _Fixed bug_" in release_notes
    assert "- PR: #102 _Fixed bug_" in release_notes

def test_generate_release_notes_latest_release_found_by_created_at(
    mocker,
    mock_repo,
    mock_git_release,
    mock_issue_closed_i1_bug,
    mock_pull_closed_with_rls_notes_101,
    mock_pull_closed_with_rls_notes_102,
    mock_commit,
):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo
    mock_repo.created_at = datetime.now() - timedelta(days=10)
    mock_repo.published_at = datetime.now() - timedelta(days=9)
    mock_repo.get_issues.return_value = [mock_issue_closed_i1_bug]
    mock_repo.get_pulls.return_value = [mock_pull_closed_with_rls_notes_101, mock_pull_closed_with_rls_notes_102]
    mock_repo.get_commits.return_value = [mock_commit]
    mock_commit.commit.author.date = mock_repo.created_at + timedelta(days=1)
    mock_repo.get_release.return_value = None
    mock_repo.get_releases.return_value = []
    mock_issue_closed_i1_bug.created_at = mock_repo.created_at + timedelta(days=7)
    mock_issue_closed_i1_bug.closed_at = mock_repo.created_at + timedelta(days=6)
    mock_pull_closed_with_rls_notes_101.merged_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_101.closed_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_102.merged_at = mock_repo.created_at + timedelta(days=7)
    mock_pull_closed_with_rls_notes_102.closed_at = mock_repo.created_at + timedelta(days=7)
    mock_git_release.created_at = mock_repo.created_at + timedelta(days=5)
    mock_git_release.published_at = mock_repo.created_at + timedelta(days=5)
    mocker.patch("release_notes_generator.data.miner.DataMiner.get_latest_release", return_value=mock_git_release)
    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit
    mock_get_action_input = mocker.patch("release_notes_generator.utils.gh_action.get_action_input")
    mock_get_action_input.side_effect = lambda first_arg, **kwargs: (
        "{number} _{title}_ in {pull-requests} {unknown} {another-unknown}" if first_arg == ROW_FORMAT_ISSUE else None
    )
    mocker.patch("release_notes_generator.record.factory.default_record_factory.get_issues_for_pr", return_value=None)
    custom_chapters = CustomChapters(print_empty_chapters=True)
    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()
    assert release_notes is not None
    assert "- N/A: #122 _I1+bug_" in release_notes
    assert "- PR: #101 _Fixed bug_" not in release_notes
    assert "- PR: #102 _Fixed bug_" in release_notes

def test_generate_release_notes_latest_release_found_by_published_at(
    mocker,
    mock_repo,
    mock_git_release,
    mock_issue_closed_i1_bug,
    mock_pull_closed_with_rls_notes_101,
    mock_pull_closed_with_rls_notes_102,
    mock_commit,
):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo
    mock_repo.created_at = datetime.now() - timedelta(days=10)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_published_at", return_value="true")
    mock_repo.get_issues.return_value = [mock_issue_closed_i1_bug]
    mock_repo.get_pulls.return_value = [mock_pull_closed_with_rls_notes_101, mock_pull_closed_with_rls_notes_102]
    mock_repo.get_commits.return_value = [mock_commit]
    mock_commit.commit.author.date = mock_repo.created_at + timedelta(days=1)
    mock_repo.get_release.return_value = None
    mock_repo.get_releases.return_value = []
    mock_issue_closed_i1_bug.created_at = mock_repo.created_at + timedelta(days=7)
    mock_issue_closed_i1_bug.closed_at = mock_repo.created_at + timedelta(days=8)
    mock_pull_closed_with_rls_notes_101.merged_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_101.closed_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_102.merged_at = mock_repo.created_at + timedelta(days=7)
    mock_pull_closed_with_rls_notes_102.closed_at = mock_repo.created_at + timedelta(days=7)
    github_mock.get_repo().get_latest_release.return_value = mock_git_release
    mock_git_release.created_at = mock_repo.created_at + timedelta(days=5)
    mock_git_release.published_at = mock_repo.created_at + timedelta(days=5)
    mocker.patch("release_notes_generator.data.miner.DataMiner.get_latest_release", return_value=mock_git_release)
    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit
    mocker.patch("release_notes_generator.record.factory.default_record_factory.get_issues_for_pr", return_value=None)
    custom_chapters = CustomChapters(print_empty_chapters=True)
    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()
    assert release_notes is not None
    assert "- N/A: #122 _I1+bug_" in release_notes
    assert "- PR: #101 _Fixed bug_" not in release_notes
    assert "- PR: #102 _Fixed bug_" in release_notes

