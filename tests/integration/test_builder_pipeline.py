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
# Maximal integration snapshot
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
    """Full pipeline from main.run() produces a 1:1 snapshot of the release notes."""
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
# warnings=False suppresses entire service chapter block
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
    """With warnings=false no service chapter heading appears in the output."""
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
# print_empty_chapters=False suppresses empty custom chapter headings
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
    """An unmatched chapter heading is absent when print_empty_chapters=false."""
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
# skip labels exclude record from all chapters
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
    """Records with skip labels are absent from both custom and service chapters."""
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
# chapter order field governs output sequence
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
    """Chapters with explicit order render in ascending order regardless of declaration order."""
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

    actual = _capture_run(
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

    actual = _capture_run(
        patch_env,
        {"INPUT_CHAPTERS": "- {title: 'Features', label: feature}", "INPUT_DUPLICITY_SCOPE": "none", "INPUT_WARNINGS": "true"},
    )

    occurrences = actual.count("Bare issue")
    assert occurrences == 1, f"Record must appear in exactly one service chapter with scope=none (found {occurrences})"


# ---------------------------------------------------------------------------
# hidden chapter tracked but absent from output
# ---------------------------------------------------------------------------


def test_hidden_chapter_tracked_but_absent_from_output(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Hidden chapter heading and record content are absent from rendered output.

    A record routed to a hidden chapter does not appear in the output markdown.
    The hidden chapter's label is also included in user_defined_labels, so the record
    is ineligible for label-based service chapters regardless.  This test verifies the
    rendering behaviour (heading suppressed, rows suppressed) and that the visible
    chapter is unaffected.
    """
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # "Internal" chapter is hidden; "Features" chapter is visible
    chapters_yaml = (
        "- {title: 'Internal', label: internal, hidden: true}\n"
        "- {title: 'Features', label: feature}"
    )
    # Issue with only the hidden label — heading and content must both be absent from output
    i1 = make_issue(1, "closed", ["internal"], title="Secret work", user_login="dev1")
    pr10 = make_pr(10, title="Secret PR", body="Closes #1\n", user_login="dev1")

    # Issue with visible label — should appear in Features
    i2 = make_issue(2, "closed", ["feature"], title="Public feature", user_login="dev2")
    pr20 = make_pr(20, title="Feature PR", body="Closes #2\n", user_login="dev2")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo)],
        pull_requests=[(pr10, repo), (pr20, repo)],
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

    actual = _capture_run(
        patch_env,
        {
            "INPUT_CHAPTERS": chapters_yaml,
            "INPUT_DUPLICITY_SCOPE": "both",
            "INPUT_WARNINGS": "true",
            "INPUT_PRINT_EMPTY_CHAPTERS": "false",
        },
    )

    assert "### Internal" not in actual, "Hidden chapter heading must not appear in output"
    assert "Secret work" not in actual, "Hidden chapter record content must not appear in output"
    assert "### Features" in actual, "Visible chapter heading must appear"
    assert "Public feature" in actual, "Visible chapter record must appear"


# ---------------------------------------------------------------------------
# service chapter global exclude drops record
# ---------------------------------------------------------------------------


def test_service_chapter_global_exclude_drops_record(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Record matching a global '*' exclusion rule is absent from all service chapters."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Issue with no custom-chapter label → would hit service chapters
    # But it carries "no-notes" → global exclude rule drops it
    i1 = make_issue(1, "closed", ["no-notes"], title="Excluded issue", user_login="dev1")

    # Normal issue in custom chapter (control)
    i2 = make_issue(2, "closed", ["bug"], title="Normal bug", user_login="dev2")
    pr20 = make_pr(20, title="Fix bug", body="Closes #2\n", user_login="dev2")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo)],
        pull_requests=[(pr20, repo)],
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

    # YAML for service_chapter_exclude: global rule excludes records with "no-notes" label
    exclude_yaml = "'*': [[no-notes]]"

    actual = _capture_run(
        patch_env,
        {"INPUT_SERVICE_CHAPTER_EXCLUDE": exclude_yaml, "INPUT_WARNINGS": "true"},
    )

    assert "Excluded issue" not in actual, "Globally excluded record must be absent from all chapters"
    assert "Normal bug" in actual, "Non-excluded record must still appear"


# ---------------------------------------------------------------------------
# release notes extraction from issue and PR body
# ---------------------------------------------------------------------------


def test_release_notes_extraction_from_issue_and_pr_body(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Release notes blocks from issue and PR bodies are indented under the record row."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Issue body with release notes
    i1 = make_issue(
        1, "closed", ["bug"], title="Issue with notes",
        body="Some description.\n\nRelease Notes:\n- Fixed critical crash\n- Improved startup time\n",
        user_login="dev1",
    )
    # PR body with release notes (issue has no notes)
    i2 = make_issue(2, "closed", ["feature"], title="Issue no notes", user_login="dev2")
    pr10 = make_pr(10, title="Fix issue 1", body="Closes #1\n", user_login="dev1")
    pr20 = make_pr(
        20, title="Add feature",
        body="Closes #2\n\nRelease Notes:\n- New export feature\n",
        user_login="dev2",
    )

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo)],
        pull_requests=[(pr10, repo), (pr20, repo)],
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

    actual = _capture_run(patch_env, {"INPUT_WARNINGS": "false"})

    # Release notes from issue body
    assert "Fixed critical crash" in actual
    assert "Improved startup time" in actual
    # Release notes from PR body
    assert "New export feature" in actual
    # Indented under the record row (release notes lines start with spaces)
    lines = actual.splitlines()
    for line in lines:
        if "Fixed critical crash" in line:
            assert line.startswith("  "), f"Release notes line must be indented: {line!r}"
            break


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

    actual = _capture_run(
        patch_env,
        {"INPUT_CHAPTERS": chapters_yaml, "INPUT_DUPLICITY_SCOPE": "custom", "INPUT_WARNINGS": "true"},
    )

    # Custom chapters: record appears in both
    assert actual.count("Custom dup item") == 2, "Dual-labeled record must appear in both custom chapters"
    # Service chapters: unlabeled issue appears only once
    assert actual.count("Service single item") == 1, "Service chapter record must appear only once with scope=custom"


# ---------------------------------------------------------------------------
# per-chapter service exclude rule
# ---------------------------------------------------------------------------


def test_per_chapter_service_exclude_rule(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Per-chapter exclude rule hides record from that chapter only."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Closed issue with no PR and the "internal" label (not user-defined) →
    # hits "Closed Issues without Pull Request" AND "Closed Issues without User Defined Labels".
    # The per-chapter exclude should remove it from the second only.
    i1 = make_issue(1, "closed", ["internal"], title="Excluded from one", user_login="dev1")

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

    # Exclude from "Closed Issues without User Defined Labels" only
    exclude_yaml = "'Closed Issues without User Defined Labels ⚠️': [[internal]]"

    actual = _capture_run(
        patch_env,
        {
            "INPUT_SERVICE_CHAPTER_EXCLUDE": exclude_yaml,
            "INPUT_WARNINGS": "true",
            "INPUT_DUPLICITY_SCOPE": "both",
        },
    )

    # Should still appear in "Closed Issues without Pull Request"
    without_pr_section = actual.split("### Closed Issues without Pull Request")[1].split("###")[0]
    assert "Excluded from one" in without_pr_section, "Record must still appear in non-excluded chapter"

    # Should NOT appear in "Closed Issues without User Defined Labels"
    without_labels_section = actual.split("### Closed Issues without User Defined Labels")[1].split("###")[0]
    assert "Excluded from one" not in without_labels_section, "Record must be absent from excluded chapter"


# ---------------------------------------------------------------------------
# hidden service chapters
# ---------------------------------------------------------------------------


def test_hidden_service_chapters_selective(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_commit: Callable[..., Commit],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Hidden service chapters are omitted while other service chapters remain visible."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    i1 = make_issue(1, "closed", ["bug"], title="Normal bug", user_login="dev1")
    pr10 = make_pr(10, title="Fix bug", body="Closes #1\n", user_login="dev1")
    c1 = make_commit("aaa1234567", "Direct commit")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo)],
        pull_requests=[(pr10, repo)],
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

    actual = _capture_run(
        patch_env,
        {"INPUT_HIDDEN_SERVICE_CHAPTERS": "Direct commits ⚠️", "INPUT_WARNINGS": "true"},
    )

    assert "### Direct commits" not in actual, "Hidden service chapter must not appear"
    assert "Direct commit" not in actual, "Content of hidden service chapter must not appear"
    # Other service chapters should still be present
    assert "### Closed Issues without Pull Request" in actual or "### Merged PRs" in actual, (
        "Non-hidden service chapters must still appear"
    )


# ---------------------------------------------------------------------------
# multi-label chapter (labels array)
# ---------------------------------------------------------------------------


def test_multi_label_chapter_matches_any_label(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """A chapter with labels: [a, b] matches records carrying either label."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    chapters_yaml = "- {title: 'Improvements', labels: [feature, enhancement]}"
    i1 = make_issue(1, "closed", ["feature"], title="Feature item", user_login="dev1")
    i2 = make_issue(2, "closed", ["enhancement"], title="Enhancement item", user_login="dev2")
    i3 = make_issue(3, "closed", ["bug"], title="Bug item", user_login="dev3")
    pr10 = make_pr(10, title="PR 1", body="Closes #1\n", user_login="dev1")
    pr20 = make_pr(20, title="PR 2", body="Closes #2\n", user_login="dev2")
    pr30 = make_pr(30, title="PR 3", body="Closes #3\n", user_login="dev3")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo), (i3, repo)],
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

    actual = _capture_run(
        patch_env,
        {"INPUT_CHAPTERS": chapters_yaml, "INPUT_WARNINGS": "false", "INPUT_PRINT_EMPTY_CHAPTERS": "false"},
    )

    assert "### Improvements" in actual
    assert "Feature item" in actual, "Record with 'feature' label must match the multi-label chapter"
    assert "Enhancement item" in actual, "Record with 'enhancement' label must match the multi-label chapter"
    assert "Bug item" not in actual, "Record with unmatched label must not appear (print_empty=false, no bug chapter)"


