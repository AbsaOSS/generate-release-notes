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
    """Class for keeping track of an item in inventory."""

    repository: Repository
    release: GitRelease
    issues: list[Issue]
    pull_requests: list[PullRequest]
    commits: list[Commit]
    since: datetime

    def __init__(self):
        self.repository: Optional[Repository] = None
        self.release: Optional[GitRelease] = None
        self.issues: list[Issue] = []
        self.pull_requests: list[PullRequest] = []
        self.commits: list[Commit] = []
        self.since = datetime(1970, 1, 1)  # Default to epoch start

    def is_empty(self):
        if self.repository is None:
            return True
        return False

    def mock(self, mocker, rls_mock: Optional[GitRelease], mock_repo: Repository) -> "MinedData":
        """Mock method to create a MinedData instance with dummy data."""
        self.repository = mock_repo
        self.release = rls_mock if rls_mock != None else mocker.Mock(spec=GitRelease)
        self.issues = [
            mocker.Mock(spec=Issue, title="Mock Issue 1", number=1),
            mocker.Mock(spec=Issue, title="Mock Issue 2", number=2),
        ]
        self.pull_requests = [
            mocker.Mock(spec=PullRequest, title="Mock PR 1", number=1),
            mocker.Mock(spec=PullRequest, title="Mock PR 2", number=2),
        ]
        self.commits = [
            mocker.Mock(spec=Commit, sha="abc123", commit={"message": "Mock Commit 1"}),
            mocker.Mock(spec=Commit, sha="def456", commit={"message": "Mock Commit 2"}),
        ]
        self.since = datetime.now()
        return self
