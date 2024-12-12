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

from typing import Optional

import yaml

from release_notes_generator.utils.constants import (
    GITHUB_REPOSITORY,
    GITHUB_TOKEN,
    TAG_NAME,
    CHAPTERS,
    PUBLISHED_AT,
    VERBOSE,
    WARNINGS,
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
    SUPPORTED_ROW_FORMAT_KEYS,
    FROM_TAG_NAME,
)
from release_notes_generator.utils.enums import DuplicityScopeEnum
from release_notes_generator.utils.gh_action import get_action_input

logger = logging.getLogger(__name__)


# pylint: disable=too-many-branches, too-many-statements, too-many-locals
class ActionInputs:
    """
    A class representing the inputs provided to the GH action.
    """

    _row_format_issue = None
    _row_format_pr = None
    _row_format_link_pr = None

    @staticmethod
    def get_github_repository() -> str:
        """
        Get the GitHub repository from the action inputs.
        """
        return get_action_input(GITHUB_REPOSITORY)

    @staticmethod
    def get_github_token() -> str:
        """
        Get the GitHub token from the action inputs.
        """
        return get_action_input(GITHUB_TOKEN)

    @staticmethod
    def get_tag_name() -> str:
        """
        Get the tag name from the action inputs.
        """
        return get_action_input(TAG_NAME)

    @staticmethod
    def get_from_tag_name() -> str:
        """
        Get the from-tag name from the action inputs.
        """
        return get_action_input(FROM_TAG_NAME, default="")

    @staticmethod
    def is_from_tag_name_defined() -> bool:
        """
        Check if the from-tag name is defined in the action inputs.
        """
        value = ActionInputs.get_from_tag_name()
        return value.strip() != ""

    @staticmethod
    def get_chapters() -> Optional[list[dict[str, str]]]:
        """
        Get list of the chapters from the action inputs. Each chapter is a dict.
        """
        # Get the 'chapters' input from environment variables
        chapters_input: str = get_action_input(CHAPTERS, default="")

        # Parse the received string back to YAML array input.
        try:
            chapters = yaml.safe_load(chapters_input)
            if not isinstance(chapters, list):
                logger.error("Error: 'chapters' input is not a valid YAML list.")
                return None
        except yaml.YAMLError as exc:
            logger.error("Error parsing 'chapters' input: {%s}", exc)
            return None

        return chapters

    @staticmethod
    def get_duplicity_scope() -> DuplicityScopeEnum:
        """
        Get the duplicity scope parameter value from the action inputs.
        """
        duplicity_scope = get_action_input(DUPLICITY_SCOPE, "both").upper()

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
        return get_action_input(DUPLICITY_ICON, "🔔")

    @staticmethod
    def get_published_at() -> bool:
        """
        Get the published at parameter value from the action inputs.
        """
        return get_action_input(PUBLISHED_AT, "false").lower() == "true"

    @staticmethod
    def get_skip_release_notes_labels() -> str:
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
        """
        return os.getenv(RUNNER_DEBUG, "0") == "1" or get_action_input(VERBOSE).lower() == "true"

    @staticmethod
    def get_release_notes_title() -> str:
        """
        Get the release notes title from the action inputs.
        """
        return get_action_input(RELEASE_NOTES_TITLE, RELEASE_NOTE_TITLE_DEFAULT)

    # Features
    @staticmethod
    def get_warnings() -> bool:
        """
        Get the warnings parameter value from the action inputs.
        """
        return get_action_input(WARNINGS, "true").lower() == "true"

    @staticmethod
    def get_print_empty_chapters() -> bool:
        """
        Get the print empty chapters parameter value from the action inputs.
        """
        return get_action_input(PRINT_EMPTY_CHAPTERS, "true").lower() == "true"

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
    def get_row_format_issue() -> str:
        """
        Get the issue row format for the release notes.
        """
        if ActionInputs._row_format_issue is None:
            ActionInputs._row_format_issue = ActionInputs._detect_row_format_invalid_keywords(
                get_action_input(ROW_FORMAT_ISSUE, "{number} _{title}_ in {pull-requests}").strip(), clean=True
            )
        return ActionInputs._row_format_issue

    @staticmethod
    def get_row_format_pr() -> str:
        """
        Get the pr row format for the release notes.
        """
        if ActionInputs._row_format_pr is None:
            ActionInputs._row_format_pr = ActionInputs._detect_row_format_invalid_keywords(
                get_action_input(ROW_FORMAT_PR, "{number} _{title}_").strip(), clean=True
            )
        return ActionInputs._row_format_pr

    @staticmethod
    def get_row_format_link_pr() -> bool:
        """
        Get the value controlling whether the row format should include a 'PR:' prefix when linking to PRs.
        """
        return get_action_input(ROW_FORMAT_LINK_PR, "true").lower() == "true"

    @staticmethod
    def validate_inputs() -> None:
        """
        Validates the inputs provided for the release notes generator.
        Logs any validation errors and exits if any are found.
        @return: None
        """
        errors = []

        repository_id = ActionInputs.get_github_repository()
        if "/" in repository_id:
            owner, repo_name = ActionInputs.get_github_repository().split("/")
        else:
            owner = repo_name = ""

        if not isinstance(owner, str) or not owner.strip() or not isinstance(repo_name, str) or not repo_name.strip():
            errors.append("Owner and Repo must be a non-empty string.")

        tag_name = ActionInputs.get_tag_name()
        if not isinstance(tag_name, str) or not tag_name.strip():
            errors.append("Tag name must be a non-empty string.")

        from_tag_name = ActionInputs.get_from_tag_name()
        if not isinstance(from_tag_name, str):
            errors.append("From tag name must be a string.")

        chapters = ActionInputs.get_chapters()
        if chapters is None:
            errors.append("Chapters must be a valid yaml array.")

        duplicity_icon = ActionInputs.get_duplicity_icon()
        if not isinstance(duplicity_icon, str) or not duplicity_icon.strip() or len(duplicity_icon) != 1:
            errors.append("Duplicity icon must be a non-empty string and have a length of 1.")

        warnings = ActionInputs.get_warnings()
        ActionInputs.validate_input(warnings, bool, "Warnings must be a boolean.", errors)

        published_at = ActionInputs.get_published_at()
        ActionInputs.validate_input(published_at, bool, "Published at must be a boolean.", errors)

        verbose = ActionInputs.get_verbose()
        ActionInputs.validate_input(verbose, bool, "Verbose logging must be a boolean.", errors)

        release_notes_title = ActionInputs.get_release_notes_title()
        if not isinstance(release_notes_title, str) or len(release_notes_title) == 0:
            errors.append("Release Notes title must be a non-empty string and have non-zero length.")

        row_format_issue = ActionInputs.get_row_format_issue()
        if not isinstance(row_format_issue, str) or not row_format_issue.strip():
            errors.append("Issue row format must be a non-empty string.")

        ActionInputs._detect_row_format_invalid_keywords(row_format_issue)

        row_format_pr = ActionInputs.get_row_format_pr()
        if not isinstance(row_format_pr, str) or not row_format_pr.strip():
            errors.append("PR Row format must be a non-empty string.")

        ActionInputs._detect_row_format_invalid_keywords(row_format_pr, row_type="PR")

        row_format_link_pr = ActionInputs.get_row_format_link_pr()
        ActionInputs.validate_input(row_format_link_pr, bool, "'row-format-link-pr' value must be a boolean.", errors)

        # Features
        print_empty_chapters = ActionInputs.get_print_empty_chapters()
        ActionInputs.validate_input(print_empty_chapters, bool, "Print empty chapters must be a boolean.", errors)

        # Log errors if any
        if errors:
            for error in errors:
                logger.error(error)
            sys.exit(1)

        logger.debug("Repository: %s/%s", owner, repo_name)
        logger.debug("Tag name: %s", tag_name)
        logger.debug("Chapters: %s", chapters)
        logger.debug("Published at: %s", published_at)
        logger.debug("Skip release notes labels: %s", ActionInputs.get_skip_release_notes_labels())
        logger.debug("Verbose logging: %s", verbose)
        logger.debug("Warnings: %s", warnings)
        logger.debug("Print empty chapters: %s", print_empty_chapters)
        logger.debug("Release notes title: %s", release_notes_title)

    @staticmethod
    def _detect_row_format_invalid_keywords(row_format: str, row_type: str = "Issue", clean: bool = False) -> str:
        """
        Detects invalid keywords in the row format.

        @param row_format: The row format to be checked for invalid keywords.
        @param row_type: The type of row format. Default is "Issue".
        @return: If clean is True, the cleaned row format. Otherwise, the original row format.
        """
        keywords_in_braces = re.findall(r"\{(.*?)\}", row_format)
        invalid_keywords = [keyword for keyword in keywords_in_braces if keyword not in SUPPORTED_ROW_FORMAT_KEYS]
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
