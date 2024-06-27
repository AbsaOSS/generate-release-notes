from typing import Optional
from unittest.mock import Mock

import pytest
import json

from datetime import datetime
from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.formatter.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder
from github.Issue import Issue as GitIssue
from github.PullRequest import PullRequest as GitPullRequest

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
        - Open                              [state = open]                          "this state is not mined"
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
                                    is_merged: bool = True) -> PullRequest:
    mock_pr = Mock(spec=GitPullRequest)
    mock_pr.state = state
    mock_pr.number = number
    mock_pr.title = f"PR {number}"

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
                                         pr_with_rls_notes: bool = True, second_pr_merged: bool = True) -> dict[int, Record]:
    # create 1 closed issue without PR
    issue = __get_default_issue_mock(number=1, state=issue_state, labels=issue_labels)
    # create 2 PRs
    pr1 = __get_default_pull_request_mock(issue_number=1, number=101, with_rls_notes=pr_with_rls_notes)
    pr2 = __get_default_pull_request_mock(issue_number=1, number=102, with_rls_notes=pr_with_rls_notes,
                                          is_merged=second_pr_merged)

    records = {}
    if issue_state == "closed":
        records[0] = Record(issue)
    else:
        records[0] = Record()               # Note: Issue in open state is not registered to record set
    records[0].register_pull_request(pr1)
    records[0].register_pull_request(pr2)

    return records


def __get_record_mock_1_pr_with_no_issue(state: str = "closed", is_merged: bool = True, labels: list[str] = None,
                                         with_rls_notes: bool = True) -> dict[int, Record]:
    # create 2 PRs
    pr1 = __get_default_pull_request_mock(number=101, state=state, is_merged=is_merged, with_rls_notes=with_rls_notes,
                                          labels=labels)

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
- #1 _I1+0PR+1L-bug_ in [#101](https://github.com/None/pull/101), [#102](https://github.com/None/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_custom_chapters_more_labels_duplicity_reduction_on = """### New Features 🎉
- #1 _I1+0PR+2L-bug-enhancement_ in [#101](https://github.com/None/pull/101), [#102](https://github.com/None/pull/102)
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_data_custom_chapters_more_labels_duplicity_reduction_off = """### New Features 🎉
- #1 _I1+0PR+2L-bug-enhancement_ in [#101](https://github.com/None/pull/101), [#102](https://github.com/None/pull/102)
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
    # Happy paths - see closed issue in used defined chapters
    {
        # Goal: issue in Closed (1st) state is visible in the release notes - with one label
        "test_name": "test_build_closed_issue_with_one_custom_label",
        "expected_release_notes": release_notes_data_custom_chapters_one_label,
        "records": __get_record_mock_1_issue_with_2_prs(issue_labels=['bug'])
    },
    {
        # Goal: issue in Closed (1st) state is visible in the release notes - with more label - duplicity reduction on
        "test_name": "test_build_closed_issue_with_more_custom_labels_duplicity_reduction_on",
        "expected_release_notes": release_notes_data_custom_chapters_more_labels_duplicity_reduction_on,
        "records": __get_record_mock_1_issue_with_2_prs(issue_labels=['bug', 'enhancement'])
    },
    # {
    #     # Goal: issue in Closed (1st) state is visible in the release notes - with more label - duplicity reduction off
    #     # TODO - switch off duplicity reduction
    #     "test_name": "test_build_closed_issue_with_more_custom_labels_duplicity_reduction_off",
    #     "expected_release_notes": release_notes_data_custom_chapters_more_labels_duplicity_reduction_off,
    #     "records": __get_record_mock_with_2_prs(issue_labels=['bug', 'enhancement'])
    # },
    # ---------------------------------------------------------------------------------------------
    # Happy paths - see closed issue in services chapters
    {
        # Goal: issue in Closed (1st) - visible in service chapters - without pull requests and user defined labels - no labels
        "test_name": "test_build_closed_issue_service_chapter_without_pull_request_and_user_defined_label",
        "expected_release_notes": release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels,
        "records": {0: Record(__get_default_issue_mock(number=1, state="closed"))}
    },
    {
        # Goal: pr in merged (1st) state is visible in the release notes service chapters - no labels
        "test_name": "test_build_merged_pr_service_chapter_without_issue_and_user_labels",
        "expected_release_notes": release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels,
        "records": __get_record_mock_1_pr_with_no_issue()
    },
    {
        # Goal: pr in closed state is visible in the release notes service chapters - no labels
        "test_name": "test_build_merged_pr_service_chapter_without_issue_and_user_labels",
        "expected_release_notes": release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels,
        "records": __get_record_mock_1_pr_with_no_issue(is_merged=False)
    },
    {
        # Goal: issue in open state with pr in merged state is visible in the release notes service chapters - no labels
        "test_name": "test_build_open_issue_with_merged_pr_service_chapter_linked_to_not_closed_issue",
        "expected_release_notes": release_notes_data_service_chapters_open_issue_and_merged_pr_no_user_labels,
        "records": __get_record_mock_1_issue_with_2_prs(issue_state="open")
    },
    # Goal: No Topic service chapter is here to catch unexpected and 'new' data combinations - do not lost them
    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see issue in all states (except 1st closed) without labels ==> in correct service chapters
    # TODO next

    # {
    #     # Goal: issue in Open (Initial) state is not visible in the release notes - no labels
    #     "test_name": "test_build_open_issue",
    #     "expected_release_notes": release_notes_no_data,
    #     "records": {0: Record(__get_default_issue_mock(number=1, state="open"))}
    # },
    # {
    #     # Goal: issue in Open (Reopened) state is not visible in the release notes - no labels
    #     "test_name": "test_build_reopened_issue",
    #     "expected_release_notes": release_notes_no_data,
    #     "records": {0: Record(__get_default_issue_mock(number=1, state="open", state_reason="reopened"))}
    # },
    # {
    #     # Goal: issue in Closed (not_planned) state is visible in the release notes - no labels
    #     "test_name": "test_build_closed_not_planned_issue",
    #     "expected_release_notes": release_notes_no_data,
    #     "records": {0: Record(__get_default_issue_mock(number=1, state="closed", state_reason="not_planned"))}
    # }

    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see issue in all logical states ==> in correct service chapters

    # TODO next

    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see pull request in all states ==> in correct service chapters

    # TODO next

    # ---------------------------------------------------------------------------------------------
    # Alternative paths - see pull request in all logical states ==> in correct service chapters

    # TODO next

]


@pytest.mark.parametrize("test_case", test_cases, ids=[tc["test_name"] for tc in test_cases])
def test_release_notes_builder(test_case):
    # Extract values from test case
    expected_release_notes = test_case.get("expected_release_notes", release_notes_no_data)
    records = test_case.get("records", {})
    changelog_url = test_case.get("changelog_url", default_changelog_url)
    formatter = test_case.get("formatter", default_formatter)
    chapters_json = test_case.get("chapters_json", default_chapters_json)

    custom_chapters = CustomChapters(print_empty_chapters=False)
    custom_chapters.from_json(chapters_json)

    builder = ReleaseNotesBuilder(records=records,
                                  changelog_url=changelog_url,
                                  formatter=formatter,
                                  custom_chapters=custom_chapters,
                                  print_empty_chapters=False)

    actual_release_notes = builder.build()
    print(f"Actual - {test_case['test_name']}:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


if __name__ == '__main__':
    pytest.main()
