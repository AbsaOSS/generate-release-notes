import pytest
import json

from datetime import datetime
from github_integration.model.pull_request import PullRequest
from github_integration.model.issue import Issue
from release_notes.formatter.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder


def generate_full_dataset() -> dict[int, Record]:
    issues = [
        # labeled issue with one PR
        Issue(id=1, number=1, title="I1+1PR+l-bug", body="Dummy body", state="closed", labels=["bug"], created_at=datetime.now()),
        # labeled issue with two PRs
        Issue(id=2, number=4, title="I4+2PR+l-enhancement", body="Dummy body", state="closed", labels=["enhancement"], created_at=datetime.now()),
        # labeled issue with no PRs ==> no rls notes
        Issue(id=3, number=7, title="I7+0PR+l-enhancement", body="Dummy body", state="closed", labels=["enhancement"], created_at=datetime.now()),
        # labeled issue with no PRs, no user defined label ==> no rls notes
        Issue(id=4, number=8, title="I8+0PR+l-spike", body="Dummy body", state="closed", labels=["spike"], created_at=datetime.now()),
        # labeled issue with no PRs, no label ==> no rls notes
        Issue(id=5, number=9, title="I9+0PR+l-any", body="Dummy body", state="closed", labels=[], created_at=datetime.now()),
    ]

    pulls = [
        # [0] - PR 1 to Issue 1
        PullRequest(
            id=1,
            number=101,
            title="PR1+2xRLS+1I+l-no",
            labels=[],
            body="Dummy body\nCloses #1\n\nRelease notes:\n- PR 1 First release note\n- PR 1 Second release note\n",
            state="merged",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=None,
            merged_at=datetime.now(),
            milestone=None,
            url="http://example.com/pr1",
            issue_url=None,
            html_url=None,
            patch_url=None,
            diff_url=None
        ),
        # [1] - PR without Issue and with Release notes in description - with bug label
        PullRequest(
            id=2,
            number=102,
            title="PR2+2xRLS+0I+l-no",
            labels=[],
            body="Dummy body\n\nRelease notes:\n- PR 2 First release note\n- PR 2 Second release note\n",
            state="merged",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=None,
            merged_at=datetime.now(),
            milestone=None,
            url="http://example.com/pr2",
            issue_url=None,
            html_url=None,
            patch_url=None,
            diff_url=None
        ),
        # [2] - PR without Issue and without Release notes in description - with no labels - closed state
        PullRequest(
            id=3,
            number=103,
            title="PR3+0xRLS+0I+l-bug",
            labels=['error'],
            body="Dummy body",
            state="closed",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=datetime.now(),
            merged_at=None,
            milestone=None,
            url="http://example.com/pr3",
            issue_url=None,
            html_url=None,
            patch_url=None,
            diff_url=None
        ),
        # [3, 4] - 2 PRs with Issue '2' - no labels, both with Release notes
        PullRequest(
            id=5,
            number=105,
            title="PR5+2xRLS+1I+l-no",
            labels=[],
            body="Dummy body\ncloses #2\n\nRelease notes:\n- PR 5 release note\n",
            state="merged",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=None,
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
            title="PR6+1xRLS+1I+l-no",
            labels=['bug'],     # wrong label - should be ignored by logic
            body="Dummy body\nFixes #1\n\nRelease notes:\n- PR 6 release note\n",
            state="merged",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=None,
            merged_at=datetime.now(),
            milestone=None,
            url="http://example.com/pr6",
            issue_url=None,
            html_url=None,
            patch_url=None,
            diff_url=None
        ),
        # [5] - 1 PRs with Issue '11' - no labels, with Release notes - PR linked to Open Issue
        PullRequest(
            id=11,
            number=111,
            title="PR11+1xRLS+1I+l-no",
            labels=[],
            body="Dummy body\nFixes #10\n\nRelease notes:\n- PR 11 release note\n",
            state="merged",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=None,
            merged_at=datetime.now(),
            milestone=None,
            url="http://example.com/pr6",
            issue_url=None,
            html_url=None,
            patch_url=None,
            diff_url=None
        )
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

### Closed Issues without Pull Request (Release Notes) ⚠️
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
- #4 _I4+2PR+l-enhancement_ implemented by TODO
  - PR 5 release note
  - PR 6 release note

### Bugfixes 🛠
- #1 _I1+1PR+l-bug_ implemented by TODO
  - PR 1 First release note
  - PR 1 Second release note

### Closed Issues without Pull Request (Release Notes) ⚠️
- #7 _I7+0PR+l-enhancement_ implemented by TODO
- #8 _I8+0PR+l-spike_ implemented by TODO
- #9 _I9+0PR+l-any_ implemented by TODO

### Closed Issues without User Defined Labels ⚠️
- #8 _I8+0PR+l-spike_ implemented by TODO
- #9 _I9+0PR+l-any_ implemented by TODO

### Merged PRs without Issue and User Defined Labels ⚠️
- PR2+2xRLS+0I+l-no

### Closed PRs without Issue and User Defined Labels ⚠️
- PR3+0xRLS+0I+l-bug

### Merged PRs Linked to 'Not Closed' Issue ⚠️
- PR11+1xRLS+1I+l-no

### Others - No Topic ⚠️
Previous filters caught all Issues or Pull Requests.

#### Full Changelog
http://example.com/changelog
"""

release_notes_full_no_empty_chapters = """### New Features 🎉
- #4 _I4+2PR+l-enhancement_ implemented by TODO
  - PR 5 release note
  - PR 6 release note

### Bugfixes 🛠
- #1 _I1+1PR+l-bug_ implemented by TODO
  - PR 1 First release note
  - PR 1 Second release note

### Closed Issues without Pull Request (Release Notes) ⚠️
- #7 _I7+0PR+l-enhancement_ implemented by TODO
- #8 _I8+0PR+l-spike_ implemented by TODO
- #9 _I9+0PR+l-any_ implemented by TODO

### Closed Issues without User Defined Labels ⚠️
- #8 _I8+0PR+l-spike_ implemented by TODO
- #9 _I9+0PR+l-any_ implemented by TODO

### Merged PRs without Issue and User Defined Labels ⚠️
- PR2+2xRLS+0I+l-no

### Closed PRs without Issue and User Defined Labels ⚠️
- PR3+0xRLS+0I+l-bug

### Merged PRs Linked to 'Not Closed' Issue ⚠️
- PR11+1xRLS+1I+l-no

#### Full Changelog
http://example.com/changelog
"""

release_notes_full_no_warnings = """### Breaking Changes 💥
No entries detected.

### New Features 🎉
- #4 _I4+2PR+l-enhancement_ implemented by TODO
  - PR 5 release note
  - PR 6 release note

### Bugfixes 🛠
- #1 _I1+1PR+l-bug_ implemented by TODO
  - PR 1 First release note
  - PR 1 Second release note

#### Full Changelog
http://example.com/changelog
"""


# build

def test_build_full_with_empty_chapters():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(chapters_json)

    builder = ReleaseNotesBuilder(records=generate_full_dataset(), changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters)
    expected_release_notes = release_notes_full
    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


def test_build_no_data_with_empty_chapters():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(chapters_json)

    builder = ReleaseNotesBuilder(records={}, changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters)
    expected_release_notes = release_notes_no_data
    actual_release_notes = builder.build()
    print("Actual - no data:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


def test_build_no_warnings():
    custom_chapters = CustomChapters()
    custom_chapters.from_json(chapters_json)

    builder = ReleaseNotesBuilder(records=generate_full_dataset(), changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters, warnings=False)
    expected_release_notes = release_notes_full_no_warnings
    actual_release_notes = builder.build()
    print("Actual:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


def test_build_full_no_empty_chapters():
    custom_chapters_no_empty_chapters = CustomChapters()
    custom_chapters_no_empty_chapters.from_json(chapters_json)
    custom_chapters_no_empty_chapters.print_empty_chapters = False
    expected_release_notes = release_notes_full_no_empty_chapters

    builder = ReleaseNotesBuilder(records=generate_full_dataset(), changelog_url=changelog_url, formatter=formatter,
                                  custom_chapters=custom_chapters_no_empty_chapters, print_empty_chapters=False)

    actual_release_notes = builder.build()
    print("Actual:\n" + actual_release_notes)
    assert expected_release_notes == actual_release_notes


if __name__ == '__main__':
    pytest.main()
