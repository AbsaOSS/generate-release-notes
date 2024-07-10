from typing import Optional
from unittest.mock import Mock

import pytest
import json

from datetime import datetime

from github import Github
from github.Repository import Repository
from github.Issue import Issue as GitIssue, Issue
from github.PullRequest import PullRequest as GitPullRequest, PullRequest

from release_notes.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder


"""
    Issue can be in 2 states (each in 2 'sub' states):
        - Open
            - Open (initial)                [state_reason = null]
            - Reopened                      [state_reason = "reopened"]
        - Closed
            - Closed                        [state_reason = null]
            - Closed (Not planned)          [state_reason = "not_planned"]
          
    Issue can have these logical states:
        - by linked PR
            - With one
            - With multiple
            - Without
        - by user labels
            - With one
            - With multiple
            - Without
        
    Pull Request can be in 2 states:    
        - Open                              [state = open]                          
        - Open (Reopened)                   [state = open, no other flag detected - additional comment required]  
        
        Ready for review
        - Closed                            [state - closed, all *_at = time, draft = false]
        - Closed (not planned)              [state = closed, merged_at = null, draft = false]
        
        Draft
        - xx Closed xx                      [state - closed, Not possible to merge !!!]
        - Closed (not planned)              [state = closed, merged_at = null, draft = true]           
        
    Pull Request can have these logical states:
        - by user labels
            - With one
            - With multiple
            - Without
        - by link/mention Issue
            - With one in state
                - Open (init)
                - Open (Reopened)
                - Closed
                - Closed (not planned)                
            - With multiple in these states
                - Open (init)
                - Open (Reopened)
                - Closed
                - Closed (not planned)
            - Without linked Issue								
"""


def __get_default_issue_mock(number: int, state: str, labels: list[str] = None,
                             state_reason: Optional[str] = None) -> Issue:
    mock_issue = Mock(spec=GitIssue)
    mock_issue.number = number
    mock_issue.body = "Dummy body"
    mock_issue.state = state
    mock_issue.created_at = datetime.now()
    mock_issue.state_reason = state_reason

    if labels is None:
        mock_issue.title = f"I1+0PR+0L"
        mock_issue.get_labels.return_value = []
    else:
        labels_str = "-".join(labels)
        labels_mocks = []
        for label in labels:
            mock_label = Mock()
            mock_label.name = label
            labels_mocks.append(mock_label)

        mock_issue.title = f"I1+0PR+{len(labels)}L-{labels_str}"
        mock_issue.get_labels.return_value = labels_mocks

    return Issue(mock_issue)


def __get_default_pull_request_mock(issue_number: Optional[int] = None, state="closed", number: int = 101,
                                    with_rls_notes: bool = True, labels: list[str] = None,
                                    is_merged: bool = True, is_draft: bool = False) -> PullRequest:
    mock_pr = Mock(spec=GitPullRequest)
    mock_pr.state = state
    mock_pr.number = number
    mock_pr.title = f"PR {number}"
    mock_pr.draft = is_draft

    mock_pr.body = "Dummy body"
    if issue_number is not None:
        mock_pr.body += f"\nCloses #{issue_number}"
    if with_rls_notes:
        mock_pr.body += f"\n\nRelease notes:\n- PR {number} 1st release note\n- PR {number} 2nd release note\n"

    labels_mocks = []
    if labels is not None:
        for label in labels:
            mock_label = Mock()
            mock_label.name = label
            labels_mocks.append(mock_label)
    mock_pr.get_labels.return_value = labels_mocks

    mock_pr.created_at = datetime.now()
    mock_pr.updated_at = datetime.now()

    if is_merged:
        mock_pr.merged_at = datetime.now()
        mock_pr.closed_at = datetime.now()
    else:
        mock_pr.merged_at = None
        mock_pr.closed_at = datetime.now()

    return PullRequest(mock_pr)


