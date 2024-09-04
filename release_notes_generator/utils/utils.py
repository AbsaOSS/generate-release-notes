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
from typing import Optional

from github.GitRelease import GitRelease
from github.Repository import Repository

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
