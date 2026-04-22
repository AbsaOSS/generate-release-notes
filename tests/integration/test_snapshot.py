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
"""Offline integration test — full pipeline golden snapshot (test_full_pipeline_snapshot)."""

import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.data.miner import DataMiner
from tests.integration.conftest import build_mined_data, capture_run

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _snapshot_path(name: str) -> Path:
    return FIXTURES_DIR / f"{name}.md"


def _assert_snapshot(actual: str, snapshot_name: str) -> None:
    """Compare actual to stored snapshot, or write snapshot if WRITE_SNAPSHOTS=1.

    Fails explicitly when the snapshot file is missing in normal runs so that
    accidental deletions are caught rather than silently re-created.
    """
    FIXTURES_DIR.mkdir(exist_ok=True)
    path = _snapshot_path(snapshot_name)
    if os.getenv("WRITE_SNAPSHOTS") == "1":
        path.write_text(actual, encoding="utf-8")
        pytest.skip(f"Snapshot written to {path}. Re-run without WRITE_SNAPSHOTS=1 to compare.")
    if not path.exists():
        pytest.fail(
            f"Snapshot file '{path}' does not exist. "
            "Run with WRITE_SNAPSHOTS=1 to create it."
        )
    expected = path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Snapshot mismatch for '{snapshot_name}'.\n"
        f"Run with WRITE_SNAPSHOTS=1 to update the fixture.\n"
        f"--- expected ---\n{expected}\n--- actual ---\n{actual}"
    )


def test_full_pipeline_snapshot(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_commit: Callable[..., Commit],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Full pipeline from main.run() produces a 1:1 snapshot of the release notes.

    Exercises in a single run:
      - Custom chapters (Bugfixes, Features, Enhancements)
      - Duplicity scope=both with icon 🔔 (issue with two labels appears in two chapters)
      - Release notes extraction from issue body and from PR body
      - Skip labels (record absent from all chapters)
      - Issues with no PR (land in service chapters only)
      - Unlinked merged PR (lands in service chapter)
      - Direct commit (lands in service chapter)
      - print_empty_chapters=true (empty service chapters show placeholder)
      - Full Changelog footer with compare URL
    """
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # --- issues ---
    i1 = make_issue(1, "closed", ["bug"], title="Fix login crash", user_login="dev1")
    i2 = make_issue(2, "closed", ["feature"], title="Add dashboard", body="Release Notes:\n- New dashboard added\n", user_login="dev2")
    i3 = make_issue(3, "closed", ["bug", "enhancement"], title="Dual label item", user_login="dev3")
    i4 = make_issue(4, "closed", ["skip-release-notes"], title="Skip this", user_login="skip_user")
    i5 = make_issue(5, "closed", [], title="Unlabeled no PR", user_login="dev5")
    i6 = make_issue(6, "closed", ["bug"], title="Bug with no PR", user_login="dev6")

    # --- pull requests ---
    pr10 = make_pr(10, title="Fix login", body="Closes #1\n\nRelease Notes:\n- Login crash fixed\n", user_login="dev1")
    pr20 = make_pr(20, title="Add dashboard", body="Closes #2\n", user_login="dev2")
    pr30 = make_pr(30, title="Dual fix", body="Closes #3\n", user_login="dev3")
    pr40 = make_pr(40, title="Unlinked PR", body="", user_login="dev4")

    # --- direct commit (sha not matching any PR merge_commit_sha) ---
    c1 = make_commit("deadbee1234", "Direct commit message")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo), (i3, repo), (i4, repo), (i5, repo), (i6, repo)],
        pull_requests=[(pr10, repo), (pr20, repo), (pr30, repo), (pr40, repo)],
        commits=[(c1, repo)],
        release=release,
        since=datetime(2023, 1, 1),
    )

    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = capture_run(patch_env)
    _assert_snapshot(actual, "test_full_pipeline_snapshot")
