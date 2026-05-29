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
"""Offline integration tests — compare mode (graph-based commit selection).

Covers the end-to-end behaviour difference between timestamp mode and compare mode
through the full pipeline (main.run → mine_data → filter → build → output).

The key observable difference:
  - Timestamp mode: PRs/commits whose merged_at/author.date pre-dates data.since are
    silently dropped by FilterByRelease.
  - Compare mode: PRs/commits in data.pull_requests/data.commits pass through
    unchanged — FilterByRelease treats the set as already exact.

In a real branching history this means maintenance-branch cherry-picks (whose
merge date may pre-date the previous tag on the develop branch) are always
included in the compare-mode output.
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from pytest_mock import MockerFixture

from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.data.miner import DataMiner
from tests.integration.helpers import build_mined_data, capture_run


# ---------------------------------------------------------------------------
# Compare mode: PRs dated before data.since still appear in the output
# ---------------------------------------------------------------------------


def test_compare_mode_includes_pr_dated_before_since(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """In compare mode a PR merged before data.since is retained in the output.

    Simulates a cherry-pick commit on a maintenance branch: the PR was merged
    before the previous-tag timestamp but belongs in the release because the
    compare API returned its commit.
    """
    repo = make_repo("org/repo")
    release = make_release("v2.6.3")

    since = datetime(2026, 5, 7)
    # PR merged 30 days before since — timestamp mode would drop it
    pr_cherry_pick = make_pr(
        1363,
        title="Fix new service access role",
        body="",
        user_login="dev1",
        merged=True,
    )
    pr_cherry_pick.merged_at = since - timedelta(days=30)
    pr_cherry_pick.closed_at = pr_cherry_pick.merged_at
    pr_cherry_pick.merge_commit_sha = "abc1363"

    data = build_mined_data(
        repo=repo,
        issues=[],
        pull_requests=[(pr_cherry_pick, repo)],
        commits=[],
        release=release,
        since=since,
    )
    # compare mode sentinel
    data.compare_commit_shas = {"abc1363"}

    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {
            "INPUT_TAG_NAME": "v2.6.4",
            "INPUT_FROM_TAG_NAME": "v2.6.3",
        },
    )

    assert "Fix new service access role" in actual, (
        "Compare-mode PR dated before data.since must appear in the release notes"
    )


# ---------------------------------------------------------------------------
# Timestamp mode: same PR is excluded when merged before data.since
# ---------------------------------------------------------------------------


def test_timestamp_mode_excludes_pr_dated_before_since(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """In timestamp mode a PR merged before data.since is excluded.

    This is the control case: identical setup to the compare-mode test but
    without compare_commit_shas populated, so FilterByRelease applies
    timestamp filtering and drops the old PR.
    """
    repo = make_repo("org/repo")
    release = make_release("v2.6.3")

    since = datetime(2026, 5, 7)
    pr_old = make_pr(
        1363,
        title="Fix new service access role",
        body="",
        user_login="dev1",
        merged=True,
    )
    pr_old.merged_at = since - timedelta(days=30)
    pr_old.closed_at = pr_old.merged_at

    data = build_mined_data(
        repo=repo,
        issues=[],
        pull_requests=[(pr_old, repo)],
        commits=[],
        release=release,
        since=since,
    )
    # compare_commit_shas is empty → timestamp mode (default from build_mined_data)

    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {
            "INPUT_TAG_NAME": "v2.6.4",
            "INPUT_FROM_TAG_NAME": "",
        },
    )

    assert "Fix new service access role" not in actual, (
        "Timestamp-mode PR dated before data.since must be absent from the release notes"
    )


# ---------------------------------------------------------------------------
# Compare mode: multiple PRs all retained, none filtered by timestamp
# ---------------------------------------------------------------------------


def test_compare_mode_retains_all_prs_regardless_of_date(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """All compare-mode PRs appear even when all predate data.since.

    Represents the v2.6.5 scenario: the backport PR and any other PRs
    unique to the maintenance branch all belong in the release notes.
    """
    repo = make_repo("org/repo")
    release = make_release("v2.6.4")

    since = datetime(2026, 5, 14)
    old_date = since - timedelta(days=60)

    pr_a = make_pr(1402, title="Backport: handle empty schema in Hive", body="", user_login="dev1", merged=True)
    pr_a.merged_at = old_date
    pr_a.closed_at = old_date
    pr_a.merge_commit_sha = "sha1402"

    pr_b = make_pr(1350, title="Backport: fix config loader", body="", user_login="dev2", merged=True)
    pr_b.merged_at = old_date
    pr_b.closed_at = old_date
    pr_b.merge_commit_sha = "sha1350"

    data = build_mined_data(
        repo=repo,
        issues=[],
        pull_requests=[(pr_a, repo), (pr_b, repo)],
        commits=[],
        release=release,
        since=since,
    )
    data.compare_commit_shas = {"sha1402", "sha1350"}

    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {
            "INPUT_TAG_NAME": "v2.6.5",
            "INPUT_FROM_TAG_NAME": "v2.6.4",
        },
    )

    assert "Backport: handle empty schema in Hive" in actual
    assert "Backport: fix config loader" in actual


# ---------------------------------------------------------------------------
# Compare mode: commits dated before data.since are included in service chapters
# ---------------------------------------------------------------------------


def test_compare_mode_includes_commit_dated_before_since(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_commit: Callable[..., Commit],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """A direct commit pre-dating data.since appears in the service chapter in compare mode."""
    repo = make_repo("org/repo")
    release = make_release("v2.6.3")

    since = datetime(2026, 5, 7)

    commit = make_commit("bumpsha1234", "Bump version to 2.6.4")
    commit.commit.author.date = since - timedelta(days=10)

    data = build_mined_data(
        repo=repo,
        issues=[],
        pull_requests=[],
        commits=[(commit, repo)],
        release=release,
        since=since,
    )
    data.compare_commit_shas = {"bumpsha1234"}

    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(
        patch_env,
        {
            "INPUT_TAG_NAME": "v2.6.4",
            "INPUT_FROM_TAG_NAME": "v2.6.3",
            "INPUT_WARNINGS": "true",
        },
    )

    assert "Bump version to 2.6.4" in actual, (
        "Compare-mode commit pre-dating data.since must appear in service chapter"
    )