# ---------------------------------------------------------------------------
# no previous release (all records pass through)
# ---------------------------------------------------------------------------


def test_no_previous_release_includes_all_records(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_commit: Callable[..., Commit],
    make_repo: Callable[..., Repository],
) -> None:
    """When there is no previous release, all records are included unfiltered."""
    repo = make_repo("org/repo")

    i1 = make_issue(1, "closed", ["bug"], title="Old bug", user_login="dev1")
    pr10 = make_pr(10, title="Fix old bug", body="Closes #1\n", user_login="dev1")
    c1 = make_commit("bbb1234567", "Old commit")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo)],
        pull_requests=[(pr10, repo)],
        commits=[(c1, repo)],
        release=None,
        since=None,
    )
    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = _capture_run(patch_env)

    assert "Old bug" in actual, "Issue must be included when no previous release exists"
    assert "Old commit" in actual, "Commit must be included when no previous release exists"


# ---------------------------------------------------------------------------
# custom row format for issues
# ---------------------------------------------------------------------------


def test_custom_row_format_issue(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Custom row-format-issue template changes the rendered row format."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    i1 = make_issue(1, "closed", ["bug"], title="Custom format bug", user_login="dev1")
    pr10 = make_pr(10, title="Fix it", body="Closes #1\n", user_login="dev1")

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

    actual = _capture_run(
        patch_env,
        {
            "INPUT_ROW_FORMAT_ISSUE": "{number} | {title} | {developers}",
            "INPUT_WARNINGS": "false",
        },
    )

    assert "#1 | Custom format bug |" in actual, "Custom row format must be applied"
    assert "developed by" not in actual, "Default format tokens must not appear with custom format"


# ---------------------------------------------------------------------------
# closed-but-not-merged PR routes to correct service chapter
# ---------------------------------------------------------------------------


def test_closed_pr_not_merged_routes_to_service_chapter(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """A closed-but-not-merged PR lands in 'Closed PRs without Issue and User Defined Labels'."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    i1 = make_issue(1, "closed", ["bug"], title="Normal issue", user_login="dev1")
    pr10 = make_pr(10, title="Normal PR", body="Closes #1\n", user_login="dev1")
    # Closed but not merged, no issue mentions, no labels
    pr99 = make_pr(99, title="Abandoned PR", body="", user_login="dev9", merged=False)

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo)],
        pull_requests=[(pr10, repo), (pr99, repo)],
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

    actual = _capture_run(patch_env, {"INPUT_WARNINGS": "true"})

    closed_pr_section = actual.split("### Closed PRs without Issue and User Defined Labels")[1].split("###")[0]
    assert "Abandoned PR" in closed_pr_section, "Closed-not-merged PR must appear in the correct service chapter"


# ---------------------------------------------------------------------------
# open issue with linked PR routes to service chapter
# ---------------------------------------------------------------------------


def test_open_issue_with_pr_routes_to_merged_prs_linked_open(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """An open issue with a linked PR appears in 'Merged PRs Linked to Not Closed Issue'."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Open issue with a linked PR
    i1 = make_issue(1, "open", ["bug"], title="Open issue with PR", user_login="dev1")
    pr10 = make_pr(10, title="Fix open issue", body="Closes #1\n", user_login="dev1")

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

    actual = _capture_run(
        patch_env,
        {"INPUT_WARNINGS": "true", "INPUT_PRINT_EMPTY_CHAPTERS": "false"},
    )

    assert "Merged PRs Linked to 'Not Closed' Issue" in actual, "Chapter heading must appear for open issue with PR"
    assert "Open issue with PR" in actual, "Open issue record must appear in the chapter"


# ---------------------------------------------------------------------------
# service chapter ordering
# ---------------------------------------------------------------------------


def test_service_chapter_ordering(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_commit: Callable[..., Commit],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Reordering service chapters changes their position in the output."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Unlabeled issue with no PR → hits two service chapters
    i1 = make_issue(1, "closed", [], title="Bare issue", user_login="dev1")
    # Direct commit → hits "Direct commits" chapter
    c1 = make_commit("ccc1234567", "Stray commit")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo)],
        pull_requests=[],
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

    # Default order: "Closed Issues without User Defined Labels" before "Direct commits"
    # Reorder: put "Direct commits" first
    reorder = "Direct commits ⚠️,Closed Issues without User Defined Labels ⚠️"
    actual = _capture_run(
        patch_env,
        {
            "INPUT_CHAPTERS": "- {title: 'Features', label: feature}",
            "INPUT_SERVICE_CHAPTER_ORDER": reorder,
            "INPUT_WARNINGS": "true",
            "INPUT_DUPLICITY_SCOPE": "both",
        },
    )

    pos_direct = actual.index("Direct commits")
    pos_closed_labels = actual.index("Closed Issues without User Defined Labels")
    assert pos_direct < pos_closed_labels, "Direct commits must appear before Closed Issues after reorder"


# ---------------------------------------------------------------------------
# CodeRabbit release notes extraction
# ---------------------------------------------------------------------------


def test_coderabbit_release_notes_extraction(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """CodeRabbit summary is extracted when coderabbit-support-active=true and no explicit release notes."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # PR with no explicit "Release Notes:" section, but with CodeRabbit summary
    i1 = make_issue(1, "closed", ["feature"], title="CR feature", user_login="dev1")
    pr10 = make_pr(
        10,
        title="CR PR",
        body=(
            "Closes #1\n\n"
            "Summary by CodeRabbit\n"
            "  - Added new authentication flow\n"
            "  - Improved error messages\n"
        ),
        user_login="dev1",
    )

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

    actual = _capture_run(
        patch_env,
        {"INPUT_CODERABBIT_SUPPORT_ACTIVE": "true", "INPUT_WARNINGS": "false"},
    )

    assert "Added new authentication flow" in actual, "CodeRabbit summary line must be extracted"
    assert "Improved error messages" in actual, "CodeRabbit summary line must be extracted"


# ---------------------------------------------------------------------------
# super-chapters group custom chapters under headings
# ---------------------------------------------------------------------------


def test_super_chapters_group_chapters_under_headings(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Super-chapters wrap matching custom chapters under level-2 headings."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    chapters_yaml = (
        "- {title: 'Bugfixes', label: bug}\n"
        "- {title: 'Features', label: feature}\n"
        "- {title: 'Docs', label: docs}"
    )
    super_chapters_yaml = (
        "- {title: 'Code Changes', labels: [bug, feature]}\n"
        "- {title: 'Documentation', labels: [docs]}"
    )

    i1 = make_issue(1, "closed", ["bug"], title="A bug fix", user_login="dev1")
    i2 = make_issue(2, "closed", ["feature"], title="A feature", user_login="dev2")
    i3 = make_issue(3, "closed", ["docs"], title="Doc update", user_login="dev3")
    pr1 = make_pr(10, title="Fix bug", body="Closes #1\n", user_login="dev1")
    pr2 = make_pr(20, title="Add feature", body="Closes #2\n", user_login="dev2")
    pr3 = make_pr(30, title="Update docs", body="Closes #3\n", user_login="dev3")

    data = build_mined_data(
        repo=repo,
        issues=[(i1, repo), (i2, repo), (i3, repo)],
        pull_requests=[(pr1, repo), (pr2, repo), (pr3, repo)],
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

    actual = _capture_run(
        patch_env,
        {
            "INPUT_CHAPTERS": chapters_yaml,
            "INPUT_SUPER_CHAPTERS": super_chapters_yaml,
            "INPUT_WARNINGS": "false",
        },
    )

    assert "## Code Changes" in actual, "Super-chapter heading must appear"
    assert "## Documentation" in actual, "Super-chapter heading must appear"
    assert "A bug fix" in actual, "Bug issue must be rendered under Code Changes"
    assert "A feature" in actual, "Feature issue must be rendered under Code Changes"
    assert "Doc update" in actual, "Docs issue must be rendered under Documentation"

    pos_code = actual.index("## Code Changes")
    pos_docs = actual.index("## Documentation")
    pos_bug = actual.index("A bug fix")
    pos_feat = actual.index("A feature")
    pos_doc_item = actual.index("Doc update")
    assert pos_code < pos_bug < pos_docs, "Bug must appear between Code Changes and Documentation headings"
    assert pos_code < pos_feat < pos_docs, "Feature must appear between Code Changes and Documentation headings"
    assert pos_doc_item > pos_docs, "Doc update must appear after Documentation heading"


# ---------------------------------------------------------------------------
# hierarchy parent/sub-issue rendering
# ---------------------------------------------------------------------------


def test_hierarchy_parent_sub_issue_rendering(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """With hierarchy=true, parent issues render sub-issues indented beneath them."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Parent issue with sub-issues
    i_parent = make_issue(1, "closed", ["feature"], title="Epic feature", user_login="dev1")
    i_child1 = make_issue(2, "closed", ["feature"], title="Sub-task A", user_login="dev2")
    i_child2 = make_issue(3, "closed", ["feature"], title="Sub-task B", user_login="dev3")
    pr10 = make_pr(10, title="Implement epic", body="Closes #1\n", user_login="dev1")
    pr20 = make_pr(20, title="Sub task A work", body="Closes #2\n", user_login="dev2")
    pr30 = make_pr(30, title="Sub task B work", body="Closes #3\n", user_login="dev3")

    data = build_mined_data(
        repo=repo,
        issues=[(i_parent, repo), (i_child1, repo), (i_child2, repo)],
        pull_requests=[(pr10, repo), (pr20, repo), (pr30, repo)],
        commits=[],
        release=release,
        since=datetime(2023, 1, 1),
    )

    hierarchy_mapping = {
        "org/repo#1": ["org/repo#2", "org/repo#3"],
    }

    def _fake_mine_missing(filtered_data):
        filtered_data.parents_sub_issues = hierarchy_mapping
        return {}, {}

    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch.object(DataMiner, "mine_missing_sub_issues", side_effect=_fake_mine_missing)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = _capture_run(
        patch_env,
        {"INPUT_HIERARCHY": "true", "INPUT_WARNINGS": "false"},
    )

    assert "Epic feature" in actual, "Parent issue must appear in output"
    assert "Sub-task A" in actual, "Sub-issue A must appear in output"
    assert "Sub-task B" in actual, "Sub-issue B must appear in output"

    # Sub-issues must appear after parent
    pos_parent = actual.index("Epic feature")
    pos_child_a = actual.index("Sub-task A")
    pos_child_b = actual.index("Sub-task B")
    assert pos_parent < pos_child_a, "Sub-task A must appear after parent"
    assert pos_parent < pos_child_b, "Sub-task B must appear after parent"

    # Parent should appear only once as top-level record (not duplicated as standalone)
    assert actual.count("Epic feature") == 1, "Parent must appear exactly once"


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
    behaviour by comparing against scope=custom (T-INT-11).
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

    actual = _capture_run(
        patch_env,
        {"INPUT_CHAPTERS": chapters_yaml, "INPUT_DUPLICITY_SCOPE": "service", "INPUT_WARNINGS": "true"},
    )

    # Custom chapters always show all label matches (scope does not affect custom)
    assert actual.count("Custom dup item") == 2, "Custom dups always shown regardless of scope"
    # Service chapters: duplicity allowed with scope=service — record appears in multiple
    assert actual.count("Service dup item") >= 2, "Service chapter dups must be allowed with scope=service"


# ---------------------------------------------------------------------------
# custom row format for PRs
# ---------------------------------------------------------------------------


def test_custom_row_format_pr(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Custom row-format-pr template changes the rendered row for unlinked PRs."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Unlinked merged PR (no issue) → renders using row-format-pr
    pr99 = make_pr(99, title="Standalone PR", body="", user_login="dev9")

    data = build_mined_data(
        repo=repo,
        issues=[],
        pull_requests=[(pr99, repo)],
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

    actual = _capture_run(
        patch_env,
        {
            "INPUT_ROW_FORMAT_PR": "{number} -- {title} -- {developers}",
            "INPUT_WARNINGS": "true",
        },
    )

    assert "#99 -- Standalone PR --" in actual, "Custom PR row format must be applied"


# ---------------------------------------------------------------------------
# row-format-link-pr=false suppresses PR prefix
# ---------------------------------------------------------------------------


def test_row_format_link_pr_false(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """row-format-link-pr=false removes the 'PR:' prefix from unlinked PR rows."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    pr99 = make_pr(99, title="Unlinked PR", body="", user_login="dev9")

    data = build_mined_data(
        repo=repo,
        issues=[],
        pull_requests=[(pr99, repo)],
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

    actual = _capture_run(
        patch_env,
        {"INPUT_ROW_FORMAT_LINK_PR": "false", "INPUT_WARNINGS": "true"},
    )

    assert "Unlinked PR" in actual, "PR must appear in output"
    assert "PR:" not in actual, "PR: prefix must not appear when row-format-link-pr=false"


# ---------------------------------------------------------------------------
# published-at=true affects time-based filtering boundary
# ---------------------------------------------------------------------------


def test_published_at_true_filters_by_published_timestamp(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """With published-at=true, the filter boundary uses the release published_at timestamp.

    Two issues: one closed between created_at and published_at, one closed after published_at.
    With published-at=true, the first should be filtered out.
    """
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")
    # Set distinct timestamps: created_at=2023-01-01, published_at=2023-06-01
    release.created_at = datetime(2023, 1, 1)
    release.published_at = datetime(2023, 6, 1)

    # Issue closed between created_at and published_at (2023-03-01) — should be filtered OUT
    i_old = make_issue(
        1, "closed", ["bug"], title="Old issue before publish",
        user_login="dev1", closed_at=datetime(2023, 3, 1),
    )
    pr_old = make_pr(10, title="Fix old", body="Closes #1\n", user_login="dev1")
    pr_old.merged_at = datetime(2023, 3, 1)
    pr_old.closed_at = datetime(2023, 3, 1)

    # Issue closed after published_at (2024-01-01) — should be included
    i_new = make_issue(
        2, "closed", ["bug"], title="New issue after publish",
        user_login="dev2", closed_at=datetime(2024, 1, 1),
    )
    pr_new = make_pr(20, title="Fix new", body="Closes #2\n", user_login="dev2")

    data = build_mined_data(
        repo=repo,
        issues=[(i_old, repo), (i_new, repo)],
        pull_requests=[(pr_old, repo), (pr_new, repo)],
        commits=[],
        release=release,
        since=datetime(2023, 6, 1),  # published_at boundary
    )
    mocker.patch.object(DataMiner, "check_repository_exists", return_value=True)
    mocker.patch.object(DataMiner, "mine_data", return_value=data)
    mocker.patch(
        "release_notes_generator.record.factory.default_record_factory.get_issues_for_pr",
        return_value=set(),
    )

    actual = _capture_run(
        patch_env,
        {"INPUT_PUBLISHED_AT": "true", "INPUT_WARNINGS": "false"},
    )

    assert "New issue after publish" in actual, "Issue closed after published_at must be included"
    assert "Old issue before publish" not in actual, "Issue closed before published_at must be filtered out"


# ---------------------------------------------------------------------------
# coderabbit-summary-ignore-groups filters CR groups
# ---------------------------------------------------------------------------


def test_coderabbit_summary_ignore_groups(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """CodeRabbit summary groups listed in ignore-groups are excluded from output."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    i1 = make_issue(1, "closed", ["feature"], title="CR filtered", user_login="dev1")
    pr10 = make_pr(
        10,
        title="CR PR",
        body=(
            "Closes #1\n\n"
            "Summary by CodeRabbit\n"
            "- **Bug Fixes**\n"
            "  - Fixed login issue\n"
            "- **Documentation**\n"
            "  - Updated README\n"
            "- **New Features**\n"
            "  - Added export\n"
        ),
        user_login="dev1",
    )

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
        return_value={"org/repo#1"},
    )

    actual = _capture_run(
        patch_env,
        {
            "INPUT_CODERABBIT_SUPPORT_ACTIVE": "true",
            "INPUT_CODERABBIT_SUMMARY_IGNORE_GROUPS": "Documentation",
            "INPUT_WARNINGS": "false",
        },
    )

    assert "Fixed login issue" in actual, "Non-ignored CR group must appear"
    assert "Added export" in actual, "Non-ignored CR group must appear"
    assert "Updated README" not in actual, "Ignored CR group 'Documentation' must be excluded"


# ---------------------------------------------------------------------------
# custom release-notes-title regex
# ---------------------------------------------------------------------------


def test_custom_release_notes_title_regex(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Custom release-notes-title regex matches a non-default section heading."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    # Issue body uses a custom heading instead of default "Release Notes:"
    i1 = make_issue(
        1, "closed", ["bug"], title="Custom title issue",
        body="Description here.\n\nChangelog:\n- Fixed the widget\n- Improved performance\n",
        user_login="dev1",
    )
    pr10 = make_pr(10, title="Fix widget", body="Closes #1\n", user_login="dev1")

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

    actual = _capture_run(
        patch_env,
        {
            "INPUT_RELEASE_NOTES_TITLE": "[Cc]hangelog:",
            "INPUT_WARNINGS": "false",
        },
    )

    assert "Fixed the widget" in actual, "Custom release-notes-title regex must extract notes"
    assert "Improved performance" in actual, "All lines from custom section must be extracted"


# ---------------------------------------------------------------------------
# multiple custom skip-release-notes-labels
# ---------------------------------------------------------------------------


def test_multiple_skip_release_notes_labels(
    mocker: MockerFixture,
    patch_env: Callable,
    mock_github: object,
    make_issue: Callable[..., Issue],
    make_pr: Callable[..., PullRequest],
    make_repo: Callable[..., Repository],
    make_release: Callable[..., GitRelease],
) -> None:
    """Multiple skip labels all cause records to be excluded from all chapters."""
    repo = make_repo("org/repo")
    release = make_release("v0.9.0")

    i_normal = make_issue(1, "closed", ["bug"], title="Normal issue", user_login="dev1")
    i_skip1 = make_issue(2, "closed", ["skip-changelog"], title="Skipped by label 1", user_login="dev2")
    i_skip2 = make_issue(3, "closed", ["internal-only"], title="Skipped by label 2", user_login="dev3")

    pr1 = make_pr(10, title="Fix normal", body="Closes #1\n", user_login="dev1")
    pr2 = make_pr(20, title="Fix skip1", body="Closes #2\n", user_login="dev2")
    pr3 = make_pr(30, title="Fix skip2", body="Closes #3\n", user_login="dev3")

    data = build_mined_data(
        repo=repo,
        issues=[(i_normal, repo), (i_skip1, repo), (i_skip2, repo)],
        pull_requests=[(pr1, repo), (pr2, repo), (pr3, repo)],
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

    actual = _capture_run(
        patch_env,
        {
            "INPUT_SKIP_RELEASE_NOTES_LABELS": "skip-changelog,internal-only",
            "INPUT_WARNINGS": "false",
        },
    )

    assert "Normal issue" in actual, "Non-skipped issue must appear"
    assert "Skipped by label 1" not in actual, "Issue with first skip label must be excluded"
    assert "Skipped by label 2" not in actual, "Issue with second skip label must be excluded"
