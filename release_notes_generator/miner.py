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
import traceback
from typing import Optional

import semver
from github import Github
from github.GitRelease import GitRelease
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.model.pull_request_record import PullRequestRecord
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

    def check_repository_exists(self) -> bool:
        """
        Checks if the specified GitHub repository exists.

        Returns:
            bool: True if the repository exists, False otherwise.
        """
        repo: Repository = self._safe_call(self.github_instance.get_repo)(ActionInputs.get_github_repository())
        if repo is None:
            logger.error("Repository not found: %s", ActionInputs.get_github_repository())
            return False
        return True

    def get_repository(self, full_name: str) -> Optional[Repository]:
        """
        Retrieves the specified GitHub repository.

        Returns:
            Optional[Repository]: The GitHub repository if found, None otherwise.
        """
        repo: Repository = self._safe_call(self.github_instance.get_repo)(full_name)
        if repo is None:
            logger.error("Repository not found: %s", full_name)
            return None
        return repo

    def mine_data(self) -> MinedData:
        """
        Mines data from GitHub, including repository information, issues, pull requests, commits, and releases.
        """
        logger.info("Starting data mining from GitHub...")
        repo: Optional[Repository] = self.get_repository(ActionInputs.get_github_repository())
        if repo is None:
            raise ValueError("Repository not found")

        data = MinedData(repo)
        data.release = self.get_latest_release(repo)

        self._get_issues(data)

        # pulls and commits, and then reduce them by the latest release since time
        data.pull_requests = list(self._safe_call(repo.get_pulls)(state=PullRequestRecord.PR_STATE_CLOSED))
        data.commits = list(self._safe_call(repo.get_commits)())

        logger.info("Data mining from GitHub completed.")

        logger.info("Filtering duplicated issues from the list of issues...")
        de_duplicated_data = self.__filter_duplicated_issues(data)
        logger.info("Filtering duplicated issues from the list of issues finished.")

        return de_duplicated_data

    def get_latest_release(self, repository: Repository) -> Optional[GitRelease]:
        """
        Get the latest release of the repository.

        @param repository: The repository to get the latest release from.
        @return: The latest release of the repository, or None if no releases are found.
        """

        rls: Optional[GitRelease] = None

        # check if from-tag name is defined
        if ActionInputs.is_from_tag_name_defined():
            logger.info("Getting latest release by from-tag name %s", ActionInputs.get_from_tag_name())
            rls = self._safe_call(repository.get_release)(ActionInputs.get_from_tag_name())

            if rls is None:
                logger.error(
                    "Latest release not found for received from-tag %s. Ending!", ActionInputs.get_from_tag_name()
                )
                sys.exit(1)

        else:
            logger.info("Getting latest release by semantic ordering (could not be the last one by time).")
            gh_releases: list = list(self._safe_call(repository.get_releases)())
            rls = self.__get_latest_semantic_release(gh_releases)

            if rls is None:
                logger.info("Latest release not found for %s. 1st release for repository!", repository.full_name)
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
        Populate data.issues.

        Logic:
          - If no release: fetch all issues.
          - If release exists: fetch issues updated since the release timestamp AND all currently open issues
            (to include long-lived open issues not updated recently). De-duplicate by issue.number.
        """
        assert data.home_repository is not None, "Repository must not be None"
        logger.info("Fetching issues from repository...")

        if data.release is None:
            data.issues = list(self._safe_call(data.home_repository.get_issues)(state=IssueRecord.ISSUE_STATE_ALL))
            logger.info("Fetched %d issues", len(data.issues))
            return

        # Derive 'since' from release
        prefer_published = ActionInputs.get_published_at()
        data.since = (
            data.release.published_at
            if prefer_published and getattr(data.release, "published_at", None)
            else data.release.created_at
        )
        issues_since = self._safe_call(data.home_repository.get_issues)(
            state=IssueRecord.ISSUE_STATE_ALL,
            since=data.since,
        )
        open_issues = self._safe_call(data.home_repository.get_issues)(
            state=IssueRecord.ISSUE_STATE_OPEN,
        )

        issues_since = list(issues_since or [])
        open_issues = list(open_issues or [])

        by_number = {}
        for issue in issues_since:
            num = getattr(issue, "number", None)
            if num is not None and num not in by_number:
                by_number[num] = issue
        for issue in open_issues:
            num = getattr(issue, "number", None)
            if num is not None and num not in by_number:
                by_number[num] = issue

        data.issues = list(by_number.values())
        logger.info("Fetched %d issues (deduplicated).", len(data.issues))

    @staticmethod
    def __get_latest_semantic_release(releases) -> Optional[GitRelease]:
        published_releases = [release for release in releases if not release.draft and not release.prerelease]
        latest_version: Optional[semver.Version] = None
        rls: Optional[GitRelease] = None

        for release in published_releases:
            try:
                version_str = release.tag_name.lstrip("v")
                current_version: Optional[semver.Version] = semver.VersionInfo.parse(version_str)
            except ValueError:
                logger.error("Skipping invalid value of version tag: %s", release.tag_name)
                continue
            except TypeError as error:
                logger.error("Skipping invalid type of version tag: %s | Error: %s", release.tag_name, str(error))
                logger.error("Full traceback:\n%s", traceback.format_exc())
                continue

            if latest_version is None or current_version > latest_version:  # type: ignore[operator]
                # mypy: check for None is done first
                latest_version = current_version
                rls = release

        return rls

    @staticmethod
    def __filter_duplicated_issues(data: MinedData) -> "MinedData":
        """
        Filters out duplicated issues from the list of issues.
        This method address problem in output of GitHub API where issues list contains PR values.

        Parameters:
            - data (MinedData): The mined data containing issues and pull requests.

        Returns:
            - MinedData: The mined data with duplicated issues removed.
        """
        pr_numbers = {pr.number for pr in data.pull_requests}
        filtered_issues = [issue for issue in data.issues if issue.number not in pr_numbers]

        logger.debug("Duplicated issues removed: %s", len(data.issues) - len(filtered_issues))

        data.issues = filtered_issues

        return data
