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
from collections.abc import Callable

import pytest
from pytest_mock import MockerFixture

from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.pull_request_record import PullRequestRecord


@pytest.fixture
def make_pr(mocker: MockerFixture) -> Callable[..., PullRequestRecord]:
    """Factory fixture for lightweight PullRequestRecord mocks."""

    def _factory(*, author=None, skip=False, labels=None) -> PullRequestRecord:
        pull = mocker.Mock(spec=PullRequest)
        if author:
            user = mocker.Mock()
            user.login = author
            pull.user = user
        else:
            pull.user = None
        pull.assignees = []
        repo = mocker.Mock(spec=Repository)
        return PullRequestRecord(pull=pull, repo=repo, labels=labels if labels is not None else [], skip=skip)

    return _factory


@pytest.fixture
def make_issue(mocker: MockerFixture) -> Callable[..., IssueRecord]:
    """Factory fixture for lightweight IssueRecord mocks."""

    def _factory(*, author=None, assignees=None, skip=False, labels=None) -> IssueRecord:
        issue = mocker.Mock(spec=Issue)
        if author:
            user = mocker.Mock()
            user.login = author
            issue.user = user
        else:
            issue.user = None
        issue.assignees = [mocker.Mock(login=login) for login in (assignees or [])]
        return IssueRecord(issue=issue, issue_labels=labels if labels is not None else [], skip=skip)

    return _factory
