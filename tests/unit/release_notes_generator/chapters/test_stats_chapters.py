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

from release_notes_generator.chapters.stats_chapters import StatsChapters
from release_notes_generator.utils.constants import SKIP_RELEASE_NOTES_LABEL_STATS

_SKIP_LABEL = "skip-release-notes"
_PATCH = "release_notes_generator.chapters.stats_chapters.ActionInputs.get_skip_release_notes_labels"


def _make_stats(mocker, *, skip_labels=None, print_empty=True):
    mocker.patch(_PATCH, return_value=skip_labels if skip_labels is not None else [_SKIP_LABEL])
    return StatsChapters(print_empty_chapters=print_empty)


def test_switch_on_no_skipped(mocker, make_pr):
    """Chapter omitted when no records carry a skip label."""
    sc = _make_stats(mocker)
    pr = make_pr(author="alice", skip=False, labels=["bug"])
    sc.populate({0: pr})
    assert sc.to_string() == ""


def test_switch_on_with_skipped(mocker, make_pr):
    """Chapter rendered when at least one record is skipped."""
    sc = _make_stats(mocker)
    pr = make_pr(author="alice", skip=True, labels=[_SKIP_LABEL, "bug"])
    sc.populate({0: pr})
    assert SKIP_RELEASE_NOTES_LABEL_STATS in sc.to_string()


def test_switch_on_empty_records(mocker):
    """Chapter omitted when records dict is empty."""
    sc = _make_stats(mocker)
    sc.populate({})
    assert sc.to_string() == ""


def test_print_empty_true_shows_zero_skipped_subsection(mocker, make_pr, make_issue):
    """Sub-section with records but none skipped is shown when print_empty=True."""
    sc = _make_stats(mocker, print_empty=True)
    alice_pr1 = make_pr(author="alice", skip=False, labels=["bug"])
    alice_pr2 = make_pr(author="alice", skip=False, labels=["bug"])
    issue_skip = make_issue(author="bob", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: alice_pr1, 1: alice_pr2, 2: issue_skip})
    result = sc.to_string()
    assert "PR Authors" in result
    assert "| @alice | 2 | 0 |" in result


def test_print_empty_false_hides_zero_skipped_subsection(mocker, make_pr, make_issue):
    """Sub-section with records but none skipped is hidden when print_empty=False."""
    sc = _make_stats(mocker, print_empty=False)
    alice_pr1 = make_pr(author="alice", skip=False, labels=["bug"])
    alice_pr2 = make_pr(author="alice", skip=False, labels=["bug"])
    issue_skip = make_issue(author="bob", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: alice_pr1, 1: alice_pr2, 2: issue_skip})
    result = sc.to_string()
    assert "PR Authors" not in result


def test_print_empty_false_still_shows_nonzero_skipped(mocker, make_pr):
    """Sub-section where some records are skipped is shown regardless of print_empty."""
    sc = _make_stats(mocker, print_empty=False)
    pr_skip = make_pr(author="alice", skip=True, labels=[_SKIP_LABEL])
    pr_normal = make_pr(author="alice", skip=False, labels=["bug"])
    sc.populate({0: pr_skip, 1: pr_normal})
    result = sc.to_string()
    assert "PR Authors" in result
    assert "| @alice | 2 | 1 |" in result


def test_no_pr_records(mocker, make_issue):
    """No PullRequestRecord instances → PR Authors sub-section absent."""
    sc = _make_stats(mocker)
    issue_skip = make_issue(author="alice", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: issue_skip})
    result = sc.to_string()
    assert SKIP_RELEASE_NOTES_LABEL_STATS in result
    assert "PR Authors" not in result


def test_single_author_all_skipped(mocker, make_pr):
    """One author with all PRs skipped → @alice | 3 | 3."""
    sc = _make_stats(mocker)
    prs = [make_pr(author="alice", skip=True, labels=[_SKIP_LABEL]) for _ in range(3)]
    sc.populate({i: pr for i, pr in enumerate(prs)})
    assert "| @alice | 3 | 3 |" in sc.to_string()


