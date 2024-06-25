from unittest.mock import Mock

import github
import pytest
import json

from datetime import datetime
from github_integration.model.pull_request import PullRequest
from github_integration.model.issue import Issue
from release_notes.formatter.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder
from github.Issue import Issue as GitIssue
from github.PullRequest import PullRequest as GitPullRequest


def generate_full_dataset() -> dict[int, Record]:
    # Mock the get_labels method
    mock_label_1 = Mock()
    mock_label_1.name = "bug"
    mock_label_2 = Mock()
    mock_label_2.name = "enhancement"
    mock_label_3 = Mock()
    mock_label_3.name = "spike"
    mock_label_4 = Mock()
    mock_label_4.name = "error"

    mock_git_issue_id_1 = Mock(spec=GitIssue)
    mock_git_issue_id_1.number = 1
    mock_git_issue_id_1.title = "I1+1PR+l-bug"
    mock_git_issue_id_1.body = "Dummy body"
    mock_git_issue_id_1.state = "closed"
    mock_git_issue_id_1.get_labels.return_value = [mock_label_1]
    mock_git_issue_id_1.created_at = datetime.now()

    mock_git_issue_id_2 = Mock(spec=GitIssue)
    mock_git_issue_id_2.number = 4
    mock_git_issue_id_2.title = "I4+2PR+l-enhancement"
    mock_git_issue_id_2.body = "Dummy body"
    mock_git_issue_id_2.state = "closed"
    mock_git_issue_id_2.get_labels.return_value = [mock_label_2]
    mock_git_issue_id_2.created_at = datetime.now()

    mock_git_issue_id_3 = Mock(spec=GitIssue)
    mock_git_issue_id_3.number = 7
    mock_git_issue_id_3.title = "I7+0PR+l-enhancement"
    mock_git_issue_id_3.body = "Dummy body"
    mock_git_issue_id_3.state = "closed"
    mock_git_issue_id_3.get_labels.return_value = [mock_label_2]
    mock_git_issue_id_3.created_at = datetime.now()

    mock_git_issue_id_4 = Mock(spec=GitIssue)
    mock_git_issue_id_4.number = 8
    mock_git_issue_id_4.title = "I8+0PR+l-spike"
    mock_git_issue_id_4.body = "Dummy body"
    mock_git_issue_id_4.state = "closed"
    mock_git_issue_id_4.get_labels.return_value = [mock_label_3]
    mock_git_issue_id_4.created_at = datetime.now()

    mock_git_issue_id_5 = Mock(spec=GitIssue)
    mock_git_issue_id_5.number = 9
    mock_git_issue_id_5.title = "I9+0PR+l-any"
    mock_git_issue_id_5.body = "Dummy body"
    mock_git_issue_id_5.state = "closed"
    mock_git_issue_id_5.get_labels.return_value = []
    mock_git_issue_id_5.created_at = datetime.now()

    issues = [
        Issue(mock_git_issue_id_1),     # labeled issue with one PR
        Issue(mock_git_issue_id_2),     # labeled issue with two PRs
        Issue(mock_git_issue_id_3),     # labeled issue with no PRs ==> no rls notes
        Issue(mock_git_issue_id_4),     # labeled issue with no PRs, no user defined label ==> no rls notes
        Issue(mock_git_issue_id_5),     # labeled issue with no PRs, no label ==> no rls notes
    ]

    mock_git_pr_id_101 = Mock(spec=GitPullRequest)
    mock_git_pr_id_101.number = 101
    mock_git_pr_id_101.title = "PR1+2xRLS+1I+l-no"
    mock_git_pr_id_101.body = "Dummy body\nCloses #1\n\nRelease notes:\n- PR 1 First release note\n- PR 1 Second release note\n"
    mock_git_pr_id_101.get_labels.return_value = []
    mock_git_pr_id_101.state = "merged"
    mock_git_pr_id_101.created_at = datetime.now()
    mock_git_pr_id_101.updated_at = datetime.now()
    mock_git_pr_id_101.closed_at = None
    mock_git_pr_id_101.merged_at = datetime.now()

    mock_git_pr_id_102 = Mock(spec=GitPullRequest)
    mock_git_pr_id_102.number = 102
    mock_git_pr_id_102.title = "PR2+2xRLS+0I+l-no"
    mock_git_pr_id_102.body = "Dummy body\n\nRelease notes:\n- PR 2 First release note\n- PR 2 Second release note\n"
    mock_git_pr_id_102.get_labels.return_value = []
    mock_git_pr_id_102.state = "merged"
    mock_git_pr_id_102.created_at = datetime.now()
    mock_git_pr_id_102.updated_at = datetime.now()
    mock_git_pr_id_102.closed_at = None
    mock_git_pr_id_102.merged_at = datetime.now()

    mock_git_pr_id_103 = Mock(spec=GitPullRequest)
    mock_git_pr_id_103.number = 103
    mock_git_pr_id_103.title = "PR3+0xRLS+0I+l-bug"
    mock_git_pr_id_103.body = "Dummy body"
    mock_git_pr_id_103.get_labels.return_value = [mock_label_4]
    mock_git_pr_id_103.state = "closed"
    mock_git_pr_id_103.created_at = datetime.now()
    mock_git_pr_id_103.updated_at = datetime.now()
    mock_git_pr_id_103.closed_at = datetime.now()
    mock_git_pr_id_103.merged_at = None

    mock_git_pr_id_105 = Mock(spec=GitPullRequest)
    mock_git_pr_id_105.number = 105
    mock_git_pr_id_105.title = "PR5+2xRLS+1I+l-no"
    mock_git_pr_id_105.body = "Dummy body\nCloses #2\n\nRelease notes:\n- PR 5 release note\n"
    mock_git_pr_id_105.get_labels.return_value = []
    mock_git_pr_id_105.labels = []
    mock_git_pr_id_105.state = "merged"
    mock_git_pr_id_105.created_at = datetime.now()
    mock_git_pr_id_105.updated_at = datetime.now()
    mock_git_pr_id_105.closed_at = None
    mock_git_pr_id_105.merged_at = datetime.now()

    mock_git_pr_id_106 = Mock(spec=GitPullRequest)
    mock_git_pr_id_106.number = 106
    mock_git_pr_id_106.title = "PR6+1xRLS+1I+l-no"
    mock_git_pr_id_106.body = "Dummy body\nCloses #1\n\nRelease notes:\n- PR 6 release note\n"
    mock_git_pr_id_106.get_labels.return_value = [mock_label_1]
    mock_git_pr_id_106.labels = ['bug']
    mock_git_pr_id_106.state = "merged"
    mock_git_pr_id_106.created_at = datetime.now()
    mock_git_pr_id_106.updated_at = datetime.now()
    mock_git_pr_id_106.closed_at = None
    mock_git_pr_id_106.merged_at = datetime.now()

    mock_git_pr_id_111 = Mock(spec=GitPullRequest)
    mock_git_pr_id_111.number = 111
    mock_git_pr_id_111.title = "PR11+1xRLS+1I+l-no"
    mock_git_pr_id_111.body = "Dummy body\nFixes #10\n\nRelease notes:\n- PR 11 release note\n"
    mock_git_pr_id_111.get_labels.return_value = []
    mock_git_pr_id_111.state = "merged"
    mock_git_pr_id_111.created_at = datetime.now()
    mock_git_pr_id_111.updated_at = datetime.now()
    mock_git_pr_id_111.closed_at = None
    mock_git_pr_id_111.merged_at = datetime.now()

    pulls = [
        PullRequest(mock_git_pr_id_101),    # [0] - PR 1 to Issue 1
        PullRequest(mock_git_pr_id_102),    # [1] - PR without Issue and with Release notes in description - with bug label
        PullRequest(mock_git_pr_id_103),    # [2] - PR without Issue and without Release notes in description - with no labels - closed state
        PullRequest(mock_git_pr_id_105),    # [3, 4] - 2 PRs with Issue '2' - no labels, both with Release notes
        PullRequest(mock_git_pr_id_106),
        PullRequest(mock_git_pr_id_111),    # [5] - 1 PRs with Issue '11' - no labels, with Release notes - PR linked to Open Issue
    ]

    records_full = {}
    records_full[1] = Record(issues[0])                      # with one PR
    records_full[2] = Record()
    records_full[3] = Record()
    records_full[4] = Record(issues[1])                      # with two PRs
    records_full[5] = Record(issues[2])                      # with no PRs ==> no rls notes
    records_full[6] = Record(issues[3])                      # with no PRs, no user defined label ==> no rls notes
    records_full[7] = Record(issues[4])                      # with no PRs, no label ==> no rls notes
    records_full[8] = Record()                               # Issue is not in closed state ==> not returned in mining

    records_full[1].register_pull_request(pulls[0])
    records_full[2].register_pull_request(pulls[1])          # PR only, without Release notes in description - with no labels - merged state
    records_full[3].register_pull_request(pulls[2])          # PR only, without Release notes in description - with no labels - closed state
    records_full[4].register_pull_request(pulls[3])
    records_full[4].register_pull_request(pulls[4])
    records_full[8].register_pull_request(pulls[5])

    return records_full

