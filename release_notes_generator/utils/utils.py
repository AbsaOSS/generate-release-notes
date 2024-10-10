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
This module contains utility functions for generating release notes.
"""

import logging
import re

from typing import Optional

from github.GitRelease import GitRelease
from github.Repository import Repository

from release_notes_generator.utils.constants import (
    SUPPORTED_ROW_ISSUE_FORMAT_KEYS,
    SUPPORTED_ROW_PR_FORMAT_KEYS,
    SUPPORTED_ROW_COMMIT_FORMAT_KEYS,
)
from release_notes_generator.utils.exceptions import NotSupportedException

logger = logging.getLogger(__name__)


def get_change_url(
    tag_name: str, repository: Optional[Repository] = None, git_release: Optional[GitRelease] = None
) -> Optional[str]:
    """
    Generates a URL for viewing changes associated with a given tag name in a GitHub repository.

    @param tag_name: The tag name for which the change URL is to be generated.
    @param repository: An optional Repository. If given, this repository is used instead current one.
    @param git_release: An Optional GitRelease. If given, URL compares this release with the tag name.
    @return: An optional string containing the URL to view the changes. Returns a None if the repository is not set.
    """
    if not repository:
        logger.error("Get change url failed. Repository is not set.")
        return ""

    repo = repository
    rls = git_release

    if rls is None:
        # If there is no latest release, create a URL pointing to all commits
        changelog_url = f"https://github.com/{repo.full_name}/commits/{tag_name}"
    else:
        # If there is a latest release, create a URL pointing to commits since the latest release
        changelog_url = f"https://github.com/{repo.full_name}/compare/{rls.tag_name}...{tag_name}"

    return changelog_url


def detect_row_format_invalid_keywords(row_format: str, row_type: str = "Issue") -> list[str]:
    """
    Detects invalid keywords in the row format.

    @param row_format: The row format to be checked for invalid keywords.
    @param row_type: The type of row format. Default is "Issue".
    @return: A list of errors if invalid keywords are found, otherwise an empty list.
    """
    errors = []
    keywords_in_braces = re.findall(r"\{(.*?)\}", row_format)
    match row_type:
        case "Issue":
            supported_keys = SUPPORTED_ROW_ISSUE_FORMAT_KEYS
        case "PR":
            supported_keys = SUPPORTED_ROW_PR_FORMAT_KEYS
        case "Commit":
            supported_keys = SUPPORTED_ROW_COMMIT_FORMAT_KEYS
        case _:
            raise NotSupportedException(f"Row type '{row_type}' is not supported.")

    invalid_keywords = [keyword for keyword in keywords_in_braces if keyword not in supported_keys]
    if invalid_keywords:
        errors.append(
            f"Invalid {row_type} row format '{row_format}'. Invalid keyword(s) found: {', '.join(invalid_keywords)}"
        )
    return errors
