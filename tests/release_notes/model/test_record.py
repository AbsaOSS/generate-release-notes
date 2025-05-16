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

import logging

from github.Commit import Commit

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import ISSUE_STATE_CLOSED, PR_STATE_CLOSED


# cover property methods - simple ones
def test_record_properties_with_issue_open(mock_issue_open, record_with_issue_open_no_pull):
    assert mock_issue_open == record_with_issue_open_no_pull.issue
    assert record_with_issue_open_no_pull.is_issue
    assert not record_with_issue_open_no_pull.is_pr
    assert record_with_issue_open_no_pull.is_open_issue
    mock_issue_open.state = ISSUE_STATE_CLOSED
    assert record_with_issue_open_no_pull.is_closed_issue
    assert record_with_issue_open_no_pull.is_closed
    assert not record_with_issue_open_no_pull.is_merged_pr
    assert ["label1", "label2"] == record_with_issue_open_no_pull.labels
    assert 0 == record_with_issue_open_no_pull.pulls_count
    assert record_with_issue_open_no_pull.pr_links is None
    assert record_with_issue_open_no_pull.pull_request() is None
    assert 122 == record_with_issue_open_no_pull.number


def test_record_properties_with_pull(mock_pull_closed, record_with_no_issue_one_pull_closed, mocker):
    assert [mock_pull_closed] == record_with_no_issue_one_pull_closed.pulls
    assert not record_with_no_issue_one_pull_closed.is_present_in_chapters
    record_with_no_issue_one_pull_closed.increment_present_in_chapters()
    assert record_with_no_issue_one_pull_closed.is_present_in_chapters
    assert record_with_no_issue_one_pull_closed.is_pr
    assert not record_with_no_issue_one_pull_closed.is_issue
    mock_pull_closed.state = PR_STATE_CLOSED
    assert record_with_no_issue_one_pull_closed.is_closed
    mock_pull_closed.merged_at = mocker.Mock()
    mock_pull_closed.closed_at = mocker.Mock()
    assert record_with_no_issue_one_pull_closed.is_merged_pr
    assert ["label1"] == record_with_no_issue_one_pull_closed.labels
    assert record_with_no_issue_one_pull_closed.pull_request(index=5) is None
    assert mock_pull_closed == record_with_no_issue_one_pull_closed.pull_request()
    assert 123 == record_with_no_issue_one_pull_closed.number


# authors & contributors - not supported now by code
def test_record_properties_authors_contributors(record_with_no_issue_one_pull_closed):
    assert record_with_no_issue_one_pull_closed.authors is None
    assert record_with_no_issue_one_pull_closed.contributors is None


# get_rls_notes


def test_get_rls_notes_multi_level(record_with_no_issue_one_pull_closed):
    record_with_no_issue_one_pull_closed.pull_request(0).body = """Release Notes:

- Fixed bug
  - Which was awful

- Improved performance
  + Now it runs like a cheetah - really!

+ More nice code
  * Awesome architecture

## Another chapter
You should not see this chapter as part of the collected RLS notes.

## Summary by CodeRabbit

- **Group1**
  - Fixed bug
    """
    expected_notes = "  - Fixed bug\n    - Which was awful\n  - Improved performance\n    + Now it runs like a cheetah - really!\n  + More nice code\n    * Awesome architecture"
    assert record_with_no_issue_one_pull_closed.get_rls_notes() == expected_notes


def test_get_rls_notes_mixed_line_marks(record_with_no_issue_one_pull_closed):
    expected_notes = "  - Fixed bug\n  - Improved performance\n  + More nice code\n    * Awesome architecture"
    assert record_with_no_issue_one_pull_closed.get_rls_notes() == expected_notes


def test_get_rls_notes_not_detected(record_with_no_issue_one_pull_closed, mocker):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_release_notes_title", return_value="XXX")
    assert '' == record_with_no_issue_one_pull_closed.get_rls_notes()


def test_get_rls_notes_multi_level_coderabbit(record_with_no_issue_one_pull_closed, mocker):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_coderabbit_support_active", return_value="true")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_coderabbit_summary_ignore_groups", return_value=["Group2"])
    record_with_no_issue_one_pull_closed.pull_request(0).body = """## Another chapter
You should not see this chapter as part of the collected RLS notes.

## Summary by CodeRabbit

- **Group1**
  - Fixed bug
  
- **Group2**
  - Improved performance
  
## Another chapter

With another test section.
    """
    expected_notes = "  - Fixed bug"
    assert record_with_no_issue_one_pull_closed.get_rls_notes() == expected_notes


# contains_release_notes


def test_contains_release_notes_success(record_with_no_issue_one_pull_closed):
    assert record_with_no_issue_one_pull_closed.contains_release_notes


def test_contains_release_notes_fail(record_with_no_issue_one_pull_closed_no_rls_notes):
    assert not record_with_no_issue_one_pull_closed_no_rls_notes.contains_release_notes


# pr_contains_issue_mentions


def test_pr_contains_issue_mentions(record_with_no_issue_one_pull_closed, mocker):
    mock_extract_issue_numbers_from_body = mocker.patch(
        "release_notes_generator.model.record.extract_issue_numbers_from_body"
    )
    mock_extract_issue_numbers_from_body.return_value = [123]
    assert record_with_no_issue_one_pull_closed.pr_contains_issue_mentions

    mock_extract_issue_numbers_from_body.return_value = []
    assert not record_with_no_issue_one_pull_closed.pr_contains_issue_mentions


