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

"""This module contains the Filter classes which are responsible for filtering records based on various criteria."""

import logging
from copy import deepcopy
from typing import Optional
from release_notes_generator.model.mined_data import MinedData

logger = logging.getLogger(__name__)


class Filter:
    """
    Base class for filtering records.
    """

    def filter(self, data: MinedData) -> MinedData:
        """
        Filter the mined data based on specific criteria.

        @param data: The mined data to filter.
        @return: The filtered mined data.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class FilterByRelease(Filter):
    """
    Filter records based on the release version.
    """

    def __init__(self, release_version: Optional[str] = None):
        self.release_version = release_version

    def filter(self, data: MinedData) -> MinedData:
        """
        Filters issues, pull requests, and commits based on the latest release date.
        If the release is not None, it filters out closed issues, merged pull requests, and commits
        that occurred before the release date.

        @Parameters:
        - data (MinedData): The mined data containing issues, pull requests, commits, and release information.

        @Returns:
        - MinedData: The filtered mined data with issues, pull requests, and commits reduced based on the release date.
        """
        md = MinedData()
        md.repository = data.repository
        md.release = data.release
        md.since = data.since

        if data.release is not None:
            logger.info("Starting issue, prs and commit reduction by the latest release since time.")

            # filter out closed Issues before the date
            issues_list = list(
                filter(lambda issue: issue.closed_at is not None and issue.closed_at >= data.since, data.issues)
            )
            logger.debug("Count of issues reduced from %d to %d", len(data.issues), len(issues_list))

            # filter out merged PRs and commits before the date
            pulls_list = list(
                filter(lambda pull: pull.merged_at is not None and pull.merged_at >= data.since, data.pull_requests)
            )
            logger.debug("Count of pulls reduced from %d to %d", len(data.pull_requests), len(pulls_list))

            commits_list = list(filter(lambda commit: commit.commit.author.date > data.since, data.commits))
            logger.debug("Count of commits reduced from %d to %d", len(data.commits), len(commits_list))

            md.issues = issues_list
            md.pull_requests = pulls_list
            md.commits = commits_list

            logger.debug(
                f"Input data. Issues: {len(data.issues)}, "
                f"Pull Requests: {len(data.pull_requests)}, Commits: {len(data.commits)}"
            )
            logger.debug(
                f"Filtered data. Issues: {len(md.issues)}, "
                f"Pull Requests: {len(md.pull_requests)}, Commits: {len(md.commits)}"
            )
        else:
            md.issues = deepcopy(data.issues)
            md.pull_requests = deepcopy(data.pull_requests)
            md.commits = deepcopy(data.commits)

        return md
