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
from datetime import datetime
from typing import Optional

from github import Github

from release_notes_generator.data.filter import FilterByRelease
from release_notes_generator.data.miner import DataMiner
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.builder.builder import ReleaseNotesBuilder
from release_notes_generator.chapters.custom_chapters import CustomChapters
from release_notes_generator.model.record.record import Record
from release_notes_generator.record.factory.default_record_factory import DefaultRecordFactory
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.record_utils import get_id
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

        @Parameters:
        - filterer: An instance of Filter that will be used to filter the mined data.

        @return: The generated release notes as a string, or None if the repository could not be found.
        """
        miner = DataMiner(self._github_instance, self._rate_limiter)
        if not miner.check_repository_exists():
            return None

        data = miner.mine_data()

        if data.is_empty():
            return None

        self.custom_chapters.since = data.since or datetime.min

        filterer = FilterByRelease()
        data_filtered_by_release = filterer.filter(data=data)

        # data expansion when hierarchy is enabled
        if ActionInputs.get_hierarchy():
            fetched_issues, prs_of_fetched_issues = miner.mine_missing_sub_issues(data_filtered_by_release)
            data_filtered_by_release.issues.update(fetched_issues)
            data_filtered_by_release.pull_requests_of_fetched_cross_issues = prs_of_fetched_issues
        else:
            # fill flat structure with empty lists, no hierarchy
            for i, repo in data_filtered_by_release.issues.items():
                data_filtered_by_release.parents_sub_issues[get_id(i, repo)] = []

        changelog_url: str = get_change_url(
            tag_name=ActionInputs.get_tag_name(),
            repository=data_filtered_by_release.home_repository,
            git_release=data_filtered_by_release.release,
        )

        assert data_filtered_by_release.home_repository is not None, "Repository must not be None"

        rls_notes_records: dict[str, Record] = DefaultRecordFactory(
            github=self._github_instance, home_repository=data_filtered_by_release.home_repository
        ).generate(data=data_filtered_by_release)

        return ReleaseNotesBuilder(
            records=rls_notes_records,
            custom_chapters=self._custom_chapters,
            changelog_url=changelog_url,
        ).build()
