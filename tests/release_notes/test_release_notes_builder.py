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
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.builder.builder import ReleaseNotesBuilder
from release_notes_generator.chapters.custom_chapters import CustomChapters

# pylint: disable=pointless-string-statement
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


# pylint: disable=too-few-public-methods
class MockLabel:
    def __init__(self, name):
        self.name = name


DEFAULT_CHANGELOG_URL = "http://example.com/changelog"
default_chapters = [
        {"title": "Breaking Changes 💥", "label": "breaking-change"},
        {"title": "New Features 🎉", "label": "feature"},
        {"title": "New Features 🎉", "label": "enhancement"},
        {"title": "Bugfixes 🛠", "label": "bug"},
    ]

RELEASE_NOTES_NO_DATA = """### Breaking Changes 💥
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

### Direct commits ⚠️
All direct commits are linked pull requests.

### Others - No Topic ⚠️
Previous filters caught all Issues or Pull Requests.

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_NO_DATA_NO_WARNING = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
No entries detected.

### Bugfixes 🛠
No entries detected.

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_NO_DATA_NO_WARNING_NO_EMPTY_CHAPTERS = """#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_NO_DATA_NO_EMPTY_CHAPTERS = RELEASE_NOTES_NO_DATA_NO_WARNING_NO_EMPTY_CHAPTERS

RELEASE_NOTES_DATA_CUSTOM_CHAPTERS_ONE_LABEL = """### Chapter 1 🛠
- #122 _I1+bug_ in #101, #102
  - Fixed bug
  - Improved performance
  + More nice code
    * Awesome architecture
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_CUSTOM_CHAPTERS_ONE_LABEL_HIERARCHY = """### Chapter 1 🛠
 - #122 _I1+bug_ in #123
   - Fixed bug
   - Improved performance
   + More nice code
     * Awesome architecture
   - Fixed bug
   - Improved performance



### New Epics
 - 🔔 _HI200 open_ #200

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_CUSTOM_CHAPTERS_MORE_LABELS_DUPLICITY_REDUCTION_ON = """### Chapter 1 🛠
- #122 _I1+bug-enhancement_ in #101, #102
  - Fixed bug
  - Improved performance
  + More nice code
    * Awesome architecture
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_CUSTOM_CHAPTERS_MORE_LABELS_DUPLICITY_REDUCTION_OFF = """### New Features 🎉
- #1 _I1+0PR+2L-bug-enhancement_ in #101, #102
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

TODO - add bug chapter

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_ISSUE_NO_PR_NO_USER_LABELS = """### Closed Issues without Pull Request ⚠️
- #121 _Fix the bug_ in

### Closed Issues without User Defined Labels ⚠️
- 🔔 #121 _Fix the bug_ in

#### Full Changelog
http://example.com/changelog
"""

# pylint: disable=line-too-long
RELEASE_NOTES_DATA_SERVICE_CHAPTERS_MERGED_PR_NO_ISSUE_NO_USER_LABELS = """### Merged PRs without Issue and User Defined Labels ⚠️
- PR: #123 _Fixed bug_
  - Fixed bug
  - Improved performance

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_PR_NO_ISSUE_NO_USER_LABELS = """### Closed PRs without Issue and User Defined Labels ⚠️
- PR: #123 _Fixed bug_
  - Fixed bug
  - Improved performance
  + More nice code
    * Awesome architecture

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_PR_NO_ISSUE_SKIP_USER_LABELS = RELEASE_NOTES_NO_DATA_NO_WARNING_NO_EMPTY_CHAPTERS

