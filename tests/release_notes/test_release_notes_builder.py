import pytest
import json

from src.github_integration.model.issue import Issue
from src.github_integration.model.pull_request import PullRequest
from src.release_notes.release_notes_builder import ReleaseNotesBuilder


@pytest.fixture
def issues():
    return [
        Issue(id=1, title='Issue 1', labels=['bug'], is_closed=True, linked_pr_id=None),
        Issue(id=2, title='Issue 2', labels=['enhancement'], is_closed=True, linked_pr_id=None),
        Issue(id=3, title='Issue 3', labels=[], is_closed=True, linked_pr_id=None),
    ]


@pytest.fixture
def pulls():
    return [
        PullRequest(id=1, title='PR 1', linked_issue_id=None),
        PullRequest(id=2, title='PR 2', linked_issue_id=1),
    ]


@pytest.fixture
def chapters_json():
    return json.dumps([
        {"title": "Bugs", "label": "bug"},
        {"title": "Enhancements", "label": "enhancement"},
        {"title": "No Entries", "label": "no_entries"},
    ])


@pytest.fixture
def builder(issues, pulls, chapters_json):
    return ReleaseNotesBuilder(issues, pulls, "http://changelog.url", chapters_json, warnings=True,
                               print_empty_chapters=True)


def builder_print_empty_chapters_false(issues, pulls, chapters_json):
    return ReleaseNotesBuilder(issues, pulls, "http://changelog.url", chapters_json, warnings=True,
                               print_empty_chapters=False)


user_chapters = """
Bugs
- Issue 1 (#1)
    
Enhancements
- Issue 2 (#2)
    
No Entries
No entries for this chapter.

"""


user_chapters_no_empty_chapters = """
Bugs
- Issue 1 (#1)
    
Enhancements
- Issue 2 (#2)
    
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

def test_build(builder):
    expected_release_notes = release_notes_full
    actual_release_notes = builder.build()
    assert expected_release_notes == actual_release_notes


# get_user_defined_chapters

# def test_get_user_defined_chapters(builder):
#     expected_release_notes = release_notes_full
#
#     actual_release_notes = builder._get_user_defined_chapters()
#
#     assert expected_release_notes == actual_release_notes


# def test_get_user_defined_chapters_not_print_empty_chapters(builder_print_empty_chapters_false):
#     expected_release_notes = release_notes_no_empty_chapters
#
#     actual_release_notes = builder_print_empty_chapters_false._get_user_defined_chapters()
#
#     assert expected_release_notes == actual_release_notes






if __name__ == '__main__':
    pytest.main()
