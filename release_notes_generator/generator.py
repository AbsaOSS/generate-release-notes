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

from release_notes_generator.filter import FilterByRelease
from release_notes_generator.miner import DataMiner
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.builder.base_builder import ReleaseNotesBuilder
from release_notes_generator.builder.default_builder import DefaultReleaseNotesBuilder
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.model.record import Record
from release_notes_generator.record.default_record_factory import DefaultRecordFactory
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

        @Parameters:
        - filterer: An instance of Filter that will be used to filter the mined data.

        @return: The generated release notes as a string, or None if the repository could not be found.
        """
        miner = DataMiner(self._github_instance, self._rate_limiter)
        data = miner.mine_data()
        if data.is_empty():
            return None

        filterer = FilterByRelease()
        data_filtered_by_release = filterer.filter(data=data)

        changelog_url: str = get_change_url(
            tag_name=ActionInputs.get_tag_name(),
            repository=data_filtered_by_release.repository,
            git_release=data_filtered_by_release.release,
        )

        assert data_filtered_by_release.repository is not None, "Repository must not be None"

        # get record factory instance in dependency on selected regime
        record_factory: RecordFactory = DefaultRecordFactory()
        # This is a placeholder for future regimes - will be added in following issue
        # match ActionInputs.get_regime():
        #     case "TODO":
        #         record_factory = TBD

        rls_notes_records: dict[int | str, Record] = record_factory.generate(
            github=self._github_instance, data=data_filtered_by_release
        )

        return self._get_rls_notes_builder(rls_notes_records, changelog_url, self.custom_chapters).build()

    def _get_rls_notes_builder(
        self, records: dict[int | str, Record], changelog_url: str, custom_chapters: CustomChapters
    ) -> ReleaseNotesBuilder:

        return DefaultReleaseNotesBuilder(
            records=records,
            custom_chapters=custom_chapters,
            changelog_url=changelog_url,
        )