RELEASE_NOTES_DATA_SERVICE_CHAPTERS_OPEN_ISSUE_AND_MERGED_PR_NO_USER_LABELS = """### Merged PRs Linked to 'Not Closed' Issue ⚠️
- #122 _I1 open_ in #101, #102
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_SERVICE_CHAPTERS_OPEN_ISSUE_AND_MERGED_PR_NO_USER_LABELS_ISSUE_NOT_PART_OF_RECORD = """### Others - No Topic ⚠️
- PR: #101 _PR 101_
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_CLOSED_ISSUE_NO_PR_WITH_USER_LABELS = """### Closed Issues without Pull Request ⚠️
- #121 _Fix the bug_ in

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_PR_WITHOUT_USER_LABELS = """### Closed Issues without User Defined Labels ⚠️
- #122 _I1_ in #101, #102
  - Fixed bug
  - Improved performance
  + More nice code
    * Awesome architecture
  - PR 101 1st release note
  - PR 101 2nd release note
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_OPEN_PR_WITHOUT_ISSUE = """### Others - No Topic ⚠️
- PR: #123 _Fix bug_
  - Fixed bug
  - Improved performance

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_MERGED_PR_WITH_USER_LABELS_DUPLICITY_REDUCTION_ON = """### Chapter 1 🛠
- PR: #123 _Fixed bug_
  - Fixed bug
  - Improved performance

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_MERGED_PRS_WITH_OPEN_ISSUES = """### Merged PRs Linked to 'Not Closed' Issue ⚠️
- #122 _I1 open_ in #101
  - PR 101 1st release note
  - PR 101 2nd release note
- #123 _I2 open_ in #102
  - PR 102 1st release note
  - PR 102 2nd release note

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_MERGED_PRS_WITHOUT_USER_LABELS = """### Closed Issues without User Defined Labels ⚠️
- #121 _Fix the bug_ in #123
  - Fixed bug
  - Improved performance
  + More nice code
    * Awesome architecture

#### Full Changelog
http://example.com/changelog
"""

RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_MERGED_PRS_WITH_USER_LABELS_WITH_SKIP_LABEL = RELEASE_NOTES_NO_DATA_NO_WARNING_NO_EMPTY_CHAPTERS

RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_MERGED_PRS_WITH_USER_LABELS = """### Chapter 1 🛠
- #122 _I1+bug_ in #123
  - Fixed bug
  - Improved performance
  + More nice code
    * Awesome architecture
  - Fixed bug
  - Improved performance