def test_multiple_authors_mixed_skip(mocker, make_pr):
    """Multiple authors with different skip rates; sorted by skipped count descending."""
    sc = _make_stats(mocker)
    alice_skip1 = make_pr(author="alice", skip=True, labels=[_SKIP_LABEL])
    alice_skip2 = make_pr(author="alice", skip=True, labels=[_SKIP_LABEL])
    alice_normal = make_pr(author="alice", skip=False, labels=["bug"])
    bob_normal1 = make_pr(author="bob", skip=False, labels=["bug"])
    bob_normal2 = make_pr(author="bob", skip=False, labels=["bug"])
    sc.populate({0: alice_skip1, 1: alice_skip2, 2: alice_normal, 3: bob_normal1, 4: bob_normal2})
    result = sc.to_string()
    assert "| @alice | 3 | 2 |" in result
    assert "| @bob | 2 | 0 |" in result
    assert result.index("@alice") < result.index("@bob")


def test_pr_with_no_author(mocker, make_pr):
    """PR with no resolvable author counted under '(no author)' bucket."""
    sc = _make_stats(mocker)
    pr = make_pr(author=None, skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: pr})
    assert "| (no author) | 1 | 1 |" in sc.to_string()


def test_custom_skip_label(mocker, make_pr):
    """Configured skip label other than default is correctly recognised."""
    sc = _make_stats(mocker, skip_labels=["custom-skip"])
    pr = make_pr(author="alice", skip=True, labels=["custom-skip"])
    sc.populate({0: pr})
    assert "| @alice | 1 | 1 |" in sc.to_string()


def test_no_issue_records(mocker, make_pr):
    """No IssueRecord instances → Issue Authors sub-section absent."""
    sc = _make_stats(mocker)
    pr_skip = make_pr(author="alice", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: pr_skip})
    assert "Issue Authors" not in sc.to_string()


def test_no_skipped_issues(mocker, make_pr, make_issue):
    """Issues exist but none skipped; with print_empty=False, sub-section absent."""
    sc = _make_stats(mocker, print_empty=False)
    issue1 = make_issue(author="alice", skip=False, labels=["bug"])
    issue2 = make_issue(author="alice", skip=False, labels=["bug"])
    pr_skip = make_pr(author="charlie", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: issue1, 1: issue2, 2: pr_skip})
    assert "Issue Authors" not in sc.to_string()


def test_author_only_skipped(mocker, make_issue):
    """Issue with author only and skip=True → @alice | 1 | 1."""
    sc = _make_stats(mocker)
    issue = make_issue(author="alice", assignees=[], skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: issue})
    assert "| @alice | 1 | 1 |" in sc.to_string()


def test_author_and_assignee_both_counted(mocker, make_issue):
    """Author and assignee receive independent rows for the same issue."""
    sc = _make_stats(mocker)
    issue = make_issue(author="alice", assignees=["bob"], skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: issue})
    result = sc.to_string()
    assert "| @alice | 1 | 1 |" in result
    assert "| @bob | 1 | 1 |" in result


def test_no_author_with_assignee(mocker, make_issue):
    """No author but has assignee; (no author) bucket and assignee bucket both present."""
    sc = _make_stats(mocker)
    issue = make_issue(author=None, assignees=["bob"], skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: issue})
    result = sc.to_string()
    assert "| (no author) | 1 | 1 |" in result
    assert "| @bob | 1 | 1 |" in result


def test_person_as_author_and_assignee(mocker, make_issue):
    """Person as author of one issue (skipped) and assignee of another (not skipped) → @alice | 2 | 1."""
    sc = _make_stats(mocker)
    issue_a = make_issue(author="alice", assignees=[], skip=True, labels=[_SKIP_LABEL])
    issue_b = make_issue(author="charlie", assignees=["alice"], skip=False, labels=["bug"])
    sc.populate({0: issue_a, 1: issue_b})
    assert "| @alice | 2 | 1 |" in sc.to_string()


