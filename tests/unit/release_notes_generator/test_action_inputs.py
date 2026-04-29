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
import yaml
import pytest
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import (
    DEFAULT_SERVICE_CHAPTER_ORDER,
    OTHERS_NO_TOPIC,
    DIRECT_COMMITS,
    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
    MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
)

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
    ("get_row_format_hierarchy_issue", "", "Hierarchy Issue row format must be a non-empty string."),
    ("get_release_notes_title", "", "Release Notes title must be a non-empty string and have non-zero length."),
    (
        "get_coderabbit_release_notes_title",
        "",
        "CodeRabbit Release Notes title must be a non-empty string and have non-zero length.",
    ),
    (
        "get_coderabbit_summary_ignore_groups",
        [""],
        "CodeRabbit summary ignore groups must be a non-empty string and have non-zero length.",
    ),
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
    assert "Invalid version tag format: 'v1.2.beta'. Expected vMAJOR.MINOR[.PATCH], e.g. 'v0.2' or 'v0.2.0'." in str(
        excinfo.value
    )


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
    assert "Invalid version tag format: 'v1.2.beta'. Expected vMAJOR.MINOR[.PATCH], e.g. 'v0.2' or 'v0.2.0'." in str(
        excinfo.value
    )


def test_get_chapters_success(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value='[{"title": "Title", "label": "Label"}]'
    )
    assert ActionInputs.get_chapters() == [{"title": "Title", "label": "Label"}]


def test_get_chapters_exception(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="wrong value")
    assert [] == ActionInputs.get_chapters()


def test_get_chapters_yaml_error(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value='[{"title": "Title" "label": "Label"}]'
    )
    assert [] == ActionInputs.get_chapters()


def test_get_super_chapters_success(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": "Module A", "label": "mod-a"}]',
    )
    assert ActionInputs.get_super_chapters() == [{"title": "Module A", "labels": ["mod-a"]}]


def test_get_super_chapters_empty_input(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_super_chapters() == []


def test_get_super_chapters_blank_input(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="   ")
    assert ActionInputs.get_super_chapters() == []


def test_get_super_chapters_not_a_list(mocker, caplog):
    caplog.set_level("ERROR")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="not_a_list: true")
    result = ActionInputs.get_super_chapters()
    assert result == []
    assert any("not a valid YAML list" in r.message for r in caplog.records)


def test_get_super_chapters_yaml_error(mocker, caplog):
    caplog.set_level("ERROR")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": "A" "label": "b"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == []
    assert any("Error parsing 'super-chapters'" in r.message for r in caplog.records)


def test_get_super_chapters_list_labels_preserved(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": "Module A", "labels": ["mod-a", "mod-b"]}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Module A", "labels": ["mod-a", "mod-b"]}]


def test_get_super_chapters_comma_separated_labels_string(mocker):
    """Comma-separated string labels are split into individual label tokens."""
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": "Module A", "labels": "atum-agent, atum-agent-spark"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Module A", "labels": ["atum-agent", "atum-agent-spark"]}]


def test_get_super_chapters_non_dict_entry_skipped(mocker, caplog):
    caplog.set_level("WARNING")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='["not-a-dict", {"title": "Valid", "label": "ok"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Valid", "labels": ["ok"]}]
    assert any("invalid type" in r.message for r in caplog.records)


def test_get_super_chapters_missing_title_skipped(mocker, caplog):
    caplog.set_level("WARNING")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"no-title": true}, {"title": "Valid", "label": "v"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Valid", "labels": ["v"]}]
    assert any("without title key" in r.message for r in caplog.records)


def test_get_super_chapters_non_string_title_skipped(mocker, caplog):
    caplog.set_level("WARNING")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": 42, "label": "l"}, {"title": "Valid", "label": "v"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Valid", "labels": ["v"]}]
    assert any("invalid title value" in r.message for r in caplog.records)


def test_get_super_chapters_blank_title_skipped(mocker, caplog):
    caplog.set_level("WARNING")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": "   ", "label": "l"}, {"title": "Valid", "label": "v"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Valid", "labels": ["v"]}]
    assert any("invalid title value" in r.message for r in caplog.records)


def test_get_super_chapters_missing_labels_skipped(mocker, caplog):
    caplog.set_level("WARNING")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": "No labels"}, {"title": "Valid", "label": "v"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Valid", "labels": ["v"]}]
    assert any("has no 'label' or 'labels' key" in r.message for r in caplog.records)


def test_get_super_chapters_empty_labels_after_normalization_skipped(mocker, caplog):
    caplog.set_level("WARNING")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value='[{"title": "Empty", "labels": []}, {"title": "Valid", "label": "v"}]',
    )
    result = ActionInputs.get_super_chapters()
    assert result == [{"title": "Valid", "labels": ["v"]}]
    assert any("empty after normalization" in r.message for r in caplog.records)