# TODO check state vs date when reopen - issue & PR

formatter = RecordFormatter()
changelog_url = "http://example.com/changelog"
chapters_json = json.dumps([
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


release_notes_full = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
- #4 _I4+2PR+l-enhancement_ in [#105](https://github.com/None/pull/105), [#106](https://github.com/None/pull/106)
  - PR 5 release note
  - PR 6 release note

### Bugfixes 🛠
- #1 _I1+1PR+l-bug_ in [#101](https://github.com/None/pull/101)
  - PR 1 First release note
  - PR 1 Second release note

### Closed Issues without Pull Request ⚠️
- #7 _I7+0PR+l-enhancement_
- #8 _I8+0PR+l-spike_
- #9 _I9+0PR+l-any_

### Closed Issues without User Defined Labels ⚠️
- #8 _I8+0PR+l-spike_
- #9 _I9+0PR+l-any_

### Merged PRs without Issue and User Defined Labels ⚠️
- PR: #102 _PR2+2xRLS+0I+l-no_, implemented by None
  - PR 2 First release note
  - PR 2 Second release note

### Closed PRs without Issue and User Defined Labels ⚠️
- PR: #103 _PR3+0xRLS+0I+l-bug_, implemented by None

### Merged PRs Linked to 'Not Closed' Issue ⚠️
- PR: #111 _PR11+1xRLS+1I+l-no_, implemented by None
  - PR 11 release note

### Others - No Topic ⚠️
Previous filters caught all Issues or Pull Requests.

#### Full Changelog
http://example.com/changelog
"""

release_notes_full_no_empty_chapters = """### New Features 🎉
- #4 _I4+2PR+l-enhancement_ in [#105](https://github.com/None/pull/105), [#106](https://github.com/None/pull/106)
  - PR 5 release note
  - PR 6 release note

### Bugfixes 🛠
- #1 _I1+1PR+l-bug_ in [#101](https://github.com/None/pull/101)
  - PR 1 First release note
  - PR 1 Second release note

### Closed Issues without Pull Request ⚠️
- #7 _I7+0PR+l-enhancement_
- #8 _I8+0PR+l-spike_
- #9 _I9+0PR+l-any_

### Closed Issues without User Defined Labels ⚠️
- #8 _I8+0PR+l-spike_
- #9 _I9+0PR+l-any_

### Merged PRs without Issue and User Defined Labels ⚠️
- PR: #102 _PR2+2xRLS+0I+l-no_, implemented by None
  - PR 2 First release note
  - PR 2 Second release note

### Closed PRs without Issue and User Defined Labels ⚠️
- PR: #103 _PR3+0xRLS+0I+l-bug_, implemented by None

### Merged PRs Linked to 'Not Closed' Issue ⚠️
- PR: #111 _PR11+1xRLS+1I+l-no_, implemented by None
  - PR 11 release note

#### Full Changelog
http://example.com/changelog
"""

release_notes_full_no_warnings = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
- #4 _I4+2PR+l-enhancement_ in [#105](https://github.com/None/pull/105), [#106](https://github.com/None/pull/106)
  - PR 5 release note
  - PR 6 release note

### Bugfixes 🛠
- #1 _I1+1PR+l-bug_ in [#101](https://github.com/None/pull/101)
  - PR 1 First release note
  - PR 1 Second release note

#### Full Changelog
http://example.com/changelog
"""


# build

def test_build_full_with_empty_chapters():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(chapters_json)

    expected_release_notes = release_notes_full

    builder = ReleaseNotesBuilder(records=generate_full_dataset(), changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters)

    actual_release_notes = builder.build()
    # print("Actual - no data:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


def test_build_no_data_with_empty_chapters():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(chapters_json)

    expected_release_notes = release_notes_no_data

    builder = ReleaseNotesBuilder(
        records={},
        changelog_url=changelog_url,
        formatter=formatter,
        custom_chapters=custom_chapters)

    actual_release_notes = builder.build()
    # print("Actual - no data:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


def test_build_no_warnings():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(chapters_json)

    expected_release_notes = release_notes_full_no_warnings

    builder = ReleaseNotesBuilder(
        records=generate_full_dataset(),
        changelog_url=changelog_url,
        formatter=formatter,
        custom_chapters=custom_chapters, warnings=False)

    actual_release_notes = builder.build()
    # print("Actual:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


def test_build_full_no_empty_chapters():
    custom_chapters_no_empty_chapters = CustomChapters()
    custom_chapters_no_empty_chapters.from_json(chapters_json)
    custom_chapters_no_empty_chapters.print_empty_chapters = False

    expected_release_notes = release_notes_full_no_empty_chapters

    builder = ReleaseNotesBuilder(
        records=generate_full_dataset(),
        changelog_url=changelog_url,
        formatter=formatter,
        custom_chapters=custom_chapters_no_empty_chapters,
        print_empty_chapters=False)

    actual_release_notes = builder.build()
    # print("Actual:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


if __name__ == '__main__':
    pytest.main()