# pr_links


def test_pr_links(record_with_no_issue_one_pull_closed):
    expected_links = "#123"
    assert record_with_no_issue_one_pull_closed.pr_links == expected_links


# pull_request_commit_count


def test_pull_request_commit_count_pr_number_not_exist(record_with_no_issue_one_pull_closed):
    assert 0 == record_with_no_issue_one_pull_closed.pull_request_commit_count(pull_number=10)


def test_pull_request_commit_count(record_with_no_issue_one_pull_closed):
    assert 1 == record_with_no_issue_one_pull_closed.pull_request_commit_count(pull_number=123)


# register_commit


def test_register_commit_success(record_with_no_issue_one_pull_closed, mocker):
    commit = mocker.Mock(spec=Commit)
    commit.sha = "merge_commit_sha"
    record_with_no_issue_one_pull_closed.register_commit(commit)
    assert commit in record_with_no_issue_one_pull_closed.commits[123]


def test_register_commit_failure(record_with_no_issue_one_pull_closed, caplog, mocker):
    commit = mocker.Mock(spec=Commit)
    commit.sha = "unknown_sha"
    with caplog.at_level(logging.ERROR):
        record_with_no_issue_one_pull_closed.register_commit(commit)
        assert f"Commit {commit.sha} not registered in any PR of record 123" in caplog.text


# to_chapter_row


def test_to_chapter_row_with_pull(record_with_no_issue_one_pull_closed):
    expected_row = (
        "PR: #123 _Fixed bug_\n  - Fixed bug\n  - Improved performance\n  + More nice code\n    * Awesome architecture"
    )
    assert expected_row == record_with_no_issue_one_pull_closed.to_chapter_row()


def test_to_chapter_row_with_pull_no_pr_prefix(record_with_no_issue_one_pull_closed, mocker):
    mocker.patch("release_notes_generator.builder.ActionInputs.get_row_format_link_pr", return_value=False)
    expected_row = (
        "#123 _Fixed bug_\n  - Fixed bug\n  - Improved performance\n  + More nice code\n    * Awesome architecture"
    )
    assert expected_row == record_with_no_issue_one_pull_closed.to_chapter_row()


def test_to_chapter_row_with_issue(record_with_issue_closed_one_pull):
    expected_row = """#121 _Fix the bug_ in #123
  - Fixed bug
  - Improved performance
  + More nice code
    * Awesome architecture"""
    assert expected_row == record_with_issue_closed_one_pull.to_chapter_row()


def test_to_chapter_row_with_pull_no_rls_notes(record_with_no_issue_one_pull_closed_no_rls_notes):
    expected_row = "PR: #123 _Fixed bug_"
    assert expected_row == record_with_no_issue_one_pull_closed_no_rls_notes.to_chapter_row()


def test_to_chapter_row_with_issue_no_rls_notes(record_with_issue_closed_one_pull_no_rls_notes):
    expected_row = "#121 _Fix the bug_ in #123"
    assert expected_row == record_with_issue_closed_one_pull_no_rls_notes.to_chapter_row()


# contains_labels


def test_contains_labels_with_issue(record_with_issue_open_no_pull):
    # Test with labels present in the issue
    assert record_with_issue_open_no_pull.contains_min_one_label(["label1"])
    assert record_with_issue_open_no_pull.contains_min_one_label(["label2"])
    assert record_with_issue_open_no_pull.contains_min_one_label(["label1", "label2"])
    assert record_with_issue_open_no_pull.contain_all_labels(["label1", "label2"])

    # Test with labels not present in the issue
    assert not record_with_issue_open_no_pull.contains_min_one_label(["label3"])
    assert record_with_issue_open_no_pull.contains_min_one_label(["label1", "label3"])
    assert not record_with_issue_open_no_pull.contain_all_labels(["label1", "label3"])


def test_contains_labels_with_pull(record_with_no_issue_one_pull_closed):
    # Test with labels present in the pull request
    assert record_with_no_issue_one_pull_closed.contains_min_one_label(["label1"])

    # Test with labels not present in the pull request
    assert not record_with_no_issue_one_pull_closed.contains_min_one_label(["label2"])
    assert record_with_no_issue_one_pull_closed.contains_min_one_label(["label1", "label2"])
    assert not record_with_no_issue_one_pull_closed.contain_all_labels(["label1", "label2"])


# present_in_chapters


def test_present_in_chapters_initial(record_with_no_issue_one_pull_closed):
    # Test initial value
    assert record_with_no_issue_one_pull_closed.present_in_chapters() == 0


def test_present_in_chapters_increment(record_with_no_issue_one_pull_closed):
    # Test after increment
    record_with_no_issue_one_pull_closed.increment_present_in_chapters()
    assert record_with_no_issue_one_pull_closed.present_in_chapters() == 1
    record_with_no_issue_one_pull_closed.increment_present_in_chapters()
    assert record_with_no_issue_one_pull_closed.present_in_chapters() == 2


# is_commit_sha_present


def test_is_commit_sha_present_true(record_with_no_issue_one_pull_closed):
    # Test with a commit SHA that is present
    assert record_with_no_issue_one_pull_closed.is_commit_sha_present("merge_commit_sha")


def test_is_commit_sha_present_false(record_with_no_issue_one_pull_closed):
    # Test with a commit SHA that is not present
    assert not record_with_no_issue_one_pull_closed.is_commit_sha_present("unknown_sha")