def test_get_super_chapters_cached_on_same_raw_input(mocker, monkeypatch):
    """Parsing and validation run only once when the raw input string has not changed."""
    monkeypatch.setattr(ActionInputs, "_super_chapters_raw", None)
    monkeypatch.setattr(ActionInputs, "_super_chapters_cache", None)
    raw = '[{"title": "Module A", "label": "mod-a"}]'
    mock_get = mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=raw)
    spy = mocker.spy(yaml, "safe_load")

    result1 = ActionInputs.get_super_chapters()
    result2 = ActionInputs.get_super_chapters()

    assert result1 == result2 == [{"title": "Module A", "labels": ["mod-a"]}]
    # yaml.safe_load must have been called exactly once despite two get_super_chapters calls
    assert spy.call_count == 1
    assert mock_get.call_count == 2  # env is read each time, only parse is skipped


def test_get_super_chapters_cache_invalidated_on_new_raw_input(mocker, monkeypatch):
    """Cache is bypassed and re-parsed when the raw input string changes between calls."""
    monkeypatch.setattr(ActionInputs, "_super_chapters_raw", None)
    monkeypatch.setattr(ActionInputs, "_super_chapters_cache", None)
    raw_a = '[{"title": "Module A", "label": "mod-a"}]'
    raw_b = '[{"title": "Module B", "label": "mod-b"}]'
    mock_get = mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=raw_a)

    result_a = ActionInputs.get_super_chapters()
    assert result_a == [{"title": "Module A", "labels": ["mod-a"]}]

    mock_get.return_value = raw_b
    result_b = ActionInputs.get_super_chapters()
    assert result_b == [{"title": "Module B", "labels": ["mod-b"]}]


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
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value="skip-release-notes, another-skip-label"
    )
    assert ActionInputs.get_skip_release_notes_labels() == ["skip-release-notes", "another-skip-label"]


def test_get_skip_release_notes_labels_no_space(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value="skip-release-notes,another-skip-label"
    )
    assert ActionInputs.get_skip_release_notes_labels() == ["skip-release-notes", "another-skip-label"]


def test_get_print_empty_chapters(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="true")
    assert ActionInputs.get_print_empty_chapters() is True


def test_get_show_stats_chapters_default_true(mocker):
    """show-stats-chapters defaults to True when the input is absent (default 'true')."""
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="true")
    assert ActionInputs.get_show_stats_chapters() is True


def test_get_show_stats_chapters_explicitly_false(mocker):
    """show-stats-chapters returns False when explicitly set to 'false'."""
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="false")
    assert ActionInputs.get_show_stats_chapters() is False


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
        "Invalid `another_invalid` detected in `Issue` row format keyword(s) found: invalid_key, another_invalid. Will be removed from string.",
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
    assert ActionInputs.get_coderabbit_summary_ignore_groups() == ["", ""]


def test_get_hidden_service_chapters_default(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_hidden_service_chapters() == []


def test_get_hidden_service_chapters_single_comma_separated(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Direct Commits ⚠️")
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️"]


def test_get_hidden_service_chapters_multiple_comma_separated(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value="Direct Commits ⚠️, Others - No Topic ⚠️"
    )
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️", "Others - No Topic ⚠️"]


def test_get_hidden_service_chapters_newline_separated(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value="Direct Commits ⚠️\nOthers - No Topic ⚠️"
    )
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️", "Others - No Topic ⚠️"]


def test_get_hidden_service_chapters_with_extra_whitespace(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input",
        return_value="  Direct Commits ⚠️  ,  Others - No Topic ⚠️  ",
    )
    assert ActionInputs.get_hidden_service_chapters() == ["Direct Commits ⚠️", "Others - No Topic ⚠️"]


def test_get_hidden_service_chapters_int_input(mocker):
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=123)
    assert ActionInputs.get_hidden_service_chapters() == []
    mock_log_error.assert_called_once()
    assert "hidden-service-chapters' is not a valid string" in mock_log_error.call_args[0][0]


# get_service_chapter_order


def test_get_service_chapter_order_default(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_service_chapter_order() == DEFAULT_SERVICE_CHAPTER_ORDER


def test_get_service_chapter_order_full_custom(mocker):
    custom_order = f"{OTHERS_NO_TOPIC}, {DIRECT_COMMITS}, {CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}, {CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS}, {MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS}, {CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS}, {MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES}"
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=custom_order)
    result = ActionInputs.get_service_chapter_order()
    assert result[0] == OTHERS_NO_TOPIC
    assert result[1] == DIRECT_COMMITS
    assert len(result) == 7


def test_get_service_chapter_order_partial(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=OTHERS_NO_TOPIC)
    result = ActionInputs.get_service_chapter_order()
    assert result[0] == OTHERS_NO_TOPIC
    assert len(result) == len(DEFAULT_SERVICE_CHAPTER_ORDER)
    # Remaining chapters appended in default order (without OTHERS_NO_TOPIC)
    remaining = [t for t in DEFAULT_SERVICE_CHAPTER_ORDER if t != OTHERS_NO_TOPIC]
    assert result[1:] == remaining


def test_get_service_chapter_order_newline_separated(mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value=f"{OTHERS_NO_TOPIC}\n{DIRECT_COMMITS}"
    )
    result = ActionInputs.get_service_chapter_order()
    assert result[0] == OTHERS_NO_TOPIC
    assert result[1] == DIRECT_COMMITS


def test_get_service_chapter_order_invalid_title(mocker):
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="Invalid Title")
    result = ActionInputs.get_service_chapter_order()
    assert result == DEFAULT_SERVICE_CHAPTER_ORDER
    mock_log_error.assert_called_once()
    assert "Invalid service chapter title" in mock_log_error.call_args[0][0]


