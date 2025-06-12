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

from typing import Optional

from github import Github

from release_notes_generator.model.MinedData import MinedData
from release_notes_generator.miner import DataMiner
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.builder import ReleaseNotesBuilder
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.model.record import Record
from release_notes_generator.record.record_factory import RecordFactory
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
        self._rate_limiter = GithubRateLimiter(self._github_instance)
        self._custom_chapters = custom_chapters

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

    def _filter_by_release(self, data: MinedData) -> None:
        """
        Filters issues, pull requests, and commits based on the latest release date.
        If the release is not None, it filters out closed issues, merged pull requests, and commits
        that occurred before the release date.
        @param data: The mined data containing issues, pull requests, commits, and release information.
        """
        issues_list = data.issues
        pulls_list = data.pull_requests
        commits_list = data.commits

        if data.release is not None:
            logger.info("Starting issue, prs and commit reduction by the latest release since time.")

            # filter out closed Issues before the date
            data.issues = list(
                filter(lambda issue: issue.closed_at is not None and issue.closed_at >= data.since, issues_list)
            )
            logger.debug("Count of issues reduced from %d to %d", len(issues_list), len(data.issues))

            # filter out merged PRs and commits before the date
            data.pull_requests = list(
                filter(lambda pull: pull.merged_at is not None and pull.merged_at >= data.since, pulls_list)
            )
            logger.debug("Count of pulls reduced from %d to %d", len(pulls_list), len(data.pull_requests))

            data.commits = list(filter(lambda commit: commit.commit.author.date > data.since, commits_list))
            logger.debug("Count of commits reduced from %d to %d", len(commits_list), len(data.commits))

    def generate(self) -> Optional[str]:
        """
        Generates the Release Notes for a given repository.

        @return: The generated release notes as a string, or None if the repository could not be found.
        """
        miner = DataMiner(self._github_instance, self._rate_limiter)
        data = miner.mine_data()
        if data.is_empty():
            return None

        self._filter_by_release(data)

        changelog_url: str = get_change_url(
            tag_name=ActionInputs.get_tag_name(), repository=data.repository, git_release=data.release
        )

        assert data.repository is not None, "Repository must not be None"

        rls_notes_records: dict[int, Record] = RecordFactory.generate(
            github=self._github_instance,
            repo=data.repository,
            issues=data.issues,
            pulls=data.pull_requests,
            commits=data.commits,
        )

        release_notes_builder = ReleaseNotesBuilder(
            records=rls_notes_records,
            custom_chapters=self.custom_chapters,
            changelog_url=changelog_url,
        )

        return release_notes_builder.build()
