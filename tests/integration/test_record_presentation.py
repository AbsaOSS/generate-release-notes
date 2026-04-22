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
"""Offline integration tests — record presentation.

Covers: release notes extraction from issue/PR body, custom row formats,
row-format-link-pr flag, CodeRabbit extraction and ignore-groups,
custom release-notes-title regex, hierarchy parent/sub-issue rendering.
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

    actual = capture_run(patch_env, {"INPUT_WARNINGS": "false"})

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

    actual = capture_run(
        patch_env,
        {
            "INPUT_ROW_FORMAT_ISSUE": "{number} | {title} | {developers}",
            "INPUT_WARNINGS": "false",
        },
    )

    assert "#1 | Custom format bug |" in actual, "Custom row format must be applied"
    assert "developed by" not in actual, "Default format tokens must not appear with custom format"


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

    actual = capture_run(
        patch_env,
        {"INPUT_CODERABBIT_SUPPORT_ACTIVE": "true", "INPUT_WARNINGS": "false"},
    )

    assert "Added new authentication flow" in actual, "CodeRabbit summary line must be extracted"
    assert "Improved error messages" in actual, "CodeRabbit summary line must be extracted"


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

    actual = capture_run(
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

    actual = capture_run(
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

    actual = capture_run(
        patch_env,
        {"INPUT_ROW_FORMAT_LINK_PR": "false", "INPUT_WARNINGS": "true"},
    )

    assert "Unlinked PR" in actual, "PR must appear in output"
    assert "PR:" not in actual, "PR: prefix must not appear when row-format-link-pr=false"


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

    actual = capture_run(
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

    actual = capture_run(
        patch_env,
        {
            "INPUT_RELEASE_NOTES_TITLE": "[Cc]hangelog:",
            "INPUT_WARNINGS": "false",
        },
    )

    assert "Fixed the widget" in actual, "Custom release-notes-title regex must extract notes"
    assert "Improved performance" in actual, "All lines from custom section must be extracted"