def test_get_service_chapter_order_duplicate_title(mocker):
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch(
        "release_notes_generator.action_inputs.get_action_input", return_value=f"{OTHERS_NO_TOPIC}, {OTHERS_NO_TOPIC}"
    )
    result = ActionInputs.get_service_chapter_order()
    assert result[0] == OTHERS_NO_TOPIC
    assert result.count(OTHERS_NO_TOPIC) == 1
    mock_log_error.assert_called_once()
    assert "Duplicate service chapter title" in mock_log_error.call_args[0][0]


def test_get_service_chapter_order_int_input(mocker):
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=123)
    result = ActionInputs.get_service_chapter_order()
    assert result == DEFAULT_SERVICE_CHAPTER_ORDER
    mock_log_error.assert_called_once()
    assert "service-chapter-order' is not a valid string" in mock_log_error.call_args[0][0]


def test_get_row_format_link_pr_true(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="true")
    assert ActionInputs.get_row_format_link_pr() is True


def test_get_row_format_link_pr_false(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="false")
    assert ActionInputs.get_row_format_link_pr() is False


def test_get_github_owner_no_slash_in_repository_id(monkeypatch, mocker):
    """Repository ID without '/' sets owner to the whole string."""
    monkeypatch.setattr(ActionInputs, "_owner", "")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="standalone")
    assert ActionInputs.get_github_owner() == "standalone"


def test_get_github_owner_with_slash_in_repository_id(monkeypatch, mocker):
    """Repository ID with '/' extracts the owner part before the slash."""
    monkeypatch.setattr(ActionInputs, "_owner", "")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="my-org/my-repo")
    assert ActionInputs.get_github_owner() == "my-org"


def test_get_github_owner_cache_hit(monkeypatch):
    """Cached owner value is returned without querying the environment."""
    monkeypatch.setattr(ActionInputs, "_owner", "primed-org")
    assert ActionInputs.get_github_owner() == "primed-org"


def test_get_github_repo_name_no_slash_in_repository_id(monkeypatch, mocker):
    """Repository ID without '/' sets repo_name to the whole string."""
    monkeypatch.setattr(ActionInputs, "_repo_name", "")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="standalone")
    assert ActionInputs.get_github_repo_name() == "standalone"


def test_get_github_repo_name_with_slash_in_repository_id(monkeypatch, mocker):
    """Repository ID with '/' extracts the repo name part after the slash."""
    monkeypatch.setattr(ActionInputs, "_repo_name", "")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="my-org/my-repo")
    assert ActionInputs.get_github_repo_name() == "my-repo"


def test_get_github_repo_name_cache_hit(monkeypatch):
    """Cached repo name is returned without querying the environment."""
    monkeypatch.setattr(ActionInputs, "_repo_name", "primed-repo")
    assert ActionInputs.get_github_repo_name() == "primed-repo"


def test_get_open_hierarchy_sub_issue_icon_default():
    assert ActionInputs.get_open_hierarchy_sub_issue_icon() == "🟡"


def test_get_open_hierarchy_sub_issue_icon_custom(mocker):
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="⚡")
    assert ActionInputs.get_open_hierarchy_sub_issue_icon() == "⚡"


def test_detect_row_format_invalid_keywords_unknown_row_type(caplog):
    """Unknown row_type logs a warning and defaults to Issue keys."""
    caplog.set_level("WARNING", logger="release_notes_generator.action_inputs")
    ActionInputs._detect_row_format_invalid_keywords("{number} {bogus}", row_type="Unknown")
    assert any("Unknown row_type" in r.message for r in caplog.records)


