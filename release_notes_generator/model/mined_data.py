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
This module contains data class MinedData, which is used to store the mined data from GitHub.
"""

import logging

from dataclasses import dataclass
from datetime import datetime

from typing import Optional

from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Commit import Commit
from github.Repository import Repository

logger = logging.getLogger(__name__)


@dataclass
class MinedData:
    """Class for keeping track of mined GitHub data."""

    def __init__(self, repository: Repository):
        self._home_repository_full_name: str = repository.full_name
        self._repositories: dict[str, Repository] = {repository.full_name: repository}
        self.release: Optional[GitRelease] = None
        self.issues: dict[Issue, Repository] = {}
        self.pull_requests: dict[PullRequest, Repository] = {}
        self.commits: dict[Commit, Repository] = {}
        self.since = datetime(1970, 1, 1)  # Default to epoch start

        self.parents_sub_issues: dict[str, list[str]] = {}  # parent issue id -> list of its sub-issues ids

    @property
    def home_repository(self) -> Repository:
        """Get the home repository."""
        return self._repositories[self._home_repository_full_name]

    def add_repository(self, repository: Repository) -> None:
        """Add a repository to the mined data if not already present."""
        if repository.full_name not in self._repositories:
            self._repositories[repository.full_name] = repository
            logger.debug(f"Added repository {repository.full_name} to mined data.")

    def get_repository(self, full_name: str) -> Optional[Repository]:
        if full_name not in self._repositories:
            return None

        return self._repositories[full_name]

    def is_empty(self):
        """
        Check if the mined data is empty (no issues, pull requests, or commits).

        Returns:
            bool: True if empty, False otherwise.
        """
        return not (self.issues or self.pull_requests or self.commits)
