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
"""Offline integration tests — chapter features.

Covers: warnings flag, print_empty_chapters, chapter ordering, hidden custom chapters,
hidden service chapters, multi-label chapters, service chapter ordering, super-chapters.
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

    actual = capture_run(patch_env, {"INPUT_WARNINGS": "false"})

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

    actual = capture_run(patch_env, {"INPUT_PRINT_EMPTY_CHAPTERS": "false", "INPUT_WARNINGS": "false"})

    assert "Bugfixes" in actual
    assert "Features" not in actual
    assert "Enhancements" not in actual


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

    actual = capture_run(patch_env, {"INPUT_CHAPTERS": chapters_yaml, "INPUT_WARNINGS": "false"})

    pos_a = actual.index("A chapter")
    pos_b = actual.index("B chapter")
    pos_c = actual.index("C chapter")
    assert pos_a < pos_b < pos_c, "Chapters must appear in ascending order-field sequence"


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

    actual = capture_run(
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

    actual = capture_run(
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

    actual = capture_run(
        patch_env,
        {"INPUT_CHAPTERS": chapters_yaml, "INPUT_WARNINGS": "false", "INPUT_PRINT_EMPTY_CHAPTERS": "false"},
    )

    assert "### Improvements" in actual
    assert "Feature item" in actual, "Record with 'feature' label must match the multi-label chapter"
    assert "Enhancement item" in actual, "Record with 'enhancement' label must match the multi-label chapter"
    assert "Bug item" not in actual, "Record with unmatched label must not appear (print_empty=false, no bug chapter)"


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
    actual = capture_run(
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

    actual = capture_run(
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
