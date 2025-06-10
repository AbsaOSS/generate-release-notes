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
This module contains logic for mining data from GitHub, including issues, pull requests, commits, and releases.
"""

import logging
import sys
from typing import Optional

import semver
from github import Github
from github.GitRelease import GitRelease

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.MinedData import MinedData
from release_notes_generator.utils.constants import ISSUE_STATE_ALL, PR_STATE_CLOSED
from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter

logger = logging.getLogger(__name__)


class DataMiner:
    """
    Class responsible for mining data from GitHub.
    """

    def __init__(self, github_instance: Github, rate_limiter: GithubRateLimiter):
        self.github_instance = github_instance
        self._safe_call = safe_call_decorator(rate_limiter)

    def mine_data(self) -> MinedData:
        logger.info("Starting data mining from GitHub...")
        data = MinedData()

        data.repository = self._safe_call(self.github_instance.get_repo)(ActionInputs.get_github_repository())
        if data.repository is None:
            logger.error("Repository not found: %s", ActionInputs.get_github_repository())
            return data

        data.release = self._get_latest_release(data)

        self._get_issues(data)

        # pulls and commits, and then reduce them by the latest release since time
        data.pull_requests = self._safe_call(data.repository.get_pulls)(state=PR_STATE_CLOSED)
        data.commits = list(self._safe_call(data.repository.get_commits)())

        logger.info("Data mining from GitHub completed.")
        return data

    def _get_latest_release(self, data: MinedData) -> Optional[GitRelease]:
        """
        Get the latest release of the repository.

        @param repo: The repository to get the latest release from.
        @return: The latest release of the repository, or None if no releases are found.
        """
        rls: Optional[GitRelease] = None

        # check if from-tag name is defined
        if ActionInputs.is_from_tag_name_defined():
            logger.info("Getting latest release by from-tag name %s", ActionInputs.get_from_tag_name())
            rls = self._safe_call(data.repository.get_release)(ActionInputs.get_from_tag_name())

            if rls is None:
                logger.info(
                    "Latest release not found for received from-tag %s. Ending!", ActionInputs.get_from_tag_name()
                )
                sys.exit(1)

        else:
            logger.info("Getting latest release by semantic ordering (could not be the last one by time).")
            gh_releases: list = list(self._safe_call(data.repository.get_releases)())
            rls = self.__get_latest_semantic_release(gh_releases)

            if rls is None:
                logger.info("Latest release not found for %s. 1st release for repository!", data.repository.full_name)
                return None

        if rls is not None:
            logger.debug(
                "Latest release with tag:'%s' created_at: %s, published_at: %s",
                rls.tag_name,
                rls.created_at,
                rls.published_at,
            )

        return rls

    def _get_issues(self, data: MinedData):
        """
        Fetches issues from the repository and adds them to the mined data.
        """
        logger.info("Fetching issues from repository...")
        # get all issues
        if data.release is None:
            data.issues = self._safe_call(data.repository.get_issues)(state=ISSUE_STATE_ALL)
        else:
            # default is repository creation date if no releases OR created_at of latest release
            data.since = data.release.created_at if data.release else data.repository.created_at
            if data.release and ActionInputs.get_published_at():
                data.since = data.release.published_at

            data.issues = self._safe_call(data.repository.get_issues)(state=ISSUE_STATE_ALL, since=data.since)

        logger.info("Fetched %d issues", len(data.issues))

    def __get_latest_semantic_release(self, releases) -> Optional[GitRelease]:
        published_releases = [release for release in releases if not release.draft and not release.prerelease]
        latest_version: Optional[semver.Version] = None
        rls: Optional[GitRelease] = None

        for release in published_releases:
            try:
                version_str = release.tag_name.lstrip("v")
                current_version: Optional[semver.Version] = semver.VersionInfo.parse(version_str)
            except ValueError:
                logger.debug("Skipping invalid value of version tag: %s", release.tag_name)
                continue
            except TypeError:
                logger.debug("Skipping invalid type of version tag: %s", release.tag_name)
                continue

            if latest_version is None or current_version > latest_version:  # type: ignore[operator]
                # mypy: check for None is done first
                latest_version = current_version
                rls = release

        return rls
