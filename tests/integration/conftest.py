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
"""Shared fixtures for offline integration tests."""

import os
import time
from collections.abc import Callable
from datetime import datetime

import pytest
from pytest_mock import MockerFixture

from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs


# ---------------------------------------------------------------------------
# ActionInputs class-level cache reset (autouse so every test gets a clean slate)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_action_inputs_cache() -> None:
    """Reset class-level caches in ActionInputs so each test starts clean."""
    ActionInputs.reset_caches_for_testing()


# ---------------------------------------------------------------------------
# Environment / input helpers
# ---------------------------------------------------------------------------

_BASE_ENV: dict[str, str] = {
    "INPUT_GITHUB_REPOSITORY": "org/repo",
    "INPUT_GITHUB_TOKEN": "fake-token",
    "INPUT_TAG_NAME": "v1.0.0",
    "INPUT_FROM_TAG_NAME": "",
    "INPUT_CHAPTERS": (
        "- {title: 'Bugfixes \U0001f6e0', label: bug}\n"
        "- {title: 'Features \U0001f389', label: feature}\n"
        "- {title: 'Enhancements \U0001f4a1', label: enhancement}"
    ),
    "INPUT_DUPLICITY_SCOPE": "both",
    "INPUT_DUPLICITY_ICON": "\U0001f514",
    "INPUT_WARNINGS": "true",
    "INPUT_PRINT_EMPTY_CHAPTERS": "true",
    "INPUT_SKIP_RELEASE_NOTES_LABELS": "skip-release-notes",
    "INPUT_HIERARCHY": "false",
    "INPUT_VERBOSE": "false",
    "INPUT_PUBLISHED_AT": "false",
    "INPUT_SERVICE_CHAPTER_EXCLUDE": "",
    "INPUT_HIDDEN_SERVICE_CHAPTERS": "",
    "INPUT_SERVICE_CHAPTER_ORDER": "",
    "INPUT_ROW_FORMAT_LINK_PR": "true",
    "INPUT_CODERABBIT_SUPPORT_ACTIVE": "false",
}


@pytest.fixture
def patch_env(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, str] | None], None]:
    """Return a callable that sets INPUT_* env vars, merging with base defaults."""

    def _apply(overrides: dict[str, str] | None = None) -> None:
        for key in list(os.environ):
            if key.startswith("INPUT_"):
                monkeypatch.delenv(key, raising=False)
        env = {**_BASE_ENV, **(overrides or {})}
        for key, value in env.items():
            monkeypatch.setenv(key, value)

    return _apply


# ---------------------------------------------------------------------------
# Object factory helpers (model layer)
# ---------------------------------------------------------------------------


@pytest.fixture
def make_label(mocker: MockerFixture) -> Callable[[str], object]:
    def _factory(name: str) -> object:
        lbl = mocker.Mock()
        lbl.name = name
        return lbl

    return _factory


@pytest.fixture
def make_issue(mocker: MockerFixture, make_label: Callable[[str], object]) -> Callable[..., Issue]:
    """Factory: (number, state, labels, *, title, body, user_login, closed_at) -> Issue mock."""

    def _factory(
        number: int,
        state: str,
        labels: list[str],
        *,
        title: str = "",
        body: str = "",
        user_login: str = "testuser",
        closed_at: datetime | None = None,
    ) -> Issue:
        issue = mocker.Mock(spec=Issue)
        issue.number = number
        issue.state = state
        issue.title = title or f"Issue {number}"
        issue.body = body
        issue.type = None
        issue.assignees = []
        issue.closed_at = closed_at or (datetime(2024, 1, 1) if state == "closed" else None)
        user = mocker.Mock()
        user.login = user_login
        issue.user = user
        issue.get_labels = mocker.Mock(return_value=[make_label(lbl) for lbl in labels])
        return issue

    return _factory


@pytest.fixture
def make_pr(mocker: MockerFixture, make_label: Callable[[str], object]) -> Callable[..., PullRequest]:
    """Factory: (number, *, title, body, user_login, labels, merged, merge_commit_sha) -> PullRequest mock."""

    def _factory(
        number: int,
        *,
        title: str = "",
        body: str = "",
        user_login: str = "testuser",
        labels: list[str] | None = None,
        merged: bool = True,
        merge_commit_sha: str | None = None,
    ) -> PullRequest:
        pr = mocker.Mock(spec=PullRequest)
        pr.number = number
        pr.title = title or f"PR {number}"
        pr.body = body
        pr.state = "closed"
        pr.merged_at = datetime(2024, 1, 2) if merged else None
        pr.closed_at = datetime(2024, 1, 2)
        pr.merge_commit_sha = merge_commit_sha or f"sha{number:04d}"
        user = mocker.Mock()
        user.login = user_login
        pr.user = user
        pr.assignees = []
        pr.get_labels = mocker.Mock(return_value=[make_label(lbl) for lbl in (labels or [])])
        return pr

    return _factory


@pytest.fixture
def make_commit(mocker: MockerFixture) -> Callable[..., Commit]:
    """Factory: (sha, message, *, author_login) -> Commit mock."""

    def _factory(sha: str, message: str, *, author_login: str | None = None) -> Commit:
        commit = mocker.Mock(spec=Commit)
        commit.sha = sha
        commit.commit = mocker.Mock()
        commit.commit.message = message
        commit.commit.author = mocker.Mock()
        commit.commit.author.date = datetime(2024, 1, 3)
        if author_login:
            commit.author = mocker.Mock()
            commit.author.login = author_login
        else:
            commit.author = None
        return commit

    return _factory


@pytest.fixture
def make_repo(mocker: MockerFixture) -> Callable[[str], Repository]:
    """Factory: (full_name,) -> Repository mock."""

    def _factory(full_name: str = "org/repo") -> Repository:
        repo = mocker.Mock(spec=Repository)
        repo.full_name = full_name
        repo.default_branch = "main"
        repo.html_url = f"https://github.com/{full_name}"
        return repo

    return _factory


@pytest.fixture
def make_release(mocker: MockerFixture) -> Callable[[str], GitRelease]:
    """Factory: (tag_name,) -> GitRelease mock with created_at = 2023-01-01."""

    def _factory(tag_name: str) -> GitRelease:
        release = mocker.Mock(spec=GitRelease)
        release.tag_name = tag_name
        release.created_at = datetime(2023, 1, 1)
        release.published_at = datetime(2023, 1, 1)
        return release

    return _factory


# ---------------------------------------------------------------------------
# Mock GitHub instance (configured to not block on rate-limit check)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_github(mocker: MockerFixture) -> object:
    """Patch main.Github and return a pre-configured mock instance.

    Rate-limit state is set so that GithubRateLimiter never sleeps.
    """
    patched_class = mocker.patch("main.Github")
    gh = patched_class.return_value

    rate_mock = mocker.Mock()
    rate_mock.remaining = 1000
    rate_mock.reset = mocker.Mock()
    rate_mock.reset.timestamp.return_value = time.time() + 3600
    rate_limit_overview = mocker.Mock()
    rate_limit_overview.rate = rate_mock
    gh.get_rate_limit.return_value = rate_limit_overview
    gh.requester = mocker.Mock()
    return gh