#### Full Changelog
http://example.com/changelog
"""

# build


def test_build_no_data():
    custom_chapters = CustomChapters()
    custom_chapters.from_yaml_array(default_chapters)

    expected_release_notes = RELEASE_NOTES_NO_DATA

    builder = ReleaseNotesBuilder(
        records={},  # empty record data set
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters,
    )

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


def test_build_no_data_no_warnings(mocker):
    custom_chapters = CustomChapters()
    custom_chapters.from_yaml_array(default_chapters)
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_warnings", return_value=False)

    expected_release_notes = RELEASE_NOTES_NO_DATA_NO_WARNING

    builder = ReleaseNotesBuilder(
        records={},  # empty record data set
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters,
    )

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


def test_build_no_data_no_warnings_no_empty_chapters(mocker):
    custom_chapters_no_empty_chapters = CustomChapters()
    custom_chapters_no_empty_chapters.from_yaml_array(default_chapters)
    custom_chapters_no_empty_chapters.print_empty_chapters = False
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_warnings", return_value=False)
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    expected_release_notes = RELEASE_NOTES_NO_DATA_NO_WARNING_NO_EMPTY_CHAPTERS

    builder = ReleaseNotesBuilder(
        records={},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_no_empty_chapters,
    )

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


def test_build_no_data_no_empty_chapters(mocker):
    custom_chapters_no_empty_chapters = CustomChapters()
    custom_chapters_no_empty_chapters.from_yaml_array(default_chapters)
    custom_chapters_no_empty_chapters.print_empty_chapters = False
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    expected_release_notes = RELEASE_NOTES_NO_DATA_NO_EMPTY_CHAPTERS

    builder = ReleaseNotesBuilder(
        records={},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_no_empty_chapters,
    )

    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


# Test cases covering data variations
# ---------------------------------------------------------------------------------------------
#   from custom/uer defined chapters
# ---------------------------------------------------------------------------------------------
# Happy paths - see closed issue in used defined chapters
# Test: issue in Closed (1st) state is visible in the release notes - with one label
# "test_name": "test_build_closed_issue_with_one_custom_label",
# "expected_release_notes": release_notes_data_custom_chapters_one_label,
# "records": __get_record_mock_1_issue_with_2_prs(mock_repo(), issue_labels=['bug'])

# Test: issue in Closed (1st) state is visible in the release notes - with more label - duplicity reduction on
# "test_name": "test_build_closed_issue_with_more_custom_labels_duplicity_reduction_on",
# "expected_release_notes": release_notes_data_custom_chapters_more_labels_duplicity_reduction_on,
# "records": __get_record_mock_1_issue_with_2_prs(mock_repo(), issue_labels=['bug', 'enhancement'])

# Test: issue in Closed (1st) state is visible in the release notes - with more label - duplicity reduction off
# TODO - switch off duplicity reduction
# "test_name": "test_build_closed_issue_with_more_custom_labels_duplicity_reduction_off",
# "expected_release_notes": release_notes_data_custom_chapters_more_labels_duplicity_reduction_off,
# "records": __get_record_mock_with_2_prs(issue_labels=['bug', 'enhancement'])

# ---------------------------------------------------------------------------------------------
#   from service chapters point of view
# ---------------------------------------------------------------------------------------------
# Happy paths - see closed issue in services chapters
# Test: issue in Closed (1st) - visible in service chapters - without pr and user defined labels - no labels
# "test_name": "test_build_closed_issue_service_chapter_without_pull_request_and_user_defined_label",
# "expected_release_notes": release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels,
# "records": {0: Record(repo=mock_repo(), issue=__get_default_issue_mock(number=1, state="closed"))}

# Test: pr in merged (1st) state is visible in the release notes service chapters - no labels
# "test_name": "test_build_merged_pr_service_chapter_without_issue_and_user_labels",
# "expected_release_notes": release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels,
# "records": __get_record_mock_1_pr_with_no_issue(mock_repo())

# Test: pr in closed state is visible in the release notes service chapters - no labels
# "test_name": "test_build_merged_pr_service_chapter_without_issue_and_user_labels",
# "expected_release_notes": release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels,
# "records": __get_record_mock_1_pr_with_no_issue(mock_repo(), is_merged=False)

# Test: issue in open state with pr in merged state is visible in the release notes service chapters - no labels
#   Reasons: Issue reopened after PR merge, Issue mention added after PR merge.
# "test_name": "test_build_open_issue_with_merged_pr_service_chapter_linked_to_not_closed_issue",
# "expected_release_notes": release_notes_data_service_chapters_open_issue_and_merged_pr_no_user_labels,
# "records": __get_record_mock_1_issue_with_2_prs(mock_repo(), issue_state="open")

# Test: No Topic service chapter is here to catch unexpected and 'new' data combinations - do not lost them
# ---------------------------------------------------------------------------------------------
#   from Issues states point of view
# ---------------------------------------------------------------------------------------------
# Alternative paths - see issue in all states without labels ==> in correct service chapters
# Test: issue in Open (Initial) state is not visible in the release notes - no labels
# "test_name": "test_build_open_issue",
# "expected_release_notes": release_notes_no_data_no_warning_no_empty_chapters,
# "records": {0: Record(Mock(), __get_default_issue_mock(number=1, state="open"))}

# Test: issue in Open (Reopened) state is not visible in the release notes - no labels
# "test_name": "test_build_reopened_issue",
# "expected_release_notes": release_notes_no_data_no_warning_no_empty_chapters,
# "records": {0: Record(mock_repo(), __get_default_issue_mock(number=1, state="open", state_reason="reopened"))}

# Test: issue in Closed (1st) state is not visible in the release notes - no labels
# "test_name": "test_build_closed_issue",
# "expected_release_notes": release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels,
# "records": {0: Record(mock_repo(), __get_default_issue_mock(number=1, state="closed"))}

# Test: issue in Closed (not_planned) state is visible in the release notes - no labels
# "test_name": "test_build_closed_not_planned_issue",
# "expected_release_notes": release_notes_data_service_chapters_closed_issue_no_pr_no_user_labels,
# "records": {0: Record(mock_repo(),
#  __get_default_issue_mock(number=1, state="closed", state_reason="not_planned"))}


# ---------------------------------------------------------------------------------------------
# Alternative paths - see issue in all logical states ==> in correct service chapters
# Test: Closed Issue without linked PR with user labels ==> not part of custom chapters as there is no merged change
# "test_name": "test_build_closed_issue_with_user_labels_no_prs",
# "expected_release_notes": release_notes_data_closed_issue_no_pr_with_user_labels,
# "records": {0: Record(mock_repo(),
# __get_default_issue_mock(number=1, state="closed", labels=['bug', 'breaking-changes']))}

# Test: Closed Issue without linked PR without user labels
#   - covered in 'test_build_merged_pr_service_chapter_without_issue_and_user_labels'

# Test: Closed Issue with 1+ merged PRs with 1+ user labels
#   - covered in 'test_build_closed_issue_with_more_custom_labels_duplicity_reduction_off'

# Test: Closed Issue with 1+ merged PRs without user labels
# "test_name": "test_build_closed_issue_with_prs_without_user_label",
# "expected_release_notes": release_notes_data_closed_issue_with_pr_without_user_labels,
# "records": __get_record_mock_1_issue_with_2_prs(mock_repo())

# ---------------------------------------------------------------------------------------------
#   from PR states point of view
# ---------------------------------------------------------------------------------------------
# Alternative paths - see pull request in all states ==> in correct service chapters
# Test: Open PR without Issue   ==> Open PR are ignored as they are not merged - no change to document
#   - Note: this should not happen, but if this happens, it will be reported in Others - No Topic chapter
# "test_name": "test_build_open_pr_without_issue",
# "expected_release_notes": release_notes_data_open_pr_without_issue,
# "records": __get_record_mock_1_pr_with_no_issue(mock_repo(), state="open")

# Test: Ready for review - Merged PR (is change in repo)
# "test_name": "test_build_merged_pr_without_issue_ready_for_review",
# "expected_release_notes": release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels,
# "records": __get_record_mock_1_pr_with_no_issue(mock_repo(), state="closed")

# Test: Ready for review - Closed PR (not planned)
# "test_name": "test_build_closed_pr_without_issue_ready_for_review",
# "expected_release_notes": release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels,
# "records": __get_record_mock_1_pr_with_no_issue(mock_repo(), state="closed", is_merged=False)

# Test: Draft - Closed PR (not planned)
# "test_name": "test_build_closed_pr_without_issue_draft",
# "expected_release_notes": release_notes_data_service_chapters_closed_pr_no_issue_no_user_labels,
# "records": __get_record_mock_1_pr_with_no_issue(mock_repo(), state="closed", is_merged=False, is_draft=True)

# ---------------------------------------------------------------------------------------------
# Alternative paths - see pull request in all logical states ==> in correct service chapters
# Test: Merged PR without Issue without user label
#   - covered in 'test_build_merged_pr_service_chapter_without_issue_and_user_labels'

# Test: Merged PR without Issue with more user label - duplicity reduction on
# "test_name": "test_merged_pr_without_issue_with_more_user_labels_duplicity_reduction_on",
# "expected_release_notes": release_notes_data_merged_pr_with_user_labels_duplicity_reduction_on,
# "records": __get_record_mock_1_pr_with_no_issue(mock_repo(), labels=['bug', 'enhancement'])

# Test: Merged PR without Issue with more user label - duplicity reduction off - TODO
# "test_name": "test_merged_pr_without_issue_with_more_user_labels_duplicity_reduction_on",
# "expected_release_notes": release_notes_data_service_chapters_merged_pr_no_issue_no_user_labels,
# "records": __get_record_mock_1_pr_with_no_issue(labels=['bug', 'enhancement'])

# Test: Merged PR with mentioned Open (Init) Issues | same to Reopen as it is same state
# "test_name": "test_merged_pr_with_open_init_issue_mention",
# "expected_release_notes": release_notes_data_merged_prs_with_open_issues,
# "records": __get_record_mock_2_issue_with_2_prs(mock_repo(), issue_1_state="open", issue_2_state="open")

# Test: Merged PR with mentioned Closed Issues
#   - covered in 'test_build_closed_issue_with_prs_without_user_label'

# Test: Merged PR with mentioned Closed (not planned) Issues - without user labels
# "test_name": "test_merged_pr_with_closed_issue_mention_without_user_labels",
# "expected_release_notes": release_notes_data_closed_issue_with_merged_prs_without_user_labels,
# "records": __get_record_mock_1_issue_with_2_prs(mock_repo(), issue_state="closed", is_closed_not_planned=True)

# Test: Merged PR with mentioned Closed (not planned) Issues - with user labels
# "test_name": "test_merged_pr_with_closed_issue_mention_with_user_labels",
# "expected_release_notes": release_notes_data_closed_issue_with_merged_prs_with_user_labels,
# "records": __get_record_mock_1_issue_with_2_prs(mock_repo(), issue_state="closed", is_closed_not_planned=True,
#                                                     issue_labels=['bug', 'enhancement'])

# Test: Merged PR without mentioned Issue
#   - covered in 'test_build_merged_pr_service_chapter_without_issue_and_user_labels'


def test_build_closed_issue_with_one_custom_label(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_two_pulls, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CUSTOM_CHAPTERS_ONE_LABEL
    rec = record_with_issue_closed_two_pulls
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_issue_with_more_custom_labels_duplicity_reduction_on(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_two_pulls, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CUSTOM_CHAPTERS_MORE_LABELS_DUPLICITY_REDUCTION_ON
    rec = record_with_issue_closed_two_pulls
    rec.issue.labels.append(MockLabel("enhancement"))
    rec.issue.title = "I1+bug-enhancement"
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_issue_service_chapter_without_pull_request_and_user_defined_label(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_no_pull, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_ISSUE_NO_PR_NO_USER_LABELS
    rec = record_with_issue_closed_no_pull
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_merged_pr_service_chapter_without_issue_and_user_labels(
    custom_chapters_not_print_empty_chapters, pull_request_record_merged, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_MERGED_PR_NO_ISSUE_NO_USER_LABELS
    rec = pull_request_record_merged
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_pr_service_chapter_without_issue_and_user_labels(
    custom_chapters_not_print_empty_chapters, pull_request_record_closed, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_PR_NO_ISSUE_NO_USER_LABELS
    rec = pull_request_record_closed
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_open_issue_with_merged_pr_service_chapter_linked_to_not_closed_issue(
    custom_chapters_not_print_empty_chapters, record_with_issue_open_two_pulls_closed, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_OPEN_ISSUE_AND_MERGED_PR_NO_USER_LABELS
    rec = record_with_issue_open_two_pulls_closed
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_open_issue(custom_chapters_not_print_empty_chapters, record_with_issue_open_no_pull, mocker):
    expected_release_notes = RELEASE_NOTES_NO_DATA_NO_WARNING_NO_EMPTY_CHAPTERS
    rec = record_with_issue_open_no_pull
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_issue(custom_chapters_not_print_empty_chapters, record_with_issue_closed_no_pull, mocker):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_ISSUE_NO_PR_NO_USER_LABELS
    rec = record_with_issue_closed_no_pull
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    print("Actual:\n%s", actual_release_notes)
    print("Expected:\n%s", expected_release_notes)
    assert expected_release_notes == actual_release_notes


def test_build_reopened_issue(custom_chapters_not_print_empty_chapters, record_with_issue_open_no_pull, mocker):
    expected_release_notes = RELEASE_NOTES_NO_DATA_NO_WARNING_NO_EMPTY_CHAPTERS
    rec = record_with_issue_open_no_pull
    rec.issue.state_reason = "reopened"
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_not_planned_issue(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_no_pull, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_ISSUE_NO_PR_NO_USER_LABELS
    rec = record_with_issue_closed_no_pull
    rec.issue.state_reason = "not_planned"
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_issue_with_user_labels_no_prs(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_no_pull, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CLOSED_ISSUE_NO_PR_WITH_USER_LABELS
    rec = record_with_issue_closed_no_pull
    rec._labels = {"bug", "breaking-changes"}
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_issue_with_prs_without_user_label(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_two_pulls, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_PR_WITHOUT_USER_LABELS
    rec = record_with_issue_closed_two_pulls
    rec._labels = {"label1", "label2"}
    rec.issue.title = "I1"
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_open_pr_without_issue(
    custom_chapters_not_print_empty_chapters, pull_request_record_open, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_OPEN_PR_WITHOUT_ISSUE
    rec = pull_request_record_open
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_merged_pr_without_issue_ready_for_review(
    custom_chapters_not_print_empty_chapters, pull_request_record_merged, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_MERGED_PR_NO_ISSUE_NO_USER_LABELS
    rec = pull_request_record_merged
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_pr_without_issue_ready_for_review(
    custom_chapters_not_print_empty_chapters, pull_request_record_closed, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_PR_NO_ISSUE_NO_USER_LABELS
    rec = pull_request_record_closed
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_pr_without_issue_non_draft(
    custom_chapters_not_print_empty_chapters, pull_request_record_closed, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_PR_NO_ISSUE_NO_USER_LABELS
    rec = pull_request_record_closed
    rec.pull_request.draft = False
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


# TODO - research situation when PR is not merged and is in draft state

def test_merged_pr_without_issue_with_more_user_labels_duplicity_reduction_on(
    custom_chapters_not_print_empty_chapters, pull_request_record_merged, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_MERGED_PR_WITH_USER_LABELS_DUPLICITY_REDUCTION_ON
    rec = pull_request_record_merged
    rec._labels = {"bug", "enhancement"}
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_merged_pr_with_open_init_issue_mention(
    custom_chapters_not_print_empty_chapters, record_with_two_issue_open_two_pulls_closed, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_MERGED_PRS_WITH_OPEN_ISSUES
    records = record_with_two_issue_open_two_pulls_closed
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records=records,
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_merged_pr_with_closed_issue_mention_without_user_labels(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_one_pull, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_MERGED_PRS_WITHOUT_USER_LABELS
    rec = record_with_issue_closed_one_pull
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_merged_pr_with_closed_issue_mention_with_user_labels(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_one_pull_merged, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_MERGED_PRS_WITH_USER_LABELS
    rec = record_with_issue_closed_one_pull_merged
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes

def test_merged_pr_with_closed_issue_mention_with_user_labels_with_skip_label_on_issue(
    custom_chapters_not_print_empty_chapters, record_with_issue_closed_one_pull_merged_skip, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CLOSED_ISSUE_WITH_MERGED_PRS_WITH_USER_LABELS_WITH_SKIP_LABEL
    rec = record_with_issue_closed_one_pull_merged_skip
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_closed_pr_service_chapter_without_issue_with_skip_label_on_pr(
        custom_chapters_not_print_empty_chapters, pull_request_record_closed_with_skip_label, mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_SERVICE_CHAPTERS_CLOSED_PR_NO_ISSUE_SKIP_USER_LABELS
    rec = pull_request_record_closed_with_skip_label
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)

    builder = ReleaseNotesBuilder(
        records={rec.record_id: rec},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    assert expected_release_notes == actual_release_notes


def test_build_hierarchy_issue_with_one_custom_label(
        custom_chapters_not_print_empty_chapters,
        record_with_hierarchy_issues,
        record_with_issue_closed_one_pull_merged,
        record_with_pr_only,
        record_with_direct_commit,
        mocker
):
    expected_release_notes = RELEASE_NOTES_DATA_CUSTOM_CHAPTERS_ONE_LABEL_HIERARCHY
    rec_1 = record_with_hierarchy_issues
    rec_2 = record_with_issue_closed_one_pull_merged
    rec_3 = record_with_pr_only
    rec_4 = record_with_direct_commit
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_print_empty_chapters", return_value=False)
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_hierarchy", return_value=True)
    mocker.patch("release_notes_generator.builder.builder.ActionInputs.get_row_format_hierarchy_issue", return_value="{type}: _{title}_ {number}")

    builder = ReleaseNotesBuilder(
        records={rec_1.record_id: rec_1, rec_2.record_id: rec_2, rec_3.record_id: rec_3, rec_4.record_id: rec_4},
        changelog_url=DEFAULT_CHANGELOG_URL,
        custom_chapters=custom_chapters_not_print_empty_chapters,
    )

    actual_release_notes = builder.build()

    print("XXX - actual release notes")
    print(actual_release_notes)
    print("XXX")

    assert expected_release_notes == actual_release_notes