def test_mixed_authors_mixed_skip(mocker, make_issue):
    """Multiple people with partial skip; sorted by skipped count descending."""
    sc = _make_stats(mocker)
    alice_skip = make_issue(author="alice", skip=True, labels=[_SKIP_LABEL])
    alice_normal = make_issue(author="alice", skip=False, labels=["bug"])
    bob_normal = make_issue(author="bob", skip=False, labels=["bug"])
    sc.populate({0: alice_skip, 1: alice_normal, 2: bob_normal})
    result = sc.to_string()
    assert "| @alice | 2 | 1 |" in result
    assert "| @bob | 1 | 0 |" in result
    assert result.index("@alice") < result.index("@bob")


def test_no_issue_records_for_types(mocker, make_pr):
    """No IssueRecord instances → Issue Labels sub-section absent."""
    sc = _make_stats(mocker)
    pr_skip = make_pr(author="alice", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: pr_skip})
    assert "Issue Labels" not in sc.to_string()


def test_no_skipped_issues_for_types(mocker, make_pr, make_issue):
    """Issues with labels exist but none skipped; with print_empty=False, sub-section absent."""
    sc = _make_stats(mocker, print_empty=False)
    issue1 = make_issue(author="alice", skip=False, labels=["bug"])
    issue2 = make_issue(author="alice", skip=False, labels=["bug"])
    pr_skip = make_pr(author="charlie", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: issue1, 1: issue2, 2: pr_skip})
    assert "Issue Labels" not in sc.to_string()


def test_single_type_all_skipped(mocker, make_issue):
    """All issues of one type skipped → bug | 3 | 3."""
    sc = _make_stats(mocker)
    issues = [make_issue(author="alice", skip=True, labels=["bug", _SKIP_LABEL]) for _ in range(3)]
    sc.populate({i: issue for i, issue in enumerate(issues)})
    assert "| bug | 3 | 3 |" in sc.to_string()


def test_issue_with_skip_label_only(mocker, make_issue):
    """Issue has only the skip label → falls into (no label) bucket."""
    sc = _make_stats(mocker)
    issue = make_issue(author="alice", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: issue})
    assert "| (no label) | 1 | 1 |" in sc.to_string()


def test_issue_with_no_labels(mocker, make_issue):
    """Issue with no labels at all falls into (no label) bucket."""
    sc = _make_stats(mocker, print_empty=True)
    issue_no_label = make_issue(author="alice", skip=False, labels=[])
    issue_skip = make_issue(author="bob", skip=True, labels=[_SKIP_LABEL, "bug"])
    sc.populate({0: issue_no_label, 1: issue_skip})
    result = sc.to_string()
    assert "| (no label) | 1 | 0 |" in result
    assert "| bug | 1 | 1 |" in result


def test_issue_counts_in_multiple_type_buckets(mocker, make_issue):
    """Issue with two non-skip labels contributes to both type buckets."""
    sc = _make_stats(mocker)
    issue = make_issue(author="alice", skip=True, labels=["bug", "enhancement", _SKIP_LABEL])
    sc.populate({0: issue})
    result = sc.to_string()
    assert "| bug | 1 | 1 |" in result
    assert "| enhancement | 1 | 1 |" in result


def test_mixed_types_mixed_skip(mocker, make_issue):
    """Multiple types with partial skip; sorted by skipped count descending."""
    sc = _make_stats(mocker)
    bug_skip = make_issue(author="alice", skip=True, labels=["bug", _SKIP_LABEL])
    bug_normal = make_issue(author="alice", skip=False, labels=["bug"])
    enh_normal = make_issue(author="alice", skip=False, labels=["enhancement"])
    sc.populate({0: bug_skip, 1: bug_normal, 2: enh_normal})
    result = sc.to_string()
    assert "| bug | 2 | 1 |" in result
    assert "| enhancement | 1 | 0 |" in result
    assert result.index("| bug |") < result.index("| enhancement |")


