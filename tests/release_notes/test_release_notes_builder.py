import pytest
import json

from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.release_notes_builder import ReleaseNotesBuilder


@pytest.fixture
def issues():
    return [
        Issue(id=1, title='Issue 1', labels=['enhancement'], is_closed=True, linked_pr_id=None),
        Issue(id=3, title='Issue 3', labels=['enhancement'], is_closed=True, linked_pr_id=None),
        Issue(id=5, title='Issue 5', labels=['bug'], is_closed=True, linked_pr_id=None),     # Issue without linked PR
        Issue(id=5, title='Issue 8', labels=[], is_closed=True, linked_pr_id=None),          # Issue without linked PR & without label
    ]


@pytest.fixture
def pulls():
    return [
        PullRequest(id=2, title='PR 1', labels=['enhancement'], linked_issue_id=1),
        PullRequest(id=4, title='PR 2', labels=[],linked_issue_id=3),
        PullRequest(id=6, title='PR 3', labels=['bug'],linked_issue_id=None),        # PR without linked Issue
    ]


@pytest.fixture
def chapters_json():
    return json.dumps([
        {"title": "Breaking Changes 💥", "label": "breaking-change"},
        {"title": "New Features 🎉", "label": "enhancement"},
        {"title": "New Features 🎉", "label": "feature"},
        {"title": "Bugfixes 🛠", "label": "bug"}
    ])


@pytest.fixture
def builder(issues, pulls, chapters_json):
    return ReleaseNotesBuilder(issues, pulls, "http://changelog.url", chapters_json, warnings=True,
                               print_empty_chapters=True)


def builder_print_empty_chapters_false(issues, pulls, chapters_json):
    return ReleaseNotesBuilder(issues, pulls, "http://changelog.url", chapters_json, warnings=True,
                               print_empty_chapters=False)


user_chapters = """
Breaking Changes 💥
No entries for this chapter.
    
New Features 🎉
- Issue 1 (#1)
- Issue 3 (#3)
    
Bugfixes
- Issue 5 (#5)
- PR 3 (#6)

"""


user_chapters_no_empty_chapters = """
New Features 🎉
- Issue 1 (#1)
- Issue 3 (#3)
    
Bugfixes
- Issue 5 (#5)
- PR 3 (#6)

"""


release_notes_full = """### Bugs
- Issue 1 (#1)


### Enhancements
- Issue 2 (#2)


### No Entries
No entries for this chapter.


### Closed Issues without Pull Request ⚠️
- Issue 1 (#1)
- Issue 2 (#2)
- Issue 3 (#3)


### Closed Issues without User Defined Labels ⚠️
- Issue 3 (#3)


### Closed Issues without Release Notes ⚠️
- Issue 1 (#1)


### Merged PRs without Linked Issue and Custom Labels ⚠️
All merged PRs are linked to issues.


### Merged PRs Linked to Open Issue ⚠️
All merged PRs are linked to Closed issues.


### Closed PRs without Linked Issue and Custom Labels ⚠️
All closed PRs are linked to issues.


#### Full Changelog
http://changelog.url
"""


# build

# TODO - un-comment when smaller methods will be developed - add high level format tests with it
# def test_build(builder):
#     expected_release_notes = release_notes_full
#     actual_release_notes = builder.build()
#     assert expected_release_notes == actual_release_notes


# get_user_defined_chapters

# def test_get_user_defined_chapters(builder):
#     expected_chapters = user_chapters
#
#     actual_chapters = builder._get_user_defined_chapters()
#
#     assert expected_chapters == actual_chapters


# def test_get_user_defined_chapters_not_print_empty_chapters(builder_print_empty_chapters_false):
#     expected_chapters = user_chapters_no_empty_chapters
#
#     actual_chapters = builder_print_empty_chapters_false._get_user_defined_chapters()
#
#     assert expected_chapters == actual_chapters






if __name__ == '__main__':
    pytest.main()
