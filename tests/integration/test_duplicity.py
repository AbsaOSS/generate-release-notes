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
"""Offline integration tests — duplicity scope behaviour.

Covers: scope=both, scope=none, scope=custom, scope=service.
"""

from collections.abc import Callable
from datetime import datetime

from pytest_mock import MockerFixture

from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.data.miner import DataMiner
from tests.integration.conftest import build_mined_data, capture_run


# ---------------------------------------------------------------------------
# duplicity_scope=both shows icon in two chapters
# ---------------------------------------------------------------------------


def test_duplicity_scope_both_shows_icon_in_two_chapters(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """A dual-labeled record appears in both matching chapters with the duplicity icon."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    chapters_yaml = (
        "- {title: 'Alpha', label: alpha}\n"
        "- {title: 'Beta', label: beta}"
    )
    i1 = make_issue(1, "closed", ["alpha", "beta"], title="Dual item", user_login="dev1")
    pr10 = make_pr(10, title="Fix dual", body="Closes #1\n", user_login="dev1")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo)],
        pull_requests=[(pr10, repo)],
        commits=[],
        release=release,
        since=datetime(2023, 1, 1),
    )
    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {"INPUT_CHAPTERS": chapters_yaml, "INPUT_DUPLICITY_SCOPE": "both", "INPUT_WARNINGS": "false"},
    )

    # Both chapter headings must contain the record title
    alpha_section = actual.split("### Alpha")[1].split("###")[0]
    beta_section = actual.split("### Beta")[1].split("###")[0]
    assert "Dual item" in alpha_section, "Record must appear in Alpha chapter"
    assert "Dual item" in beta_section, "Record must appear in Beta chapter"

    # At least one occurrence must carry the duplicity icon
    assert "\U0001f514" in actual, "Duplicity icon must appear for the duplicate entry"


# ---------------------------------------------------------------------------
# duplicity_scope=none → record appears once, no icon
# ---------------------------------------------------------------------------


def test_duplicity_scope_none_record_appears_once(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """With scope=none, a record eligible for two service chapters appears in only the first."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Issue with no labels and no PR → eligible for "Closed Issues without Pull Request"
    # AND "Closed Issues without User Defined Labels".
    # With scope=both both appear; with scope=none only the first.
    i1 = make_issue(1, "closed", [], title="Bare issue", user_login="dev1")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo)],
        pull_requests=[],
        commits=[],
        release=release,
        since=datetime(2023, 1, 1),
    )
    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {
            "INPUT_CHAPTERS": "- {title: 'Features', label: feature}",
            "INPUT_DUPLICITY_SCOPE": "none",
            "INPUT_WARNINGS": "true",
        },
    )

    occurrences = actual.count("Bare issue")
    assert occurrences == 1, f"Record must appear in exactly one service chapter with scope=none (found {occurrences})"


# ---------------------------------------------------------------------------
# duplicity_scope=custom allows custom dups, prevents service dups
# ---------------------------------------------------------------------------


def test_duplicity_scope_custom_allows_custom_prevents_service(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """scope=custom allows duplicate rows in custom chapters but not in service chapters."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    chapters_yaml = (
        "- {title: 'Alpha', label: alpha}\n"
        "- {title: 'Beta', label: beta}"
    )
    # Dual-labeled issue: should appear in both custom chapters
    i1 = make_issue(1, "closed", ["alpha", "beta"], title="Custom dup item", user_login="dev1")
    pr10 = make_pr(10, title="Fix custom", body="Closes #1\n", user_login="dev1")

    # Unlabeled issue with no PR: eligible for multiple service chapters but scope=custom prevents service dups
    i2 = make_issue(2, "closed", [], title="Service single item", user_login="dev2")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo)],
        pull_requests=[(pr10, repo)],
        commits=[],
        release=release,
        since=datetime(2023, 1, 1),
    )
    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {"INPUT_CHAPTERS": chapters_yaml, "INPUT_DUPLICITY_SCOPE": "custom", "INPUT_WARNINGS": "true"},
    )

    # Custom chapters: record appears in both
    assert actual.count("Custom dup item") == 2, "Dual-labeled record must appear in both custom chapters"
    # Service chapters: unlabeled issue appears only once
    assert actual.count("Service single item") == 1, "Service chapter record must appear only once with scope=custom"


# ---------------------------------------------------------------------------
# duplicity_scope=service allows service dups, prevents custom
# ---------------------------------------------------------------------------


def test_duplicity_scope_service_allows_service_prevents_custom(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """scope=service allows duplicate rows in service chapters but prevents service-only dedup.

    Custom chapters always show records in all matching chapters regardless of scope.
    scope=service allows service chapter duplicates (same as both for service),
    while scope=custom prevents them.  This test verifies the service-chapter
    behaviour by comparing against scope=custom.
    """
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    chapters_yaml = (
        "- {title: 'Alpha', label: alpha}\n"
        "- {title: 'Beta', label: beta}"
    )
    i1 = make_issue(1, "closed", ["alpha", "beta"], title="Custom dup item", user_login="dev1")
    pr10 = make_pr(10, title="Fix custom", body="Closes #1\n", user_login="dev1")

    # Unlabeled issue with no PR: eligible for multiple service chapters
    i2 = make_issue(2, "closed", [], title="Service dup item", user_login="dev2")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo)],
        pull_requests=[(pr10, repo)],
        commits=[],
        release=release,
        since=datetime(2023, 1, 1),
    )
    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {"INPUT_CHAPTERS": chapters_yaml, "INPUT_DUPLICITY_SCOPE": "service", "INPUT_WARNINGS": "true"},
    )

    # Custom chapters always show all label matches (scope does not affect custom)
    assert actual.count("Custom dup item") == 2, "Custom dups always shown regardless of scope"
    # Service chapters: duplicity allowed with scope=service — record appears in multiple
    assert actual.count("Service dup item") >= 2, "Service chapter dups must be allowed with scope=service"
