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

from release_notes_generator.action_inputs import ActionInputs
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

        Parameters:
            data (MinedData): The mined data containing issues, pull requests, commits, and release information.

        Returns:
            MinedData: The filtered mined data.
        """
        md = MinedData()
        md.repository = data.repository
        md.release = data.release
        md.since = data.since

        if data.release is not None:
            logger.info("Starting issue, prs and commit reduction by the latest release since time.")

            issues_list = self._filter_issues(data)
            logger.debug("Count of issues reduced from %d to %d", len(data.issues), len(issues_list))

            # filter out merged PRs and commits before the date
            pulls_seen: set[int] = set()
            pulls_list: list = []
            for pull in data.pull_requests:
                if (pull.merged_at is not None and pull.merged_at >= data.since) or (
                    pull.closed_at is not None and pull.closed_at >= data.since
                ):
                    if pull.number not in pulls_seen:
                        pulls_seen.add(pull.number)
                        pulls_list.append(pull)
            logger.debug("Count of pulls reduced from %d to %d", len(data.pull_requests), len(pulls_list))

            commits_list = list(filter(lambda commit: commit.commit.author.date > data.since, data.commits))
            logger.debug("Count of commits reduced from %d to %d", len(data.commits), len(commits_list))

            md.issues = issues_list
            md.pull_requests = pulls_list
            md.commits = commits_list

            logger.debug(
                "Input data. Issues: %d, Pull Requests: %d, Commits: %d",
                len(data.issues),
                len(data.pull_requests),
                len(data.commits),
            )
            logger.debug(
                "Filtered data. Issues: %d, Pull Requests: %d, Commits: %d",
                len(md.issues),
                len(md.pull_requests),
                len(md.commits),
            )
        else:
            md.issues = deepcopy(data.issues)
            md.pull_requests = deepcopy(data.pull_requests)
            md.commits = deepcopy(data.commits)

        return md

    def _filter_issues(self, data: MinedData) -> list:
        """
        Filter issues based on the selected regime.

        @param data: The mined data containing issues.
        @return: The filtered list of issues.
        """
        # Currently, only the default regime is implemented.
        if ActionInputs.get_regime() == ActionInputs.REGIME_ISSUE_HIERARCHY:
            return self._filter_issues_issue_hierarchy(data)


        logger.debug("Used default issue filtering regime.")
        return self._filter_issues_default(data)

    def _filter_issues_default(self, data: MinedData) -> list:
        """
        Default filtering for issues: filter out closed issues before the release date.

        @param data: The mined data containing issues.
        @return: The filtered list of issues.
        """
        return [
            issue
            for issue in data.issues
            if (issue.closed_at is None) or (issue.closed_at >= data.since)
        ]

    def _filter_issues_issue_hierarchy(self, data: MinedData) -> list:
        """
        Filtering for issues in the 'issue-hierarchy' regime:
        - filter out closed issues before the release date
        - keep open issues
        - keep issues with types defined in `issue-type-weights`

        @param data: The mined data containing issues.
        @return: The filtered list of issues.
        """
        issue_types = ActionInputs.get_issue_type_weights()
        return list(
            filter(
                lambda issue: (
                    (issue.closed_at is not None and issue.closed_at >= data.since)
                    or (issue.state == "open")
                    or (issue.type is not None and issue.type.name in issue_types)
                ),
                data.issues,
            )
        )