def test_skip_label_not_a_type_bucket(mocker, make_issue):
    """Skip label name must not appear as a type bucket key."""
    sc = _make_stats(mocker)
    issue = make_issue(author="alice", skip=True, labels=["bug", _SKIP_LABEL])
    sc.populate({0: issue})
    result = sc.to_string()
    assert "| bug | 1 | 1 |" in result
    assert _SKIP_LABEL not in result


def test_pr_label_with_skip(mocker, make_pr):
    """Non-skip label on a skipped PR → bug | 1 | 1 in PR Labels section."""
    sc = _make_stats(mocker)
    pr = make_pr(author="alice", skip=True, labels=["bug", _SKIP_LABEL])
    sc.populate({0: pr})
    assert "| bug | 1 | 1 |" in sc.to_string()


def test_pr_with_no_non_skip_label(mocker, make_pr):
    """PR with only the skip label → (no label) | 1 | 1."""
    sc = _make_stats(mocker)
    pr = make_pr(author="alice", skip=True, labels=[_SKIP_LABEL])
    sc.populate({0: pr})
    assert "| (no label) | 1 | 1 |" in sc.to_string()


def test_skip_label_not_a_label_bucket(mocker, make_pr):
    """Skip label name must not appear as a label bucket key."""
    sc = _make_stats(mocker)
    pr = make_pr(author="alice", skip=True, labels=["bug", _SKIP_LABEL])
    sc.populate({0: pr})
    result = sc.to_string()
    assert "| bug | 1 | 1 |" in result
    assert _SKIP_LABEL not in result


def test_pr_and_issue_same_label_in_separate_sections(mocker, make_pr, make_issue):
    """PR and IssueRecord with the same label each go to their own section (§4 and §3)."""
    sc = _make_stats(mocker)
    pr = make_pr(author="alice", skip=True, labels=["bug", _SKIP_LABEL])
    issue = make_issue(author="bob", skip=False, labels=["bug"])
    sc.populate({0: pr, 1: issue})
    result = sc.to_string()
    assert "Issue Labels" in result
    assert "PR Labels" in result
    # Issue Labels: 1 issue, 0 skipped
    issue_labels_pos = result.index("Issue Labels")
    pr_labels_pos = result.index("PR Labels")
    issue_section = result[issue_labels_pos:pr_labels_pos]
    assert "| bug | 1 | 0 |" in issue_section
    # PR Labels: 1 PR, 1 skipped
    pr_section = result[pr_labels_pos:]
    assert "| bug | 1 | 1 |" in pr_section


def test_mixed_labels_mixed_skip(mocker, make_pr):
    """Multiple labels with partial skip; sorted by skipped count descending."""
    sc = _make_stats(mocker)
    bug_skip1 = make_pr(author="alice", skip=True, labels=["bug", _SKIP_LABEL])
    bug_skip2 = make_pr(author="alice", skip=True, labels=["bug", _SKIP_LABEL])
    bug_normal = make_pr(author="alice", skip=False, labels=["bug"])
    docs1 = make_pr(author="alice", skip=False, labels=["docs"])
    docs2 = make_pr(author="alice", skip=False, labels=["docs"])
    sc.populate({0: bug_skip1, 1: bug_skip2, 2: bug_normal, 3: docs1, 4: docs2})
    result = sc.to_string()
    assert "| bug | 3 | 2 |" in result
    assert "| docs | 2 | 0 |" in result
    assert result.index("| bug |") < result.index("| docs |")


def test_record_counts_in_multiple_label_buckets(mocker, make_pr):
    """Record with two non-skip labels contributes to both label buckets."""
    sc = _make_stats(mocker)
    pr = make_pr(author="alice", skip=True, labels=["bug", "docs", _SKIP_LABEL])
    sc.populate({0: pr})
    result = sc.to_string()
    assert "| bug | 1 | 1 |" in result
    assert "| docs | 1 | 1 |" in result
