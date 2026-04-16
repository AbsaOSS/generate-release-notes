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
"""Offline integration tests for the full release notes pipeline.

Every test calls main.run() directly with INPUT_* env vars, a mock GitHub
instance, and a controlled MinedData returned by a patched DataMiner.  The
GitHub API network layer is never reached.

Snapshot fixture files live in tests/integration/fixtures/.
Set WRITE_SNAPSHOTS=1 to regenerate them from the current pipeline output.
"""

import os
import tempfile
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

import main
from release_notes_generator.data.miner import DataMiner
from tests.integration.conftest import build_mined_data

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capture_run(patch_env: Callable, overrides: dict | None = None) -> str:
    """Apply env overrides, run main.run() and return the captured release notes string."""
    patch_env(overrides)
    with tempfile.NamedTemporaryFile(mode="r", suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        os.environ["GITHUB_OUTPUT"] = tmp_path
        main.run()
        with open(tmp_path, encoding="utf-8") as f:
            raw = f.read()
    finally:
        os.environ.pop("GITHUB_OUTPUT", None)
        Path(tmp_path).unlink(missing_ok=True)

    # Parse the GitHub Actions output format: "name<<EOF\nvalue\nEOF\n"
    lines = raw.splitlines()
    notes_lines: list[str] = []
    inside = False
    for line in lines:
        if line == "release-notes<<EOF":
            inside = True
            continue
        if line == "EOF" and inside:
            break
        if inside:
            notes_lines.append(line)
    return "\n".join(notes_lines)


def _snapshot_path(name: str) -> Path:
    return FIXTURES_DIR / f"{name}.md"


def _assert_snapshot(actual: str, snapshot_name: str) -> None:
    """Compare actual to stored snapshot, or write snapshot if WRITE_SNAPSHOTS=1."""
    FIXTURES_DIR.mkdir(exist_ok=True)
    path = _snapshot_path(snapshot_name)
    if os.getenv("WRITE_SNAPSHOTS") == "1" or not path.exists():
        path.write_text(actual, encoding="utf-8")
        pytest.skip(f"Snapshot written to {path}. Re-run without WRITE_SNAPSHOTS=1 to compare.")
    expected = path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Snapshot mismatch for '{snapshot_name}'.\n"
        f"Run with WRITE_SNAPSHOTS=1 to update the fixture.\n"
        f"--- expected ---\n{expected}\n--- actual ---\n{actual}"
    )


# ---------------------------------------------------------------------------
# T-INT-01 — Maximal integration snapshot
#
# Exercises in a single run:
#   - Custom chapters (Bugfixes, Features, Enhancements)
#   - Duplicity scope=both with icon 🔔 (issue with two labels appears in two chapters)
#   - Release notes extraction from issue body and from PR body
#   - Skip labels (record absent from all chapters)
#   - Issues with no PR (land in service chapters only)
#   - Unlinked merged PR (lands in service chapter)
#   - Direct commit (lands in service chapter)
#   - print_empty_chapters=true (empty service chapters show placeholder)
#   - Full Changelog footer with compare URL
# ---------------------------------------------------------------------------


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
    """T-INT-01: Full pipeline from main.run() produces a 1:1 snapshot of the release notes."""
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

    actual = _capture_run(patch_env)
    _assert_snapshot(actual, "test_full_pipeline_snapshot")


# ---------------------------------------------------------------------------
# T-INT-02 — warnings=False suppresses entire service chapter block
# ---------------------------------------------------------------------------


