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

from release_notes_generator.utils.gh_action import get_action_input


class ActionInputs:
    GITHUB_REPOSITORY = 'GITHUB_REPOSITORY'
    GITHUB_TOKEN = 'github-token'
    TAG_NAME = 'tag-name'
    CHAPTERS = 'chapters'
    WARNINGS = 'warnings'
    PUBLISHED_AT = 'published-at'
    SKIP_RELEASE_NOTES_LABEL = 'skip-release-notes-label'
    PRINT_EMPTY_CHAPTERS = 'print-empty-chapters'
    CHAPTERS_TO_PR_WITHOUT_ISSUE = 'chapters-to-pr-without-issue'
    VERBOSE = 'verbose'
    RUNNER_DEBUG = 'RUNNER_DEBUG'

    @staticmethod
    def get_github_repository() -> str:
        return get_action_input(ActionInputs.GITHUB_REPOSITORY)

    @staticmethod
    def get_github_token() -> str:
        return get_action_input(ActionInputs.GITHUB_TOKEN)

    @staticmethod
    def get_tag_name() -> str:
        return get_action_input(ActionInputs.TAG_NAME)

    @staticmethod
    def get_chapters_json() -> str:
        return get_action_input(ActionInputs.CHAPTERS)

    @staticmethod
    def get_warnings() -> bool:
        return get_action_input(ActionInputs.WARNINGS).lower() == 'true'

    @staticmethod
    def get_published_at() -> bool:
        return get_action_input(ActionInputs.PUBLISHED_AT).lower() == 'true'

    @staticmethod
    def get_skip_release_notes_label() -> str:
        return get_action_input(ActionInputs.SKIP_RELEASE_NOTES_LABEL) or 'skip-release-notes'

    @staticmethod
    def get_print_empty_chapters() -> bool:
        return get_action_input(ActionInputs.PRINT_EMPTY_CHAPTERS).lower() == 'true'

    @staticmethod
    def get_chapters_to_pr_without_issue() -> bool:
        return get_action_input(ActionInputs.CHAPTERS_TO_PR_WITHOUT_ISSUE).lower() == 'true'

    @staticmethod
    def get_verbose() -> bool:
        return os.getenv('RUNNER_DEBUG', 0) == 1 or get_action_input(ActionInputs.VERBOSE).lower() == 'true'

    @staticmethod
    def validate_inputs():
        """
        Validates the inputs provided for the release notes generator.

        :raises ValueError: If any of the inputs are invalid.
        """
        repository_id = ActionInputs.get_github_repository()
        if '/' in repository_id:
            owner, repo_name = ActionInputs.get_github_repository().split('/')
        else:
            owner = repo_name = ""

        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("Owner must be a non-empty string.")

        if not isinstance(repo_name, str) or not repo_name.strip():
            raise ValueError("Repo name must be a non-empty string.")

        tag_name = ActionInputs.get_tag_name()
        if not isinstance(tag_name, str) or not tag_name.strip():
            raise ValueError("Tag name must be a non-empty string.")

        try:
            chapters_json = ActionInputs.get_chapters_json()
            json.loads(chapters_json)
        except json.JSONDecodeError:
            raise ValueError("Chapters JSON must be a valid JSON string.")

        warnings = ActionInputs.get_warnings()
        if not isinstance(warnings, bool):
            raise ValueError("Warnings must be a boolean.")

        published_at = ActionInputs.get_published_at()
        if not isinstance(published_at, bool):
            raise ValueError("Published at must be a boolean.")

        skip_release_notes_label = ActionInputs.get_skip_release_notes_label()
        if not isinstance(skip_release_notes_label, str) or not skip_release_notes_label.strip():
            raise ValueError("Skip release notes label must be a non-empty string.")

        print_empty_chapters = ActionInputs.get_print_empty_chapters()
        if not isinstance(print_empty_chapters, bool):
            raise ValueError("Print empty chapters must be a boolean.")

        chapters_to_pr_without_issue = ActionInputs.get_chapters_to_pr_without_issue()
        if not isinstance(chapters_to_pr_without_issue, bool):
            raise ValueError("Chapters to PR without issue must be a boolean.")

        verbose = ActionInputs.get_verbose()
        if not isinstance(verbose, bool):
            raise ValueError("Verbose logging must be a boolean.")

        logging.debug(f'Repository: {owner}/{repo_name}')
        logging.debug(f'Tag name: {tag_name}')
        logging.debug(f'Chapters JSON: {chapters_json}')
        logging.debug(f'Warnings: {warnings}')
        logging.debug(f'Published at: {published_at}')
        logging.debug(f'Skip release notes label: {skip_release_notes_label}')
        logging.debug(f'Print empty chapters: {print_empty_chapters}')
        logging.debug(f'Chapters to PR without issue: {chapters_to_pr_without_issue}')
        logging.debug(f'Verbose logging: {verbose}')
