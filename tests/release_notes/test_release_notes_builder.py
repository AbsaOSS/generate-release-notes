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
    Mock(spec=Issue, number=1, title="Issue 1", is_closed=True, labels=["bug"]),
]

pulls = [
    # PR 1 to Issue 1
    PullRequest(
        id=1,
        number=101,
        title="PR 1",
        labels=[],
        body="Dummy body\n\nRelease notes:\n- First release note\n- Second release note\n",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=None,
        merged_at=None,
        milestone=None,
        url="http://example.com/pr1",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    ),
    # PR without Issue and without Release notes in description - with labels
    PullRequest(
        id=2,
        number=102,
        title="PR 2",
        labels=[],
        body="Dummy body",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=None,
        merged_at=None,
        milestone=None,
        url="http://example.com/pr2",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    ),
    # PR without Issue and without Release notes in description - without labels
    PullRequest(
        id=3,
        number=103,
        title="PR 3",
        labels=['bug'],
        body="Dummy body",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        closed_at=None,
        merged_at=None,
        milestone=None,
        url="http://example.com/pr2",
        issue_url=None,
        html_url=None,
        patch_url=None,
        diff_url=None
    )
]

records = {}
records[1] = Record(issues[0])
records[2] = Record()
records[3] = Record()
records[1].register_pull_request(pulls[0])
records[2].register_pull_request(pulls[1])
records[3].register_pull_request(pulls[2])

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

release_notes_full = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
No entries detected.

### Bugfixes 🛠
- #1 _Issue 1_ implemented by TODO
  - First release note
  - Second release note
- PR 3

x### Closed Issues without Pull Request ⚠️
All closed issues linked to a Pull Request.

### Closed Issues without User Defined Labels ⚠️
All closed issues contain at least one of user defined labels.

### Closed Issues without Release Notes ⚠️
All closed issues have release notes.

### Merged PRs without Linked Issue and Custom Labels ⚠️
All merged PRs are linked to issues.

### Merged PRs Linked to Open Issue ⚠️
All merged PRs are linked to Closed issues.

### Closed PRs without Linked Issue and Custom Labels ⚠️
All closed PRs are linked to issues.x

#### Full Changelog
http://example.com/changelog
"""

release_notes_full_no_empty_chapters = """### Bugfixes 🛠
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
No entries detected.

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


def test_build_no_warnings():
    builder = ReleaseNotesBuilder(records=records, changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters, warnings=False)
    expected_release_notes = release_notes_full_no_warnings
    actual_release_notes = builder.build()
    print("Actual:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


def test_build_full_no_empty_chapters():
    custom_chapters_no_empty_chapters = custom_chapters
    custom_chapters_no_empty_chapters.print_empty_chapters = False
    expected_release_notes = release_notes_full_no_empty_chapters

    builder = ReleaseNotesBuilder(records=records, changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters, print_empty_chapters=False)

    actual_release_notes = builder.build()
    print("Actual:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


if __name__ == '__main__':
    pytest.main()
