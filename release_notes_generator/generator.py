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
This module contains the ReleaseNotesGenerator class which is responsible for generating
the Release Notes output.
"""

import logging
import sys

from typing import Optional

import semver

from github import Github
from github.GitRelease import GitRelease
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.builder import ReleaseNotesBuilder
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.model.record import Record
from release_notes_generator.record.record_factory import RecordFactory
from release_notes_generator.utils.constants import ISSUE_STATE_ALL
from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.utils import get_change_url

logger = logging.getLogger(__name__)


class ReleaseNotesGenerator:
    """
    A class representing the Release Notes Generator.
    The class uses several helper methods to fetch required data from GitHub, and generate the markdown pages
    as the output of GH action.
    """

    def __init__(self, github_instance: Github, custom_chapters: CustomChapters):
        self._github_instance = github_instance
        self._custom_chapters = custom_chapters
        self._rate_limiter = GithubRateLimiter(self.github_instance)
        self._safe_call = safe_call_decorator(self._rate_limiter)

    @property
    def github_instance(self) -> Github:
        """Getter for the GitHub instance."""
        return self._github_instance

    @property
    def custom_chapters(self) -> CustomChapters:
        """Getter for the CustomChapters instance."""
        return self._custom_chapters

    @property
    def rate_limiter(self) -> GithubRateLimiter:
        """Getter for the GithubRateLimiter instance."""
        return self._rate_limiter

    def generate(self) -> Optional[str]:
        """
        Generates the Release Notes for a given repository.

        @return: The generated release notes as a string, or None if the repository could not be found.
        """
        # get the repository
        repo = self._safe_call(self.github_instance.get_repo)(ActionInputs.get_github_repository())
        if repo is None:
            return None

        # get the latest release
        rls: Optional[GitRelease] = self.get_latest_release(repo)

        # get all issues
        if rls is None:
            issues = issues_all = self._safe_call(repo.get_issues)(state=ISSUE_STATE_ALL)
        else:
            # default is repository creation date if no releases OR created_at of latest release
            since = rls.created_at if rls else repo.created_at
            if rls and ActionInputs.get_published_at():
                since = rls.published_at

            issues = issues_all = self._safe_call(repo.get_issues)(state=ISSUE_STATE_ALL, since=since)

        # pulls and commits, and then reduce them by the latest release since time
        pulls = pulls_all = self._safe_call(repo.get_pulls)(state="closed")
        commits = commits_all = list(self._safe_call(repo.get_commits)())

        if rls is not None:
            logger.info("Starting issue, prs and commit reduction by the latest release since time.")

            # filter out closed Issues before the date
            issues = list(
                filter(lambda issue: issue.closed_at is not None and issue.closed_at >= since, list(issues_all))
            )
            logger.debug("Count of issues reduced from %d to %d", len(list(issues_all)), len(issues))

            # filter out merged PRs and commits before the date
            pulls = list(filter(lambda pull: pull.merged_at is not None and pull.merged_at >= since, list(pulls_all)))
            logger.debug("Count of pulls reduced from %d to %d", len(list(pulls_all)), len(pulls))

            commits = list(filter(lambda commit: commit.commit.author.date > since, list(commits_all)))
            logger.debug("Count of commits reduced from %d to %d", len(list(commits_all)), len(commits))

        changelog_url: str = get_change_url(tag_name=ActionInputs.get_tag_name(), repository=repo, git_release=rls)

        rls_notes_records: dict[int, Record] = RecordFactory.generate(
            github=self.github_instance,
            repo=repo,
            issues=list(issues),  # PaginatedList --> list
            pulls=list(pulls),  # PaginatedList --> list
            commits=list(commits),  # PaginatedList --> list
        )

        release_notes_builder = ReleaseNotesBuilder(
            records=rls_notes_records,
            custom_chapters=self.custom_chapters,
            changelog_url=changelog_url,
        )

        return release_notes_builder.build()

    def get_latest_release(self, repo: Repository) -> Optional[GitRelease]:
        """
        Get the latest release of the repository.

        @param repo: The repository to get the latest release from.
        @return: The latest release of the repository, or None if no releases are found.
        """
        rls: Optional[GitRelease] = None

        # check if from-tag name is defined
        if ActionInputs.is_from_tag_name_defined():
            logger.info("Getting latest release by from-tag name %s", ActionInputs.get_tag_name())
            rls = self._safe_call(repo.get_release)(ActionInputs.get_from_tag_name())

            if rls is None:
                logger.info("Latest release not found for received tag %s. Ending!", ActionInputs.get_from_tag_name())
                sys.exit(1)

        else:
            logger.info("Getting latest release by semantic ordering (could not be the last one by time).")
            gh_releases: list = list(self._safe_call(repo.get_releases)())
            rls = self.__get_latest_semantic_release(gh_releases)

            if rls is None:
                logger.info("Latest release not found for %s. 1st release for repository!", repo.full_name)

        if rls is not None:
            logger.debug(
                "Latest release with tag:'%s' created_at: %s, published_at: %s",
                rls.tag_name,
                rls.created_at,
                rls.published_at,
            )

        return rls

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

            if latest_version is None or current_version > latest_version:  # type: ignore[operator]    # check for None is done first
                latest_version = current_version
                rls = release

        return rls
