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

logger = logging.getLogger(__name__)


def get_change_url(
    tag_name: str, repository: Optional[Repository] = None, git_release: Optional[GitRelease] = None
) -> str:
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


_SEMVER_SHORT_RE = re.compile(
    r"""
    ^\s*                # optional leading whitespace
    v?                  # optional leading 'v'
    (?P<major>\d+)      # major
    \.                  # dot
    (?P<minor>\d+)      # minor
    (?:\.(?P<patch>\d+))?  # optional .patch
    \s*$                # optional trailing whitespace
""",
    re.VERBOSE,
)


def normalize_version_tag(tag: str) -> str:
    """
    Normalize a tag to full 'vMAJOR.MINOR.PATCH' form.

    Accepts:
      - 'v1.2.3'  -> 'v1.2.3'
      - 'v1.2'    -> 'v1.2.0'
      - '1.2.3'   -> 'v1.2.3'
      - '1.2'     -> 'v1.2.0'

    Returns empty string if input is empty/whitespace.
    Raises ValueError on malformed versions.
    """
    if not tag or tag.strip() == "":
        return ""

    m = _SEMVER_SHORT_RE.match(tag)
    if not m:
        raise ValueError(
            f"Invalid version tag format: {tag!r}. " "Expected vMAJOR.MINOR[.PATCH], e.g. 'v0.2' or 'v0.2.0'."
        )

    major = int(m.group("major"))
    minor = int(m.group("minor"))
    patch = int(m.group("patch")) if m.group("patch") is not None else 0

    return f"v{major}.{minor}.{patch}"
