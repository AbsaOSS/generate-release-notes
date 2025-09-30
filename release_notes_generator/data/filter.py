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

from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

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
        md = MinedData(data.home_repository)
        md.release = data.release
        md.since = data.since

        if data.release is not None:
            logger.info("Starting issue, prs and commit reduction by the latest release since time.")

            issues_dict = self._filter_issues(data)
            logger.debug("Count of issues reduced from %d to %d", len(data.issues), len(issues_dict))

            # filter out merged PRs and commits before the date
            pulls_seen: set[int] = set()
            pulls_dict: dict[PullRequest, Repository] = {}
            for pull, repo in data.pull_requests.items():
                if (pull.merged_at is not None and pull.merged_at >= data.since) or (
                    pull.closed_at is not None and pull.closed_at >= data.since
                ):
                    if pull.number not in pulls_seen:
                        pulls_seen.add(pull.number)
                        pulls_dict[pull] = repo
            logger.debug("Count of pulls reduced from %d to %d", len(data.pull_requests.items()), len(pulls_dict.items()))

            commits_dict = {
                commit: repo
                for commit, repo in data.commits.items()
                if commit.commit.author.date > data.since
            }
            logger.debug("Count of commits reduced from %d to %d", len(data.commits.items()), len(commits_dict.items()))

            md.issues = issues_dict
            md.pull_requests = pulls_dict
            md.commits = commits_dict

            logger.debug(
                "Input data. Issues: %d, Pull Requests: %d, Commits: %d",
                len(data.issues.items()),
                len(data.pull_requests.items()),
                len(data.commits.items()),
            )
            logger.debug(
                "Filtered data. Issues: %d, Pull Requests: %d, Commits: %d",
                len(md.issues.items()),
                len(md.pull_requests.items()),
                len(md.commits.items()),
            )
        else:
            md.issues = deepcopy(data.issues)
            md.pull_requests = deepcopy(data.pull_requests)
            md.commits = deepcopy(data.commits)

        return md

    def _filter_issues(self, data: MinedData) -> dict[Issue, Repository]:
        """
        Filter issues based on the selected filtering type - default or hierarchy.

        Parameters:
            data (MinedData): The mined data to filter.

        Returns:
            dict[Issue, Repository]: The filtered issues.
        """
        if ActionInputs.get_hierarchy():
            logger.debug("Used hierarchy issue filtering logic.")
            return self._filter_issues_issue_hierarchy(data)

        logger.debug("Used default issue filtering logic.")
        return self._filter_issues_default(data)

    @staticmethod
    def _filter_issues_default(data: MinedData) -> dict[Issue, Repository]:
        """
        Default filtering for issues: filter out closed issues before the release date.

        Parameters:
            data (MinedData): The mined data containing issues and release information.

        Returns:
            dict[Issue, Repository]: The filtered issues.
        """
        return {issue: repo for issue, repo in data.issues.items() if (issue.closed_at is None) or (issue.closed_at >= data.since)}

    @staticmethod
    def _filter_issues_issue_hierarchy(data: MinedData) -> dict[Issue, Repository]:
        """
        Hierarchy filtering for issues: include issues closed since the release date
        or still open at generation time.

        Parameters:
            data (MinedData): The mined data containing issues and release information.

        Returns:
            dict[Issue, Repository]: The filtered issues.
        """
        return {
            issue: repo
            for issue, repo in data.issues.items()
            if (
                (issue.closed_at is not None and issue.closed_at >= data.since)
                or (issue.state == "open")
            )
        }