def test_get_service_chapter_exclude_default(mocker):
    """Empty dict when env var absent."""
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="")
    assert ActionInputs.get_service_chapter_exclude() == {}


def test_get_service_chapter_exclude_single_chapter_single_group(mocker):
    """One chapter title, one group parsed correctly."""
    yaml_input = f'{CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}:\n  - [scope:security, type:tech-debt]\n'
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: [["scope:security", "type:tech-debt"]]}


def test_get_service_chapter_exclude_single_chapter_multiple_groups(mocker):
    """Multiple groups for one chapter (OR logic)."""
    yaml_input = (
        f'{CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}:\n'
        f'  - [scope:security, type:tech-debt]\n'
        f'  - [scope:security, type:false-positive]\n'
    )
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {
        CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: [
            ["scope:security", "type:tech-debt"],
            ["scope:security", "type:false-positive"],
        ]
    }


def test_get_service_chapter_exclude_multiple_chapters(mocker):
    """Multiple chapter titles parsed."""
    yaml_input = (
        f'{CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}:\n'
        f'  - [scope:security]\n'
        f'{OTHERS_NO_TOPIC}:\n'
        f'  - [wontfix]\n'
    )
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert len(result) == 2
    assert CLOSED_ISSUES_WITHOUT_PULL_REQUESTS in result
    assert OTHERS_NO_TOPIC in result


def test_get_service_chapter_exclude_global_key_single_group(mocker):
    """Reserved '*' key accepted without title validation."""
    yaml_input = '"*":\n  - [scope:security, type:tech-debt]\n'
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {"*": [["scope:security", "type:tech-debt"]]}


def test_get_service_chapter_exclude_global_key_with_per_chapter(mocker):
    """'*' key and a chapter title both preserved."""
    yaml_input = (
        f'"*":\n'
        f'  - [scope:security, type:tech-debt]\n'
        f'{CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}:\n'
        f'  - [scope:security, type:false-positive]\n'
    )
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert len(result) == 2
    assert "*" in result
    assert CLOSED_ISSUES_WITHOUT_PULL_REQUESTS in result


def test_get_service_chapter_exclude_invalid_yaml(mocker):
    """Parse error returns empty dict, error logged."""
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=":\n  :\n  - :")
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {}
    mock_log_error.assert_called_once()


def test_get_service_chapter_exclude_not_a_mapping(mocker):
    """Non-dict YAML returns empty dict, error logged."""
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value="- item1\n- item2")
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {}
    mock_log_error.assert_called_once()


def test_get_service_chapter_exclude_non_string_input(mocker):
    """Non-string env var returns empty dict, error logged."""
    mock_log_error = mocker.patch("release_notes_generator.action_inputs.logger.error")
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=42)
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {}
    mock_log_error.assert_called_once()


def test_get_service_chapter_exclude_unknown_chapter_title(mocker):
    """Unknown title skipped with warning."""
    mock_log_warning = mocker.patch("release_notes_generator.action_inputs.logger.warning")
    yaml_input = (
        f'{CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}:\n'
        f'  - [scope:security]\n'
        f'Unknown Chapter Title:\n'
        f'  - [wontfix]\n'
    )
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert CLOSED_ISSUES_WITHOUT_PULL_REQUESTS in result
    assert "Unknown Chapter Title" not in result
    mock_log_warning.assert_called_once()
    assert "Unknown service chapter title" in mock_log_warning.call_args[0][0]


def test_get_service_chapter_exclude_group_not_a_list(mocker):
    """Non-list group skipped with warning, valid group kept."""
    mock_log_warning = mocker.patch("release_notes_generator.action_inputs.logger.warning")
    yaml_input = (
        f'{CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}:\n'
        f'  - [scope:security]\n'
        f'  - not-a-list\n'
    )
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: [["scope:security"]]}
    mock_log_warning.assert_called_once()


def test_get_service_chapter_exclude_empty_group_list(mocker):
    """Empty list value accepted as no-op."""
    yaml_input = f'{CLOSED_ISSUES_WITHOUT_PULL_REQUESTS}: []\n'
    mocker.patch("release_notes_generator.action_inputs.get_action_input", return_value=yaml_input)
    result = ActionInputs.get_service_chapter_exclude()
    assert result == {CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: []}


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
    assert "- #121 _Fix the bug_" in release_notes
    assert "- #122 _I1+bug_" in release_notes
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
    assert "- #122 _I1+bug_" in release_notes
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
    assert "- #122 _I1+bug_" in release_notes
    assert "- PR: #101 _Fixed bug_" not in release_notes
    assert "- PR: #102 _Fixed bug_" in release_notes
