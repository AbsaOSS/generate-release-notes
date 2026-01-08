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
This module contains the ActionInputs class which is responsible for handling the inputs provided to the GH action.
"""

import logging
import os
import sys
import re

import yaml

from release_notes_generator.utils.constants import (
    GITHUB_REPOSITORY,
    GITHUB_TOKEN,
    TAG_NAME,
    CHAPTERS,
    PUBLISHED_AT,
    VERBOSE,
    WARNINGS,
    HIDDEN_SERVICE_CHAPTERS,
    RUNNER_DEBUG,
    PRINT_EMPTY_CHAPTERS,
    DUPLICITY_SCOPE,
    DUPLICITY_ICON,
    ROW_FORMAT_LINK_PR,
    ROW_FORMAT_ISSUE,
    ROW_FORMAT_PR,
    SKIP_RELEASE_NOTES_LABELS,
    RELEASE_NOTES_TITLE,
    RELEASE_NOTE_TITLE_DEFAULT,
    FROM_TAG_NAME,
    CODERABBIT_SUPPORT_ACTIVE,
    CODERABBIT_RELEASE_NOTES_TITLE,
    CODERABBIT_RELEASE_NOTE_TITLE_DEFAULT,
    CODERABBIT_SUMMARY_IGNORE_GROUPS,
    ROW_FORMAT_HIERARCHY_ISSUE,
    SUPPORTED_ROW_FORMAT_KEYS_ISSUE,
    SUPPORTED_ROW_FORMAT_KEYS_PULL_REQUEST,
    SUPPORTED_ROW_FORMAT_KEYS_HIERARCHY_ISSUE,
)
from release_notes_generator.utils.enums import DuplicityScopeEnum
from release_notes_generator.utils.gh_action import get_action_input
from release_notes_generator.utils.utils import normalize_version_tag

logger = logging.getLogger(__name__)


# pylint: disable=too-many-branches, too-many-statements, too-many-locals, too-many-public-methods
class ActionInputs:
    """
    A class representing the inputs provided to the GH action.
    """

    ROW_TYPE_ISSUE = "Issue"
    ROW_TYPE_PR = "PR"
    ROW_TYPE_HIERARCHY_ISSUE = "HierarchyIssue"

    _row_format_hierarchy_issue = None
    _row_format_issue = None
    _row_format_pr = None
    _row_format_link_pr = None
    _owner = ""
    _repo_name = ""

    @staticmethod
    def get_github_owner() -> str:
        """
        Get the GitHub owner from the action inputs.
        """
        if ActionInputs._owner:
            return ActionInputs._owner

        repository_id = get_action_input(GITHUB_REPOSITORY) or ""
        if "/" in repository_id:
            ActionInputs._owner, _ = repository_id.split("/", 1)
        else:
            ActionInputs._owner = repository_id

        return ActionInputs._owner

    @staticmethod
    def get_github_repo_name() -> str:
        """
        Get the GitHub repository name from the action inputs.
        """
        if ActionInputs._repo_name:
            return ActionInputs._repo_name

        repository_id = get_action_input(GITHUB_REPOSITORY) or ""
        if "/" in repository_id:
            _, ActionInputs._repo_name = repository_id.split("/", 1)
        else:
            ActionInputs._repo_name = repository_id

        return ActionInputs._repo_name

    @staticmethod
    def get_github_repository() -> str:
        """
        Get the GitHub repository from the action inputs.
        """
        return get_action_input(GITHUB_REPOSITORY) or ""

    @staticmethod
    def get_github_token() -> str:
        """
        Get the GitHub token from the action inputs.
        """
        return get_action_input(GITHUB_TOKEN) or ""

    @staticmethod
    def get_tag_name() -> str:
        """
        Get the tag name from the action inputs.
        """
        raw = get_action_input(TAG_NAME) or ""
        return normalize_version_tag(raw)

    @staticmethod
    def get_from_tag_name() -> str:
        """
        Get the from-tag name from the action inputs.
        """
        raw = get_action_input(FROM_TAG_NAME, default="")
        return normalize_version_tag(raw)  # type: ignore[arg-type]

    @staticmethod
    def is_from_tag_name_defined() -> bool:
        """
        Check if the from-tag name is defined in the action inputs.
        """
        value = ActionInputs.get_from_tag_name()
        return value.strip() != ""

    @staticmethod
    def get_chapters() -> list[dict[str, str]]:
        """
        Get list of the chapters from the action inputs. Each chapter is a dict.
        """
        # Get the 'chapters' input from environment variables
        chapters_input: str = get_action_input(CHAPTERS, default="")  # type: ignore[assignment]
        # mypy: string is returned as default

        # Parse the received string back to YAML array input.
        try:
            chapters = yaml.safe_load(chapters_input)
            if not isinstance(chapters, list):
                logger.error("Error: 'chapters' input is not a valid YAML list.")
                return []
        except yaml.YAMLError as exc:
            logger.error("Error parsing 'chapters' input: {%s}", exc)
            return []

        return chapters

    @staticmethod
    def get_hierarchy() -> bool:
        """
        Check if the hierarchy release notes structure is enabled.
        """
        val = get_action_input("hierarchy", "false")
        return str(val).strip().lower() in ("true", "1", "yes", "y", "on")

    @staticmethod
    def get_duplicity_scope() -> DuplicityScopeEnum:
        """
        Get the duplicity scope parameter value from the action inputs.
        """
        duplicity_scope = get_action_input(DUPLICITY_SCOPE, "both").upper()  # type: ignore[union-attr]
        # mypy: string is returned as default

        try:
            return DuplicityScopeEnum(duplicity_scope)
        except ValueError:
            logger.error("Error: '%s' is not a valid DuplicityType.", duplicity_scope)
            return DuplicityScopeEnum.BOTH

    @staticmethod
    def get_duplicity_icon() -> str:
        """
        Get the duplicity icon from the action inputs.
        """
        return get_action_input(DUPLICITY_ICON, "🔔")  # type: ignore[return-value]  # string is returned as default

    @staticmethod
    def get_published_at() -> bool:
        """
        Get the published at parameter value from the action inputs.
        """
        return get_action_input(PUBLISHED_AT, "false").lower() == "true"  # type: ignore[union-attr]
        # mypy: string is returned as default

    @staticmethod
    def get_skip_release_notes_labels() -> list[str]:
        """
        Get the skip release notes label from the action inputs.
        """
        user_input = get_action_input(SKIP_RELEASE_NOTES_LABELS, "")
        user_choice = [item.strip() for item in user_input.split(",")] if user_input else []
        if user_choice:
            return user_choice
        return ["skip-release-notes"]

    @staticmethod
    def get_verbose() -> bool:
        """
        Get the verbose parameter value from the action inputs.
        Safe for non-GitHub test contexts where the input may be unset (returns False by default).
        """
        raw = get_action_input(VERBOSE, "false")  # type: ignore[assignment]
        # Some test contexts (unit/integration) do not populate GitHub inputs; fall back to default.
        raw_normalized = (raw or "false").strip().lower()
        return os.getenv(RUNNER_DEBUG, "0") == "1" or raw_normalized == "true"
        # mypy: string is returned as default

    @staticmethod
    def get_release_notes_title() -> str:
        """
        Get the release notes title from the action inputs.
        """
        return get_action_input(RELEASE_NOTES_TITLE, RELEASE_NOTE_TITLE_DEFAULT)  # type: ignore[return-value]
        # mypy: string is returned as default

    @staticmethod
    def is_coderabbit_support_active() -> bool:
        """
        Get the CodeRabbit support active parameter value from the action inputs.
        """
        return get_action_input(CODERABBIT_SUPPORT_ACTIVE, "false").lower() == "true"  # type: ignore[union-attr]

    @staticmethod
    def get_coderabbit_release_notes_title() -> str:
        """
        Get the CodeRabbit release notes title from the action inputs.
        """
        return get_action_input(
            CODERABBIT_RELEASE_NOTES_TITLE, CODERABBIT_RELEASE_NOTE_TITLE_DEFAULT
        )  # type: ignore[return-value]

    @staticmethod
    def get_coderabbit_summary_ignore_groups() -> list[str]:
        """
        Get the CodeRabbit summary title types to ignore.
        """
        ignore_groups: list[str] = []
        raw = get_action_input(CODERABBIT_SUMMARY_IGNORE_GROUPS, "")
        if not isinstance(raw, str):
            logger.error("Error: 'coderabbit_summary_ignore_groups' is not a valid string.")
            return ignore_groups

        titles = raw.strip()
        if titles:
            separator = "," if "," in titles else "\n"
            ignore_groups = [title.strip() for title in titles.split(separator)]

        return ignore_groups

    # Features
    @staticmethod
    def get_warnings() -> bool:
        """
        Get the warnings parameter value from the action inputs.
        """
        return get_action_input(WARNINGS, "true").lower() == "true"  # type: ignore[union-attr]
        # mypy: string is returned as default

    @staticmethod
    def get_hidden_service_chapters() -> list[str]:
        """
        Get the list of service chapter titles to hide from the action inputs.
        Returns a list of chapter titles that should be hidden from output.
        """
        hidden_chapters: list[str] = []
        raw = get_action_input(HIDDEN_SERVICE_CHAPTERS, "")
        if not isinstance(raw, str):
            logger.error("Error: 'hidden-service-chapters' is not a valid string.")
            return hidden_chapters

        titles = raw.strip()
        if titles:
            # Support both comma and newline separators
            separator = "," if "," in titles else "\n"
            hidden_chapters = [title.strip() for title in titles.split(separator) if title.strip()]

        return hidden_chapters

    @staticmethod
    def get_print_empty_chapters() -> bool:
        """
        Get the print empty chapters parameter value from the action inputs.
        """
        return get_action_input(PRINT_EMPTY_CHAPTERS, "true").lower() == "true"  # type: ignore[union-attr]
        # mypy: string is returned as default

    @staticmethod
    def validate_input(input_value, expected_type: type, error_message: str, error_buffer: list) -> bool:
        """
        Validates the input value against the expected type.

        @param input_value: The input value to validate.
        @param expected_type: The expected type of the input value.
        @param error_message: The error message to log if the validation fails.
        @param error_buffer: The buffer to store the error messages.
        @return: The boolean result of the validation.
        """

        if not isinstance(input_value, expected_type):
            error_buffer.append(error_message)
            return False
        return True

    @staticmethod
    def get_row_format_hierarchy_issue() -> str:
        """
        Get the hierarchy issue row format for the release notes.
        """
        if ActionInputs._row_format_hierarchy_issue is None:
            ActionInputs._row_format_hierarchy_issue = ActionInputs._detect_row_format_invalid_keywords(
                get_action_input(
                    ROW_FORMAT_HIERARCHY_ISSUE, "{type}: _{title}_ {number}"
                ).strip(),  # type: ignore[union-attr]
                row_type=ActionInputs.ROW_TYPE_HIERARCHY_ISSUE,
                clean=True,
            )
        return ActionInputs._row_format_hierarchy_issue

    @staticmethod
    def get_row_format_issue() -> str:
        """
        Get the issue row format for the release notes.
        """
        if ActionInputs._row_format_issue is None:
            ActionInputs._row_format_issue = ActionInputs._detect_row_format_invalid_keywords(
                get_action_input(
                    ROW_FORMAT_ISSUE, "{type}: {number} _{title}_ developed by {developers} in {pull-requests}"
                ).strip(),  # type: ignore[union-attr]
                clean=True,
                # mypy: string is returned as default
            )
        return ActionInputs._row_format_issue

    @staticmethod
    def get_row_format_pr() -> str:
        """
        Get the pr row format for the release notes.
        """
        if ActionInputs._row_format_pr is None:
            ActionInputs._row_format_pr = ActionInputs._detect_row_format_invalid_keywords(
                get_action_input(
                    ROW_FORMAT_PR, "{number} _{title}_ developed by {developers}"
                ).strip(),  # type: ignore[union-attr]
                row_type=ActionInputs.ROW_TYPE_PR,
                clean=True,
                # mypy: string is returned as default
            )
        return ActionInputs._row_format_pr

    @staticmethod
    def get_row_format_link_pr() -> bool:
        """
        Get the value controlling whether the row format should include a 'PR:' prefix when linking to PRs.
        """
        return get_action_input(ROW_FORMAT_LINK_PR, "true").lower() == "true"  # type: ignore[union-attr]
        # mypy: string is returned as default

    @staticmethod
    def validate_inputs() -> None:
        """
        Validates the inputs provided for the release notes generator.
        Logs any validation errors and exits if any are found.
        @return: None
        """
        errors = []

        repository_id = ActionInputs.get_github_repository()
        if not isinstance(repository_id, str) or not repository_id.strip():
            errors.append("Repository ID must be a non-empty string.")

        if "/" in repository_id:
            ActionInputs._owner, ActionInputs._repo_name = ActionInputs.get_github_repository().split("/")
        else:
            ActionInputs._owner = ActionInputs._repo_name = ""

        if (
            not isinstance(ActionInputs._owner, str)
            or not ActionInputs._owner.strip()
            or not isinstance(ActionInputs._repo_name, str)
            or not ActionInputs._repo_name.strip()
        ):
            errors.append("Owner and Repo must be a non-empty string.")

        tag_name = ActionInputs.get_tag_name()
        if not isinstance(tag_name, str) or not tag_name.strip():
            errors.append("Tag name must be a non-empty string.")

        from_tag_name = ActionInputs.get_from_tag_name()
        if not isinstance(from_tag_name, str):
            errors.append("From tag name must be a string.")

        chapters = ActionInputs.get_chapters()
        if len(chapters) == 0:
            errors.append("Chapters must be a valid yaml array and not empty.")

        duplicity_icon = ActionInputs.get_duplicity_icon()
        if not isinstance(duplicity_icon, str) or not duplicity_icon.strip() or len(duplicity_icon) != 1:
            errors.append("Duplicity icon must be a non-empty string and have a length of 1.")

        hierarchy: bool = ActionInputs.get_hierarchy()
        ActionInputs.validate_input(hierarchy, bool, "Hierarchy must be a boolean.", errors)

        warnings = ActionInputs.get_warnings()
        ActionInputs.validate_input(warnings, bool, "Warnings must be a boolean.", errors)

        published_at = ActionInputs.get_published_at()
        ActionInputs.validate_input(published_at, bool, "Published at must be a boolean.", errors)

        verbose = ActionInputs.get_verbose()
        ActionInputs.validate_input(verbose, bool, "Verbose logging must be a boolean.", errors)

        release_notes_title = ActionInputs.get_release_notes_title()
        if not isinstance(release_notes_title, str) or len(release_notes_title) == 0:
            errors.append("Release Notes title must be a non-empty string and have non-zero length.")

        coderabbit_support_active = ActionInputs.is_coderabbit_support_active()
        coderabbit_release_notes_title = ActionInputs.get_coderabbit_release_notes_title()
        coderabbit_summary_ignore_groups = ActionInputs.get_coderabbit_summary_ignore_groups()

        if coderabbit_support_active:
            if not isinstance(coderabbit_release_notes_title, str) or len(coderabbit_release_notes_title) == 0:
                errors.append("CodeRabbit Release Notes title must be a non-empty string and have non-zero length.")

            for group in coderabbit_summary_ignore_groups:
                if not isinstance(group, str) or len(group) == 0:
                    errors.append(
                        "CodeRabbit summary ignore groups must be a non-empty string and have non-zero length."
                    )

        row_format_issue = ActionInputs.get_row_format_issue()
        if not isinstance(row_format_issue, str) or not row_format_issue.strip():
            errors.append("Issue row format must be a non-empty string.")

        ActionInputs._detect_row_format_invalid_keywords(row_format_issue)

        row_format_pr = ActionInputs.get_row_format_pr()
        if not isinstance(row_format_pr, str) or not row_format_pr.strip():
            errors.append("PR Row format must be a non-empty string.")

        ActionInputs._detect_row_format_invalid_keywords(row_format_pr, row_type=ActionInputs.ROW_TYPE_PR)

        row_format_hier_issue = ActionInputs.get_row_format_hierarchy_issue()
        if not isinstance(row_format_hier_issue, str) or not row_format_hier_issue.strip():
            errors.append("Hierarchy Issue row format must be a non-empty string.")
        ActionInputs._detect_row_format_invalid_keywords(
            row_format_hier_issue, row_type=ActionInputs.ROW_TYPE_HIERARCHY_ISSUE
        )

        row_format_link_pr = ActionInputs.get_row_format_link_pr()
        ActionInputs.validate_input(row_format_link_pr, bool, "'row-format-link-pr' value must be a boolean.", errors)

        # Features
        print_empty_chapters = ActionInputs.get_print_empty_chapters()
        ActionInputs.validate_input(print_empty_chapters, bool, "Print empty chapters must be a boolean.", errors)

        # Validate hidden service chapters: each must be a non-empty string
        hidden_service_chapters = ActionInputs.get_hidden_service_chapters()
        for chapter in hidden_service_chapters:
            if not isinstance(chapter, str) or not chapter:
                errors.append("Hidden service chapters must be a non-empty string and have non-zero length.")

        # Log errors if any
        if errors:
            for error in errors:
                logger.error(error)
            sys.exit(1)

        logger.debug("Repository: %s/%s", ActionInputs._owner, ActionInputs._repo_name)
        logger.debug("Tag name: %s", tag_name)
        logger.debug("From tag name: %s", from_tag_name)
        logger.debug("Chapters: %s", chapters)
        logger.debug("Duplicity scope: %s", ActionInputs.get_duplicity_scope())
        logger.debug("Duplicity icon: %s", ActionInputs.get_duplicity_icon())
        logger.debug("Hierarchy: %s", hierarchy)
        logger.debug("Published at: %s", published_at)
        logger.debug("Skip release notes labels: %s", ActionInputs.get_skip_release_notes_labels())
        logger.debug("Verbose logging: %s", verbose)
        logger.debug("Warnings: %s", warnings)
        logger.debug("Hidden service chapters: %s", hidden_service_chapters)
        logger.debug("Print empty chapters: %s", print_empty_chapters)
        logger.debug("Release notes title: %s", release_notes_title)
        logger.debug("CodeRabbit support active: %s", coderabbit_support_active)
        logger.debug("CodeRabbit release notes title: %s", coderabbit_release_notes_title)
        logger.debug("CodeRabbit summary ignore groups: %s", coderabbit_summary_ignore_groups)

    @staticmethod
    def _detect_row_format_invalid_keywords(row_format: str, row_type: str = "Issue", clean: bool = False) -> str:
        """
        Detects invalid keywords in the row format.

        @param row_format: The row format to be checked for invalid keywords.
        @param row_type: The type of row format. Default is "Issue".
        @return: If clean is True, the cleaned row format. Otherwise, the original row format.
        """
        keywords_in_braces = re.findall(r"\{(.*?)\}", row_format)

        mapping = {
            ActionInputs.ROW_TYPE_ISSUE: SUPPORTED_ROW_FORMAT_KEYS_ISSUE,
            ActionInputs.ROW_TYPE_PR: SUPPORTED_ROW_FORMAT_KEYS_PULL_REQUEST,
            ActionInputs.ROW_TYPE_HIERARCHY_ISSUE: SUPPORTED_ROW_FORMAT_KEYS_HIERARCHY_ISSUE,
        }
        supported_row_format_keys = mapping.get(row_type)
        if supported_row_format_keys is None:
            logger.warning(
                "Unknown row_type '%s' in _detect_row_format_invalid_keywords; defaulting to Issue keys.",
                row_type,
            )
            supported_row_format_keys = SUPPORTED_ROW_FORMAT_KEYS_ISSUE

        invalid_keywords = [keyword for keyword in keywords_in_braces if keyword not in supported_row_format_keys]
        cleaned_row_format = row_format
        for invalid_keyword in invalid_keywords:
            logger.error(
                "Invalid `%s` detected in `%s` row format keyword(s) found: %s. Will be removed from string.",
                invalid_keyword,
                row_type,
                ", ".join(invalid_keywords),
            )
            if clean:
                cleaned_row_format = cleaned_row_format.replace(f"{{{invalid_keyword}}}", "")

        return cleaned_row_format
