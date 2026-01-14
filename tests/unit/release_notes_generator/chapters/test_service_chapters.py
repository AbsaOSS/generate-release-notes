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

from release_notes_generator.model.chapter import Chapter
from release_notes_generator.chapters.service_chapters import ServiceChapters
from release_notes_generator.utils.constants import (
    MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
    MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    OTHERS_NO_TOPIC,
)
from release_notes_generator.utils.enums import DuplicityScopeEnum


# __init__


def test_initialization(service_chapters):
    assert service_chapters.sort_ascending is True
    assert service_chapters.print_empty_chapters is True
    assert service_chapters.user_defined_labels == ["bug", "enhancement"]
    assert isinstance(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS], Chapter)


# populate


def test_populate_closed_issue(service_chapters, record_with_issue_closed_no_pull):
    service_chapters.populate({1: record_with_issue_closed_no_pull})

    assert 1 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 1 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)


def test_populate_merged_pr(service_chapters, pull_request_record_merged):
    service_chapters.populate({123: pull_request_record_merged})

    assert 1 == len(service_chapters.chapters[MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)


def test_populate_closed_pr(service_chapters, pull_request_record_closed):
    service_chapters.populate({2: pull_request_record_closed})

    assert 1 == len(service_chapters.chapters[CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)


def test_populate_not_closed_issue(service_chapters, record_with_issue_open_one_pull_closed):
    service_chapters.populate({1: record_with_issue_open_one_pull_closed})
    print(service_chapters.to_string())

    assert 1 == len(service_chapters.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)


def test_populate_not_closed_issue_without_pull(service_chapters, record_with_issue_open_no_pull):
    service_chapters.populate({1: record_with_issue_open_no_pull})
    print(service_chapters.to_string())

    assert 0 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 0 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)
    assert 0 == len(service_chapters.chapters[OTHERS_NO_TOPIC].rows)


def test_populate_no_issue_with_pull(service_chapters, issue_request_record_with_merged_pr_with_issue_mentioned):
    service_chapters.populate({1: issue_request_record_with_merged_pr_with_issue_mentioned})
    print(service_chapters.to_string())

    assert 1 == len(service_chapters.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)


def test_populate_closed_issue_scope_custom(service_chapters, record_with_issue_closed_no_pull, mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.ActionInputs.get_duplicity_scope", return_value=DuplicityScopeEnum.CUSTOM
    )

    service_chapters.populate({1: record_with_issue_closed_no_pull})

    assert 1 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 0 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)


def test_populate_closed_issue_duplicity(service_chapters, record_with_issue_closed_no_pull, mocker):
    mocker.patch(
        "release_notes_generator.action_inputs.ActionInputs.get_duplicity_scope", return_value=DuplicityScopeEnum.NONE
    )

    service_chapters.used_record_numbers.append(1)
    service_chapters.populate({1: record_with_issue_closed_no_pull})

    assert 0 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 0 == len(service_chapters.chapters[CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)


# to_string with hidden chapters


def test_to_string_with_no_hidden_chapters(service_chapters, record_with_issue_closed_no_pull):
    service_chapters.populate({1: record_with_issue_closed_no_pull})
    result = service_chapters.to_string()

    assert CLOSED_ISSUES_WITHOUT_PULL_REQUESTS in result
    assert CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS in result


def test_to_string_with_single_hidden_chapter(record_with_issue_closed_no_pull):
    service_chapters = ServiceChapters(
        sort_ascending=True,
        print_empty_chapters=True,
        user_defined_labels=["bug", "enhancement"],
        hidden_chapters=[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS],
    )
    service_chapters.populate({1: record_with_issue_closed_no_pull})
    result = service_chapters.to_string()

    assert CLOSED_ISSUES_WITHOUT_PULL_REQUESTS not in result
    assert CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS in result


def test_to_string_with_multiple_hidden_chapters(record_with_issue_closed_no_pull):
    service_chapters = ServiceChapters(
        sort_ascending=True,
        print_empty_chapters=True,
        user_defined_labels=["bug", "enhancement"],
        hidden_chapters=[
            CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
            CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
        ],
    )
    service_chapters.populate({1: record_with_issue_closed_no_pull})
    result = service_chapters.to_string()

    assert CLOSED_ISSUES_WITHOUT_PULL_REQUESTS not in result
    assert CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS not in result
    # Other empty chapters should still be shown since print_empty_chapters=True
    assert MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS in result


def test_to_string_with_hidden_chapter_not_in_results(pull_request_record_merged):
    service_chapters = ServiceChapters(
        sort_ascending=True,
        print_empty_chapters=True,
        user_defined_labels=["bug", "enhancement"],
        hidden_chapters=[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS],  # This chapter won't be populated
    )
    service_chapters.populate({123: pull_request_record_merged})
    result = service_chapters.to_string()

    # CLOSED_ISSUES_WITHOUT_PULL_REQUESTS shouldn't appear anyway (not populated)
    assert CLOSED_ISSUES_WITHOUT_PULL_REQUESTS not in result
    # MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS should appear
    assert MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS in result
