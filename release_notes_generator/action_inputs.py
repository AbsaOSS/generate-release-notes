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

import json
import logging
import os
import sys

from release_notes_generator.utils.constants import (GITHUB_REPOSITORY, GITHUB_TOKEN, TAG_NAME, CHAPTERS, PUBLISHED_AT,
                                                     SKIP_RELEASE_NOTES_LABEL, VERBOSE, WARNINGS, RUNNER_DEBUG,
                                                     PRINT_EMPTY_CHAPTERS, CHAPTERS_TO_PR_WITHOUT_ISSUE)
from release_notes_generator.utils.gh_action import get_action_input


class ActionInputs:
    @staticmethod
    def get_github_repository() -> str:
        return get_action_input(GITHUB_REPOSITORY)

    @staticmethod
    def get_github_token() -> str:
        return get_action_input(GITHUB_TOKEN)

    @staticmethod
    def get_tag_name() -> str:
        return get_action_input(TAG_NAME)

    @staticmethod
    def get_chapters_json() -> str:
        return get_action_input(CHAPTERS)

    @staticmethod
    def get_published_at() -> bool:
        return get_action_input(PUBLISHED_AT, "false").lower() == 'true'

    @staticmethod
    def get_skip_release_notes_label() -> str:
        return get_action_input(SKIP_RELEASE_NOTES_LABEL) or 'skip-release-notes'

    @staticmethod
    def get_verbose() -> bool:
        return os.getenv(RUNNER_DEBUG, '0') == '1' or get_action_input(VERBOSE).lower() == 'true'

    # Features
    @staticmethod
    def get_warnings() -> bool:
        return get_action_input(WARNINGS, "true").lower() == 'true'

    @staticmethod
    def get_print_empty_chapters() -> bool:
        return get_action_input(PRINT_EMPTY_CHAPTERS, "true").lower() == 'true'

    @staticmethod
    def get_chapters_to_pr_without_issue() -> bool:
        return get_action_input(CHAPTERS_TO_PR_WITHOUT_ISSUE, "true").lower() == 'true'

    # pylint: disable=too-many-branches
    @staticmethod
    def validate_inputs():
        """
        Validates the inputs provided for the release notes generator.
        Logs any validation errors and exits if any are found.
        """
        errors = []

        repository_id = ActionInputs.get_github_repository()
        if '/' in repository_id:
            owner, repo_name = ActionInputs.get_github_repository().split('/')
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

        warnings = ActionInputs.get_warnings()
        if not isinstance(warnings, bool):
            errors.append("Warnings must be a boolean.")

        published_at = ActionInputs.get_published_at()
        if not isinstance(published_at, bool):
            errors.append("Published at must be a boolean.")

        skip_release_notes_label = ActionInputs.get_skip_release_notes_label()
        if not isinstance(skip_release_notes_label, str) or not skip_release_notes_label.strip():
            errors.append("Skip release notes label must be a non-empty string.")

        verbose = ActionInputs.get_verbose()
        if not isinstance(verbose, bool):
            errors.append("Verbose logging must be a boolean.")

        # Features
        print_empty_chapters = ActionInputs.get_print_empty_chapters()
        if not isinstance(print_empty_chapters, bool):
            errors.append("Print empty chapters must be a boolean.")

        chapters_to_pr_without_issue = ActionInputs.get_chapters_to_pr_without_issue()
        if not isinstance(chapters_to_pr_without_issue, bool):
            errors.append("Chapters to PR without issue must be a boolean.")

        # Log errors if any
        if errors:
            for error in errors:
                logging.error(error)
            sys.exit(1)

        logging.debug('Repository: %s/%s', owner, repo_name)
        logging.debug('Tag name: %s', tag_name)
        logging.debug('Chapters JSON: %s', chapters_json)
        logging.debug('Published at: %s', published_at)
        logging.debug('Skip release notes label: %s', skip_release_notes_label)
        logging.debug('Verbose logging: %s', verbose)
        logging.debug('Warnings: %s', warnings)
        logging.debug('Print empty chapters: %s', print_empty_chapters)
        logging.debug('Chapters to PR without issue: %s', chapters_to_pr_without_issue)
