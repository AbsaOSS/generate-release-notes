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
This module contains the main script for the Release Notes Generator GH Action.
It sets up logging, loads action inputs, generates the release notes and sets the output
for the GH Action.
"""

import logging

from github import Github, Auth

from release_notes_generator.generator import ReleaseNotesGenerator
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.gh_action import set_action_output
from release_notes_generator.utils.logging_config import setup_logging
from release_notes_generator.filter import FilterByRelease


def run() -> None:
    """
    The main function to run the Release Notes Generator.

    @return: None
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting 'Release Notes Generator' GitHub Action")

    # Authenticate with GitHub
    py_github = Github(auth=Auth.Token(token=ActionInputs.get_github_token()), per_page=100)

    ActionInputs.validate_inputs()
    # Load custom chapters configuration
    custom_chapters = CustomChapters(print_empty_chapters=ActionInputs.get_print_empty_chapters()).from_yaml_array(
        ActionInputs.get_chapters()
    )

    generator = ReleaseNotesGenerator(py_github, custom_chapters)
    filterer = FilterByRelease()
    rls_notes = generator.generate(filterer)
    logger.debug("Generated release notes: \n%s", rls_notes)

    # Set the output for the GitHub Action
    set_action_output(
        "release-notes",
        rls_notes if rls_notes is not None else "Failed to generate release notes. See logs for details.",
    )
    logger.info("GitHub Action 'Release Notes Generator' completed successfully")


if __name__ == "__main__":
    run()
