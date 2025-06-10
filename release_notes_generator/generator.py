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

    def generate(self) -> Optional[str]:
        """
        Generates the Release Notes for a given repository.

        @return: The generated release notes as a string, or None if the repository could not be found.
        """
        miner = DataMiner(self._github_instance, self._rate_limiter)
        data = miner.mine_data()
        if data.is_empty():
            return None
        issues_filter, pulls_filter, commits_filter = data.issues, data.pull_requests, data.commits
        if data.release is not None:
            logger.info("Starting issue, prs and commit reduction by the latest release since time.")

            # filter out closed Issues before the date
            issues_filter = list(
                filter(lambda issue: issue.closed_at is not None and issue.closed_at >= data.since, list(data.issues))
            )
            logger.debug("Count of issues reduced from %d to %d", len(list(data.issues)), len(issues_filter))

            # filter out merged PRs and commits before the date
            pulls_filter = list(
                filter(
                    lambda pull: pull.merged_at is not None and pull.merged_at >= data.since, list(data.pull_requests)
                )
            )
            logger.debug("Count of pulls reduced from %d to %d", len(list(data.pull_requests)), len(pulls_filter))

            commits_filter = list(filter(lambda commit: commit.commit.author.date > data.since, list(data.commits)))
            logger.debug("Count of commits reduced from %d to %d", len(list(data.commits)), len(commits_filter))

        changelog_url: str = get_change_url(
            tag_name=ActionInputs.get_tag_name(), repository=data.repository, git_release=data.release
        )

        rls_notes_records: dict[int, Record] = RecordFactory.generate(
            github=self._github_instance,
            repo=data.repository,
            issues=list(issues_filter),  # PaginatedList --> list
            pulls=list(pulls_filter),  # PaginatedList --> list
            commits=list(commits_filter),  # PaginatedList --> list
        )

        release_notes_builder = ReleaseNotesBuilder(
            records=rls_notes_records,
            custom_chapters=self.custom_chapters,
            changelog_url=changelog_url,
        )

        return release_notes_builder.build()
