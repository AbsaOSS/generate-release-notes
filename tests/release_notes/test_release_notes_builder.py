from datetime import datetime
from unittest.mock import Mock

import pytest
import json

from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.formatter.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder


issues = [
    # labeled issue with one PR
    Mock(spec=Issue, number=1, title="Issue 1", is_closed=True, labels=["bug"]),            # with one PR
    Mock(spec=Issue, number=4, title="Issue 4", is_closed=True, labels=["enhancement"]),    # with two PRs
    Mock(spec=Issue, number=7, title="Issue 7", is_closed=True, labels=["enhancement"]),    # with no PRs ==> no rls notes
    Mock(spec=Issue, number=8, title="Issue 8", is_closed=True, labels=["spike"]),          # with no PRs, no user defined label ==> no rls notes
]

pulls = [
    # [0] - PR 1 to Issue 1
    PullRequest(
        id=1,
        number=101,
        title="PR 1",
        labels=[],
        body="Dummy body\n\nRelease notes:\n- First release note\n- Second release note\n",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=datetime.now(),
        merged_at=datetime.now(),
        milestone=None,
        url="http://example.com/pr1",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    ),
    # [1] - PR without Issue and without Release notes in description - with no labels
    PullRequest(
        id=2,
        number=102,
        title="PR 2",
        labels=[],
        body="Dummy body",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=datetime.now(),
        merged_at=datetime.now(),
        milestone=None,
        url="http://example.com/pr2",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    ),
    # [2] - PR without Issue and without Release notes in description - without labels
    PullRequest(
        id=3,
        number=103,
        title="PR 3",
        labels=['bug'],
        body="Dummy body",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=datetime.now(),
        merged_at=datetime.now(),
        milestone=None,
        url="http://example.com/pr2",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    ),
    # [3, 4] - 2 PRs with Issue '2' - no labels, both with Release notes
    PullRequest(
        id=5,
        number=105,
        title="PR 5",
        labels=[],
        body="Dummy body\n\nRelease notes:\n- PR 5 release note\n",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=datetime.now(),
        merged_at=datetime.now(),
        milestone=None,
        url="http://example.com/pr5",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    ),
    PullRequest(
        id=6,
        number=106,
        title="PR 6",
        labels=['bug'],     # wrong label - should be ignored by logic
        body="Dummy body\n\nRelease notes:\n- PR 6 release note\n",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=datetime.now(),
        merged_at=datetime.now(),
        milestone=None,
        url="http://example.com/pr6",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    )
]

records_empty = {}
records = {}
records[1] = Record(issues[0])
records[2] = Record()
records[3] = Record()
records[4] = Record(issues[1])
records[5] = Record(issues[2])
records[6] = Record(issues[3])
records[1].register_pull_request(pulls[0])
records[2].register_pull_request(pulls[1])
records[3].register_pull_request(pulls[2])
records[4].register_pull_request(pulls[3])
records[4].register_pull_request(pulls[4])

formatter = RecordFormatter()
changelog_url = "http://example.com/changelog"
custom_chapters = CustomChapters()
chapters_json = json.dumps([
    {"title": "Breaking Changes 💥", "label": "breaking-change"},
    {"title": "New Features 🎉", "label": "feature"},
    {"title": "New Features 🎉", "label": "enhancement"},
    {"title": "Bugfixes 🛠", "label": "bug"}
])
custom_chapters.from_json(chapters_json)

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

### Closed Issues without Release Notes ⚠️
All closed issues have release notes.

### Merged PRs without Linked Issue⚠️
All merged PRs are linked to issues.

### Merged PRs without Labels ⚠️
All merged PRs have label.

### Merged PRs Linked to Open Issue ⚠️
All merged PRs are linked to Closed issues.

### Closed PRs without Linked Issue ⚠️
All closed PRs are linked to issues.

### Closed PRs without Labels ⚠️
All closed PRs have label.

#### Full Changelog
http://example.com/changelog
"""


release_notes_full = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
- #4 _Issue 4_ implemented by TODO
  - PR 5 release note
  - PR 6 release note
- #7 _Issue 7_ implemented by TODO

### Bugfixes 🛠
- #1 _Issue 1_ implemented by TODO
  - First release note
  - Second release note
- PR 3

### Closed Issues without Pull Request ⚠️
- #7 _Issue 7_ implemented by TODO

### Closed Issues without User Defined Labels ⚠️
All closed issues contain at least one of user defined labels.

### Closed Issues without Release Notes ⚠️
- #7 _Issue 7_ implemented by TODO

### Merged PRs without Linked Issue⚠️
All merged PRs are linked to issues.

### Merged PRs without Labels ⚠️
All merged PRs have label.

### Merged PRs Linked to Open Issue ⚠️
All merged PRs are linked to Closed issues.   BUG

### Closed PRs without Linked Issue ⚠️    BUG
All closed PRs are linked to issues.

### Closed PRs without Labels ⚠️    BUG
All closed PRs are linked to issues.

#### Full Changelog
http://example.com/changelog
"""

release_notes_full_no_empty_chapters = """### New Features 🎉
- #4 _Issue 4_ implemented by TODO
  - PR 5 release note
  - PR 6 release note
- #7 _Issue 7_ implemented by TODO

### Bugfixes 🛠
- #1 _Issue 1_ implemented by TODO
  - First release note
  - Second release note
- PR 3

xx

#### Full Changelog
http://example.com/changelog
"""

release_notes_full_no_warnings = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
- #4 _Issue 4_ implemented by TODO
  - PR 5 release note
  - PR 6 release note
- #7 _Issue 7_ implemented by TODO

### Bugfixes 🛠
- #1 _Issue 1_ implemented by TODO
  - First release note
  - Second release note
- PR 3

#### Full Changelog
http://example.com/changelog
"""


# build

def test_build_full_with_empty_chapters():
    builder = ReleaseNotesBuilder(records=records, changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters)
    expected_release_notes = release_notes_full
    actual_release_notes = builder.build()
    print("Actual:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


# def test_build_no_data_with_empty_chapters():
#     builder = ReleaseNotesBuilder(records=records_empty, changelog_url=changelog_url, formatter=formatter,
#                                   custom_chapters=custom_chapters)
#     expected_release_notes = release_notes_no_data
#     actual_release_notes = builder.build()
#     print("Actual - no data:\n" + actual_release_notes)
#     assert expected_release_notes == actual_release_notes
#
#
# def test_build_no_warnings():
#     builder = ReleaseNotesBuilder(records=records, changelog_url=changelog_url, formatter=formatter,
#                                   custom_chapters=custom_chapters, warnings=False)
#     expected_release_notes = release_notes_full_no_warnings
#     actual_release_notes = builder.build()
#     print("Actual:\n" + actual_release_notes)
#     assert expected_release_notes == actual_release_notes
#
#
# def test_build_full_no_empty_chapters():
#     custom_chapters_no_empty_chapters = custom_chapters
#     custom_chapters_no_empty_chapters.print_empty_chapters = False
#     expected_release_notes = release_notes_full_no_empty_chapters
#
#     builder = ReleaseNotesBuilder(records=records, changelog_url=changelog_url, formatter=formatter,
#                                   custom_chapters=custom_chapters, print_empty_chapters=False)
#
#     actual_release_notes = builder.build()
#     print("Actual:\n" + actual_release_notes)
#     assert expected_release_notes == actual_release_notes


if __name__ == '__main__':
    pytest.main()