def __get_record_mock_1_issue_with_2_prs(issue_state: str = "closed", issue_labels: list[str] = None,
                                         pr_with_rls_notes: bool = True, second_pr_merged: bool = True,
                                         is_closed_not_planned:bool = False) -> dict[int, Record]:
    # create 1 issue
    state_reason = None
    if is_closed_not_planned:
        state_reason = "not_planned"

    issue = __get_default_issue_mock(number=1, state=issue_state, labels=issue_labels, state_reason=state_reason)

    # create 2 PRs
    pr1 = __get_default_pull_request_mock(issue_number=1, number=101, with_rls_notes=pr_with_rls_notes)
    pr2 = __get_default_pull_request_mock(issue_number=1, number=102, with_rls_notes=pr_with_rls_notes,
                                          is_merged=second_pr_merged)
    records = {}
    if issue_state == "closed":
        records[0] = Record(issue)
    else:
        records[0] = Record()
    records[0].register_pull_request(pr1)
    records[0].register_pull_request(pr2)

    return records


def __get_record_mock_2_issue_with_2_prs(issue_1_state: str = "closed", issue_2_state: str = "closed",
                                         issue_1_labels: list[str] = None, issue_2_labels: list[str] = None,
                                         pr_with_rls_notes: bool = True, second_pr_merged: bool = True)-> dict[int, Record]:
    # create 2 issues
    issue1 = __get_default_issue_mock(number=1, state=issue_1_state, labels=issue_1_labels)
    issue2 = __get_default_issue_mock(number=2, state=issue_2_state, labels=issue_2_labels)
    # create 2 PRs per issue
    pr1 = __get_default_pull_request_mock(issue_number=1, number=101, with_rls_notes=pr_with_rls_notes)
    pr2 = __get_default_pull_request_mock(issue_number=1, number=102, with_rls_notes=pr_with_rls_notes,
                                          is_merged=second_pr_merged)

    records = {}
    if issue_1_state == "closed":
        records[0] = Record(issue1)
    else:
        records[0] = Record()
    if issue_2_state == "closed":
        records[1] = Record(issue2)
    else:
        records[1] = Record()
    records[0].register_pull_request(pr1)
    records[1].register_pull_request(pr2)

    return records


def __get_record_mock_1_pr_with_no_issue(state: str = "closed", is_merged: bool = True, labels: list[str] = None,
                                         with_rls_notes: bool = True, is_draft: bool = False) -> dict[int, Record]:
    # create 2 PRs
    pr1 = __get_default_pull_request_mock(number=101, state=state, is_merged=is_merged, with_rls_notes=with_rls_notes,
                                          labels=labels, is_draft=is_draft)

    records = {}
    records[0] = Record()
    records[0].register_pull_request(pr1)

    return records


default_formatter = RecordFormatter()
default_changelog_url = "http://example.com/changelog"
default_chapters_json = json.dumps([
    {"title": "Breaking Changes 💥", "label": "breaking-change"},
    {"title": "New Features 🎉", "label": "feature"},
    {"title": "New Features 🎉", "label": "enhancement"},
    {"title": "Bugfixes 🛠", "label": "bug"}
])

release_notes_no_data = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
No entries detected.

### Bugfixes 🛠
No entries detected.

### Closed Issues without Pull Request ⚠️
All closed issues linked to a Pull Request.

### Closed Issues without User Defined Labels ⚠️
All closed issues contain at least one of user defined labels.

### Merged PRs without Issue and User Defined Labels ⚠️
All merged PRs are linked to issues.

### Closed PRs without Issue and User Defined Labels ⚠️
All closed PRs are linked to issues.

### Merged PRs Linked to 'Not Closed' Issue ⚠️
All merged PRs are linked to Closed issues.

### Others - No Topic ⚠️
Previous filters caught all Issues or Pull Requests.

