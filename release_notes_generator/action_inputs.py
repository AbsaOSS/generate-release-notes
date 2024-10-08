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

import json
import logging
import os
import sys

from release_notes_generator.utils.constants import (
    GITHUB_REPOSITORY,
    GITHUB_TOKEN,
    TAG_NAME,
    CHAPTERS,
    PUBLISHED_AT,
    SKIP_RELEASE_NOTES_LABEL,
    VERBOSE,
    WARNINGS,
    RUNNER_DEBUG,
    PRINT_EMPTY_CHAPTERS,
    DUPLICITY_SCOPE,
    DUPLICITY_ICON,
    ROW_FORMAT_LINK_PR,
    ROW_FORMAT_ISSUE,
    ROW_FORMAT_PR, ROW_FORMAT_COMMIT, ROW_FORMAT_LINK_COMMIT,
)
from release_notes_generator.utils.enums import DuplicityScopeEnum
from release_notes_generator.utils.gh_action import get_action_input
from release_notes_generator.utils.utils import detect_row_format_invalid_keywords

logger = logging.getLogger(__name__)


# pylint: disable=too-many-branches, too-many-statements, too-many-locals
class ActionInputs:
    """
    A class representing the inputs provided to the GH action.
    """

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
    def get_chapters_json() -> str:
        """
        Get the chapters JSON from the action inputs.
        """
        return get_action_input(CHAPTERS)

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
    def get_skip_release_notes_label() -> str:
        """
        Get the skip release notes label from the action inputs.
        """
        return get_action_input(SKIP_RELEASE_NOTES_LABEL) or "skip-release-notes"

    @staticmethod
    def get_verbose() -> bool:
        """
        Get the verbose parameter value from the action inputs.
        """
        return os.getenv(RUNNER_DEBUG, "0") == "1" or get_action_input(VERBOSE).lower() == "true"

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
        return get_action_input(ROW_FORMAT_ISSUE, "#{number} _{title}_ {pull-requests} {assignee} {developed-by} {co-authored-by}").strip()

    @staticmethod
    def get_row_format_pr() -> str:
        """
        Get the pr row format for the release notes.
        """
        return get_action_input(ROW_FORMAT_PR, "#{number} _{title}_ {assignee} {developed-by} {co-authored-by}").strip()

    @staticmethod
    def get_row_format_commit() -> str:
        """
        Get the commit row format for the release notes.
        """
        return get_action_input(ROW_FORMAT_COMMIT, "{sha} {author} {co-authored-by}").strip()

    @staticmethod
    def get_row_format_link_pr() -> bool:
        """
        Get the value controlling whether the row format should include a 'PR:' prefix when linking to PRs.
        """
        return get_action_input(ROW_FORMAT_LINK_PR, "true").lower() == "true"

    @staticmethod
    def get_row_format_link_commit() -> bool:
        """
        Get the value controlling whether the row format should include a 'Commit:' prefix when linking to direct commit.
        """
        return get_action_input(ROW_FORMAT_LINK_COMMIT, "true").lower() == "true"

    @staticmethod
    def validate_inputs():
        """
        Validates the inputs provided for the release notes generator.
        Logs any validation errors and exits if any are found.
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

        chapters_json = ActionInputs.get_chapters_json()
        try:
            json.loads(chapters_json)
        except json.JSONDecodeError:
            errors.append("Chapters JSON must be a valid JSON string.")

        duplicity_icon = ActionInputs.get_duplicity_icon()
        if not isinstance(duplicity_icon, str) or not duplicity_icon.strip() or len(duplicity_icon) != 1:
            errors.append("Duplicity icon must be a non-empty string and have a length of 1.")

        warnings = ActionInputs.get_warnings()
        ActionInputs.validate_input(warnings, bool, "Warnings must be a boolean.", errors)

        published_at = ActionInputs.get_published_at()
        ActionInputs.validate_input(published_at, bool, "Published at must be a boolean.", errors)

        skip_release_notes_label = ActionInputs.get_skip_release_notes_label()
        if not isinstance(skip_release_notes_label, str) or not skip_release_notes_label.strip():
            errors.append("Skip release notes label must be a non-empty string.")

        verbose = ActionInputs.get_verbose()
        ActionInputs.validate_input(verbose, bool, "Verbose logging must be a boolean.", errors)

        row_format_link_pr = ActionInputs.get_row_format_link_pr()
        ActionInputs.validate_input(row_format_link_pr, bool, "'row-format-link-pr' value must be a boolean.", errors)

        row_format_link_commit = ActionInputs.get_row_format_link_commit()
        ActionInputs.validate_input(row_format_link_commit, bool, "'row-format-link-commit' value must be a boolean.", errors)

        # Features
        print_empty_chapters = ActionInputs.get_print_empty_chapters()
        ActionInputs.validate_input(print_empty_chapters, bool, "Print empty chapters must be a boolean.", errors)

        row_format_issue = ActionInputs.get_row_format_issue()
        if not isinstance(row_format_issue, str) or not row_format_issue.strip():
            errors.append("Issue row format must be a non-empty string.")

        errors.extend(detect_row_format_invalid_keywords(row_format_issue))

        row_format_pr = ActionInputs.get_row_format_pr()
        if not isinstance(row_format_pr, str) or not row_format_pr.strip():
            errors.append("PR Row format must be a non-empty string.")

        errors.extend(detect_row_format_invalid_keywords(row_format_pr, row_type="PR"))

        row_format_commit = ActionInputs.get_row_format_commit()
        if not isinstance(row_format_commit, str) or not row_format_commit.strip():
            errors.append("Commit Row format must be a non-empty string.")

        errors.extend(detect_row_format_invalid_keywords(row_format_commit, row_type="Commit"))

        # Log errors if any
        if errors:
            for error in errors:
                logger.error(error)
            sys.exit(1)

        logging.debug("Repository: %s/%s", owner, repo_name)
        logger.debug("Tag name: %s", tag_name)
        logger.debug("Chapters JSON: %s", chapters_json)
        logger.debug("Duplication scope: %s", ActionInputs.get_duplicity_scope())
        logger.debug("Duplication icon: %s", duplicity_icon)
        logger.debug("Warnings: %s", warnings)
        logger.debug("Published at: %s", published_at)
        logger.debug("Skip release notes label: %s", skip_release_notes_label)
        logger.debug("Print empty chapters: %s", print_empty_chapters)
        logger.debug("Verbose logging: %s", verbose)
        logger.debug("Github repository: %s", repository_id)
        logger.debug("Row format issue: %s", row_format_issue)
        logger.debug("Row format PR: %s", row_format_pr)
        logger.debug("Row format commit: %s", row_format_commit)
        logger.debug("Row format link PR: %s", row_format_link_pr)
        logger.debug("Row format link commit: %s", row_format_commit)
