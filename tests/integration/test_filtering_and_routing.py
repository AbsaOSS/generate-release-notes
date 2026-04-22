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
"""Offline integration tests — filtering, routing, skip and exclude rules.

Covers: skip labels, service chapter exclude (global and per-chapter), record routing
(closed-not-merged PR, open issue with PR), no-previous-release filter,
published-at filtering, multiple skip-release-notes labels.
"""

from collections.abc import Callable
from datetime import datetime

from pytest_mock import MockerFixture

from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.data.miner import DataMiner
from tests.integration.conftest import build_mined_data, capture_run


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

    actual = capture_run(patch_env)

    assert "Normal" in actual
    assert "Skipped" not in actual
    assert "Dual skip" not in actual


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

    actual = capture_run(
        patch_env,
        {"INPUT_SERVICE_CHAPTER_EXCLUDE": exclude_yaml, "INPUT_WARNINGS": "true"},
    )

    assert "Excluded issue" not in actual, "Globally excluded record must be absent from all chapters"
    assert "Normal bug" in actual, "Non-excluded record must still appear"


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

    actual = capture_run(
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

    actual = capture_run(patch_env)

    assert "Old bug" in actual, "Issue must be included when no previous release exists"
    assert "Old commit" in actual, "Commit must be included when no previous release exists"


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

    actual = capture_run(patch_env, {"INPUT_WARNINGS": "true"})

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

    actual = capture_run(
        patch_env,
        {"INPUT_WARNINGS": "true", "INPUT_PRINT_EMPTY_CHAPTERS": "false"},
    )

    assert "Merged PRs Linked to 'Not Closed' Issue" in actual, "Chapter heading must appear for open issue with PR"
    assert "Open issue with PR" in actual, "Open issue record must appear in the chapter"


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

    actual = capture_run(
        patch_env,
        {"INPUT_PUBLISHED_AT": "true", "INPUT_WARNINGS": "false"},
    )

    assert "New issue after publish" in actual, "Issue closed after published_at must be included"
    assert "Old issue before publish" not in actual, "Issue closed before published_at must be filtered out"


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

    actual = capture_run(
        patch_env,
        {
            "INPUT_SKIP_RELEASE_NOTES_LABELS": "skip-changelog,internal-only",
            "INPUT_WARNINGS": "false",
        },
    )

    assert "Normal issue" in actual, "Non-skipped issue must appear"
    assert "Skipped by label 1" not in actual, "Issue with first skip label must be excluded"
    assert "Skipped by label 2" not in actual, "Issue with second skip label must be excluded"