#### Full Changelog
http://example.com/changelog
"""

release_notes_no_data_no_warning = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
No entries detected.

### Bugfixes 🛠
No entries detected.

#### Full Changelog
http://example.com/changelog
"""

release_notes_no_data_no_warning_no_empty_chapters = """#### Full Changelog
http://example.com/changelog
"""

release_notes_no_data_no_empty_chapters = release_notes_no_data_no_warning_no_empty_chapters

release_notes_data_custom_chapters_one_label = """### Bugfixes 🛠
- #1 _I1+0PR+1L-bug_ in [#101](https://github.com/test/full_name/pull/101), [#102](https://github.com/test/full_name/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_custom_chapters_more_labels_duplicity_reduction_on = """### New Features 🎉
- #1 _I1+0PR+2L-bug-enhancement_ in [#101](https://github.com/test/full_name/pull/101), [#102](https://github.com/test/full_name/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_custom_chapters_more_labels_duplicity_reduction_off = """### New Features 🎉
- #1 _I1+0PR+2L-bug-enhancement_ in [#101](https://github.com/test/full_name/pull/101), [#102](https://github.com/test/full_name/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

TODO - add bug chapter

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels = """### Closed Issues without Pull Request ⚠️
- #1 _I1+0PR+0L_

### Closed Issues without User Defined Labels ⚠️
- #1 _I1+0PR+0L_

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels = """### Merged PRs without Issue and User Defined Labels ⚠️
- PR: #101 _PR 101_
  - PR 101 1st release note
  - PR 101 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels = """### Closed PRs without Issue and User Defined Labels ⚠️
- PR: #101 _PR 101_
  - PR 101 1st release note
  - PR 101 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_service_chapters_open_issue_and_merged_pr_no_user_labels = """### Merged PRs Linked to 'Not Closed' Issue ⚠️
- PR: #101 _PR 101_
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_closed_issue_no_pr_with_user_labels = """### Closed Issues without Pull Request ⚠️
- #1 _I1+0PR+2L-bug-breaking-changes_

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_closed_issue_with_pr_without_user_labels = """### Closed Issues without User Defined Labels ⚠️
- #1 _I1+0PR+0L_ in [#101](https://github.com/test/full_name/pull/101), [#102](https://github.com/test/full_name/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_open_pr_without_issue = """### Others - No Topic ⚠️
- PR: #101 _PR 101_
  - PR 101 1st release note
  - PR 101 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_merged_pr_with_user_labels_duplicity_reduction_on = """### New Features 🎉
- PR: #101 _PR 101_
  - PR 101 1st release note
  - PR 101 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_merged_prs_with_open_issues = """### Merged PRs Linked to 'Not Closed' Issue ⚠️
- PR: #101 _PR 101_
  - PR 101 1st release note
  - PR 101 2nd release note
- PR: #102 _PR 102_
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_closed_issue_with_merged_prs_without_user_labels = """### Closed Issues without User Defined Labels ⚠️
- #1 _I1+0PR+0L_ in [#101](https://github.com/test/full_name/pull/101), [#102](https://github.com/test/full_name/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_closed_issue_with_merged_prs_with_user_labels = """### New Features 🎉
- #1 _I1+0PR+2L-bug-enhancement_ in [#101](https://github.com/test/full_name/pull/101), [#102](https://github.com/test/full_name/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

# build


def test_build_no_data():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(default_chapters_json)

    expected_release_notes = release_notes_no_data

    builder = ReleaseNotesBuilder(
        records={},                         # empty record data set
        changelog_url=default_changelog_url,
        formatter=default_formatter,
        custom_chapters=custom_chapters)

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


def test_build_no_data_no_warnings():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(default_chapters_json)

    expected_release_notes = release_notes_no_data_no_warning

    builder = ReleaseNotesBuilder(
        records={},                         # empty record data set
        changelog_url=default_changelog_url,
        formatter=default_formatter,
        custom_chapters=custom_chapters,
        warnings=False)

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