def test_warnings_false_suppresses_service_chapters(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
    make_commit: Callable[..., Commit],
) -> None:
    """T-INT-02: With warnings=false no service chapter heading appears in the output."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    i1 = make_issue(1, "closed", ["bug"], title="Normal issue", user_login="dev1")
    pr10 = make_pr(10, title="Fix it", body="Closes #1\n", user_login="dev1")
    # unlinked PR that would normally hit a service chapter
    pr99 = make_pr(99, title="Orphan PR", body="", user_login="dev9")
    # direct commit that would hit service chapter
    c1 = make_commit("abc1234abcd", "Stray commit")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo)],
        pull_requests=[(pr10, repo), (pr99, repo)],
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

    actual = _capture_run(patch_env, {"INPUT_WARNINGS": "false"})

    assert "⚠️" not in actual, "Service chapter emoji must not appear when warnings=false"
    assert "#### Full Changelog" in actual, "Changelog footer must still be present"


# ---------------------------------------------------------------------------
# T-INT-03 — print_empty_chapters=False suppresses empty custom chapter headings
# ---------------------------------------------------------------------------


def test_print_empty_chapters_false_hides_empty_headings(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """T-INT-03: An unmatched chapter heading is absent when print_empty_chapters=false."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Only a bug issue → Bugfixes chapter populated; Features and Enhancements empty
    i1 = make_issue(1, "closed", ["bug"], title="A bug fix", user_login="dev1")
    pr10 = make_pr(10, title="Fix bug", body="Closes #1\n", user_login="dev1")

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

    actual = _capture_run(patch_env, {"INPUT_PRINT_EMPTY_CHAPTERS": "false", "INPUT_WARNINGS": "false"})

    assert "Bugfixes" in actual
    assert "Features" not in actual
    assert "Enhancements" not in actual


# ---------------------------------------------------------------------------
# T-INT-04 — skip labels exclude record from all chapters
# ---------------------------------------------------------------------------


def test_skip_labels_exclude_record_from_all_chapters(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """T-INT-04: Records with skip labels are absent from both custom and service chapters."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    i_normal = make_issue(1, "closed", ["bug"], title="Normal", user_login="dev1")
    i_skip = make_issue(2, "closed", ["skip-release-notes"], title="Skipped", user_login="dev2")
    i_both = make_issue(3, "closed", ["bug", "skip-release-notes"], title="Dual skip", user_login="dev3")

    pr10 = make_pr(10, title="Fix normal", body="Closes #1\n", user_login="dev1")
    pr20 = make_pr(20, title="Fix skipped", body="Closes #2\n", user_login="dev2")
    pr30 = make_pr(30, title="Fix dual", body="Closes #3\n", user_login="dev3")

    data = build_mined_data(
        repo=repo,
        issues=[(i_normal, repo), (i_skip, repo), (i_both, repo)],
        pull_requests=[(pr10, repo), (pr20, repo), (pr30, repo)],
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

    actual = _capture_run(patch_env)

    assert "Normal" in actual
    assert "Skipped" not in actual
    assert "Dual skip" not in actual


# ---------------------------------------------------------------------------
# T-INT-05 — chapter order field governs output sequence
# ---------------------------------------------------------------------------


def test_chapter_order_field_governs_output_sequence(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """T-INT-05: Chapters with explicit order render in ascending order regardless of declaration order."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Declare C (order 30), B (order 20), A (order 10) — expected output A, B, C
    chapters_yaml = (
        "- {title: 'C chapter', label: clabel, order: 30}\n"
        "- {title: 'B chapter', label: blabel, order: 20}\n"
        "- {title: 'A chapter', label: alabel, order: 10}"
    )
    i_a = make_issue(1, "closed", ["alabel"], title="A item", user_login="dev1")
    i_b = make_issue(2, "closed", ["blabel"], title="B item", user_login="dev2")
    i_c = make_issue(3, "closed", ["clabel"], title="C item", user_login="dev3")
    pr_a = make_pr(10, title="A PR", body="Closes #1\n", user_login="dev1")
    pr_b = make_pr(20, title="B PR", body="Closes #2\n", user_login="dev2")
    pr_c = make_pr(30, title="C PR", body="Closes #3\n", user_login="dev3")

    data = build_mined_data(
        repo=repo,
        issues=[(i_a, repo), (i_b, repo), (i_c, repo)],
        pull_requests=[(pr_a, repo), (pr_b, repo), (pr_c, repo)],
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

    actual = _capture_run(patch_env, {"INPUT_CHAPTERS": chapters_yaml, "INPUT_WARNINGS": "false"})

    pos_a = actual.index("A chapter")
    pos_b = actual.index("B chapter")
    pos_c = actual.index("C chapter")
    assert pos_a < pos_b < pos_c, "Chapters must appear in ascending order-field sequence"