def test_build_no_data_no_warnings_no_empty_chapters():
    custom_chapters_no_empty_chapters = CustomChapters()
    custom_chapters_no_empty_chapters.from_json(default_chapters_json)
    custom_chapters_no_empty_chapters.print_empty_chapters = False

    expected_release_notes = release_notes_no_data_no_warning_no_empty_chapters

    builder = ReleaseNotesBuilder(
        records={},
        changelog_url=default_changelog_url,
        formatter=default_formatter,
        custom_chapters=custom_chapters_no_empty_chapters,
        warnings=False,
        print_empty_chapters=False)

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


def test_build_no_data_no_empty_chapters():
    custom_chapters_no_empty_chapters = CustomChapters()
    custom_chapters_no_empty_chapters.from_json(default_chapters_json)
    custom_chapters_no_empty_chapters.print_empty_chapters = False

    expected_release_notes = release_notes_no_data_no_empty_chapters

    builder = ReleaseNotesBuilder(
        records={},
        changelog_url=default_changelog_url,
        formatter=default_formatter,
        custom_chapters=custom_chapters_no_empty_chapters,
        print_empty_chapters=False)

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


# Define test cases
test_cases = [
    # ---------------------------------------------------------------------------------------------
    #   from custom/uer defined chapters
    # ---------------------------------------------------------------------------------------------
    # Happy paths - see closed issue in used defined chapters
    {
        # Test: issue in Closed (1st) state is visible in the release notes - with one label
        "test_name": "test_build_closed_issue_with_one_custom_label",
        "expected_release_notes": release_notes_data_custom_chapters_one_label,
        "records": __get_record_mock_1_issue_with_2_prs(issue_labels=['bug'])
    },
    {
        # Test: issue in Closed (1st) state is visible in the release notes - with more label - duplicity reduction on
        "test_name": "test_build_closed_issue_with_more_custom_labels_duplicity_reduction_on",
        "expected_release_notes": release_notes_data_custom_chapters_more_labels_duplicity_reduction_on,
        "records": __get_record_mock_1_issue_with_2_prs(issue_labels=['bug', 'enhancement'])
    },
    # {
    #     # Test: issue in Closed (1st) state is visible in the release notes - with more label - duplicity reduction off
    #     # TODO - switch off duplicity reduction
    #     "test_name": "test_build_closed_issue_with_more_custom_labels_duplicity_reduction_off",
    #     "expected_release_notes": release_notes_data_custom_chapters_more_labels_duplicity_reduction_off,
    #     "records": __get_record_mock_with_2_prs(issue_labels=['bug', 'enhancement'])
    # },
    # ---------------------------------------------------------------------------------------------
    #   from service chapters point of view
    # ---------------------------------------------------------------------------------------------
    # Happy paths - see closed issue in services chapters
    {
        # Test: issue in Closed (1st) - visible in service chapters - without pull requests and user defined labels - no labels
        "test_name": "test_build_closed_issue_service_chapter_without_pull_request_and_user_defined_label",
        "expected_release_notes": release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels,
        "records": {0: Record(__get_default_issue_mock(number=1, state="closed"))}
    },
    {
        # Test: pr in merged (1st) state is visible in the release notes service chapters - no labels
        "test_name": "test_build_merged_pr_service_chapter_without_issue_and_user_labels",
        "expected_release_notes": release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels,
        "records": __get_record_mock_1_pr_with_no_issue()
    },
    {
        # Test: pr in closed state is visible in the release notes service chapters - no labels
        "test_name": "test_build_merged_pr_service_chapter_without_issue_and_user_labels",
        "expected_release_notes": release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels,
        "records": __get_record_mock_1_pr_with_no_issue(is_merged=False)
    },
    {
        # Test: issue in open state with pr in merged state is visible in the release notes service chapters - no labels
        "test_name": "test_build_open_issue_with_merged_pr_service_chapter_linked_to_not_closed_issue",
        "expected_release_notes": release_notes_data_service_chapters_open_issue_and_merged_pr_no_user_labels,
        "records": __get_record_mock_1_issue_with_2_prs(issue_state="open")
    },
    # Test: No Topic service chapter is here to catch unexpected and 'new' data combinations - do not lost them
    # ---------------------------------------------------------------------------------------------
    #   from Issues states point of view
    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see issue in all states without labels ==> in correct service chapters
    {
        # Test: issue in Open (Initial) state is not visible in the release notes - no labels
        "test_name": "test_build_open_issue",
        "expected_release_notes": release_notes_no_data_no_warning_no_empty_chapters,
        "records": {0: Record(__get_default_issue_mock(number=1, state="open"))}
    },
    {
        # Test: issue in Open (Reopened) state is not visible in the release notes - no labels
        "test_name": "test_build_reopened_issue",
        "expected_release_notes": release_notes_no_data_no_warning_no_empty_chapters,
        "records": {0: Record(__get_default_issue_mock(number=1, state="open", state_reason="reopened"))}
    },
    {
        # Test: issue in Closed (1st) state is not visible in the release notes - no labels
        "test_name": "test_build_closed_issue",
        "expected_release_notes": release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels,
        "records": {0: Record(__get_default_issue_mock(number=1, state="closed"))}
    },
    {
        # Test: issue in Closed (not_planned) state is visible in the release notes - no labels
        "test_name": "test_build_closed_not_planned_issue",
        "expected_release_notes": release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels,
        "records": {0: Record(__get_default_issue_mock(number=1, state="closed", state_reason="not_planned"))}
    },

    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see issue in all logical states ==> in correct service chapters
    {
        # Test: Closed Issue without linked PR with user labels ==> not part of custom chapters as there is no merged change
        "test_name": "test_build_closed_issue_with_user_labels_no_prs",
        "expected_release_notes": release_notes_data_closed_issue_no_pr_with_user_labels,
        "records": {0: Record(__get_default_issue_mock(number=1, state="closed", labels=['bug', 'breaking-changes']))}
    },

    # Test: Closed Issue without linked PR without user labels
    #   - covered in 'test_build_merged_pr_service_chapter_without_issue_and_user_labels'

    # Test: Closed Issue with 1+ merged PRs with 1+ user labels
    #   - covered in 'test_build_closed_issue_with_more_custom_labels_duplicity_reduction_off'

    {
        # Test: Closed Issue with 1+ merged PRs without user labels
        "test_name": "test_build_closed_issue_with_prs_without_user_label",
        "expected_release_notes": release_notes_data_closed_issue_with_pr_without_user_labels,
        "records": __get_record_mock_1_issue_with_2_prs()
    },

    # ---------------------------------------------------------------------------------------------
    #   from PR states point of view
    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see pull request in all states ==> in correct service chapters
    {
        # Test: Open PR without Issue   ==> Open PR are ignored as they are not merged - no change to document
        #   - Note: this should not happen, but if this happens, it will be reported in Others - No Topic chapter
        "test_name": "test_build_open_pr_without_issue",
        "expected_release_notes": release_notes_data_open_pr_without_issue,
        "records": __get_record_mock_1_pr_with_no_issue(state="open")
    },
    {
        # Test: Ready for review - Merged PR (is change in repo)
        "test_name": "test_build_merged_pr_without_issue_ready_for_review",
        "expected_release_notes": release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels,
        "records": __get_record_mock_1_pr_with_no_issue(state="closed")
    },
    {
        # Test: Ready for review - Closed PR (not planned)
        "test_name": "test_build_closed_pr_without_issue_ready_for_review",
        "expected_release_notes": release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels,
        "records": __get_record_mock_1_pr_with_no_issue(state="closed", is_merged=False)
    },
    {
        # Test: Draft - Closed PR (not planned)
        "test_name": "test_build_closed_pr_without_issue_draft",
        "expected_release_notes": release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels,
        "records": __get_record_mock_1_pr_with_no_issue(state="closed", is_merged=False, is_draft=True)
    },

    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see pull request in all logical states ==> in correct service chapters

    # Test: Merged PR without Issue without user label
    #   - covered in 'test_build_merged_pr_service_chapter_without_issue_and_user_labels'

    {
        # Test: Merged PR without Issue with more user label - duplicity reduction on
        "test_name": "test_merged_pr_without_issue_with_more_user_labels_duplicity_reduction_on",
        "expected_release_notes": release_notes_data_merged_pr_with_user_labels_duplicity_reduction_on,
        "records": __get_record_mock_1_pr_with_no_issue(labels=['bug', 'enhancement'])
    },
    # {
    #     # Test: Merged PR without Issue with more user label - duplicity reduction off - TODO
    #     "test_name": "test_merged_pr_without_issue_with_more_user_labels_duplicity_reduction_on",
    #     "expected_release_notes": release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels,
    #     "records": __get_record_mock_1_pr_with_no_issue(labels=['bug', 'enhancement'])
    # },
    {
        # Test: Merged PR with mentioned Open (Init) Issues | same to Reopen as it is same state
        "test_name": "test_merged_pr_with_open_init_issue_mention",
        "expected_release_notes": release_notes_data_merged_prs_with_open_issues,
        "records": __get_record_mock_2_issue_with_2_prs(issue_1_state="open", issue_2_state="open")
    },


    # Test: Merged PR with mentioned Closed Issues
    #   - covered in 'test_build_closed_issue_with_prs_without_user_label'
    {
        # Test: Merged PR with mentioned Closed (not planned) Issues - without user labels
        "test_name": "test_merged_pr_with_closed_issue_mention_without_user_labels",
        "expected_release_notes": release_notes_data_closed_issue_with_merged_prs_without_user_labels,
        "records": __get_record_mock_1_issue_with_2_prs(issue_state="closed", is_closed_not_planned=True)
    },
    {
        # Test: Merged PR with mentioned Closed (not planned) Issues - with user labels
        "test_name": "test_merged_pr_with_closed_issue_mention_with_user_labels",
        "expected_release_notes": release_notes_data_closed_issue_with_merged_prs_with_user_labels,
        "records": __get_record_mock_1_issue_with_2_prs(issue_state="closed", is_closed_not_planned=True,
                                                        issue_labels=['bug', 'enhancement'])
    },

    # Test: Merged PR without mentioned Issue
    #   - covered in 'test_build_merged_pr_service_chapter_without_issue_and_user_labels'
]


# @pytest.mark.parametrize("test_case", test_cases, ids=[tc["test_name"] for tc in test_cases])
# def test_release_notes_builder(test_case):
#     # Extract values from test case
#     expected_release_notes = test_case.get("expected_release_notes", release_notes_no_data)
#     records = test_case.get("records", {})
#     changelog_url = test_case.get("changelog_url", default_changelog_url)
#     formatter = test_case.get("formatter", default_formatter)
#     chapters_json = test_case.get("chapters_json", default_chapters_json)
#
#     custom_chapters = CustomChapters(print_empty_chapters=False)
#     custom_chapters.from_json(chapters_json)
#
#     g = Mock(spec=Github)
#     repository_mock = Mock(spec=Repository)
#     repository_mock.full_name = 'test/full_name'
#
#     builder = ReleaseNotesBuilder(records=records,
#                                   changelog_url=changelog_url,
#                                   formatter=formatter,
#                                   custom_chapters=custom_chapters,
#                                   print_empty_chapters=False)
#
#     actual_release_notes = builder.build()
#     print(f"Actual - {test_case['test_name']}:\n" + actual_release_notes)
#     assert expected_release_notes == actual_release_notes


if __name__ == '__main__':
    pytest.main()
