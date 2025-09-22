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

"""
This module contains the ServiceChapters class which is responsible for representing the service chapters in the release
 notes.
"""
from typing import Optional, cast

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.chapters.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.model.record import Record
from release_notes_generator.utils.constants import (
    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
    MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
    OTHERS_NO_TOPIC,
    DIRECT_COMMITS,
)
from release_notes_generator.utils.enums import DuplicityScopeEnum


# pylint: disable=too-many-instance-attributes
class ServiceChapters(BaseChapters):
    """
    A class representing the Service Chapters in the release notes.
    """

    def __init__(
        self,
        sort_ascending: bool = True,
        print_empty_chapters: bool = True,
        user_defined_labels: Optional[list[str]] = None,
        used_record_numbers: Optional[list[int | str]] = None,
    ):
        super().__init__(sort_ascending, print_empty_chapters)

        self.user_defined_labels = user_defined_labels if user_defined_labels is not None else []
        self.sort_ascending = sort_ascending
        self.used_record_numbers: list[int | str] = used_record_numbers if used_record_numbers is not None else []

        self.chapters = {
            CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: Chapter(
                title=CLOSED_ISSUES_WITHOUT_PULL_REQUESTS, empty_message="All closed issues linked to a Pull Request."
            ),
            CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: Chapter(
                title=CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
                empty_message="All closed issues contain at least one of user defined labels.",
            ),
            MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: Chapter(
                title=MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
                empty_message="All merged PRs are linked to issues.",
            ),
            CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: Chapter(
                title=CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
                empty_message="All closed PRs are linked to issues.",
            ),
            MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES: Chapter(
                title=MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
                empty_message="All merged PRs are linked to Closed issues.",
            ),
            DIRECT_COMMITS: Chapter(
                title=DIRECT_COMMITS,
                empty_message="All direct commits are linked pull requests.",
            ),
            OTHERS_NO_TOPIC: Chapter(
                title=OTHERS_NO_TOPIC, empty_message="Previous filters caught all Issues or Pull Requests."
            ),
        }
        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_merged_pr_without_issue_and_labels = True
        self.show_chapter_closed_pr_without_issue_and_labels = True

        self.show_chapter_merged_prs_linked_to_open_issues = True

    def populate(self, records: dict[int | str, Record]) -> None:
        """
        Populates the service chapters with records.

        @param records: A dictionary of records.
        @return: None
        """
        # iterate all records
        for record_id, record in records.items():
            if record.skip:
                continue

            # skip the record when already used and not allowed to be duplicated in Service chapters
            if self.__is_row_present(record_id) and not self.duplicity_allowed():
                continue

            # main three situations:
            if record.is_closed and isinstance(record, IssueRecord):
                self.__populate_closed_issues(cast(IssueRecord, record), record_id)

            elif isinstance(record, PullRequestRecord):
                self.__populate_pr(cast(PullRequestRecord, record), record_id)

            elif isinstance(record, CommitRecord):
                self.__populate_direct_commit(cast(CommitRecord, record), record_id)

            # other edge case situations
            else:
                if (
                    record.is_open
                    and isinstance(record, IssueRecord)
                    and cast(IssueRecord, record).pull_requests_count() == 0
                ):
                    # no change increment delivered
                    pass
                elif (
                    record.is_open
                    and isinstance(record, IssueRecord)
                    and cast(IssueRecord, record).pull_requests_count() > 0
                ):
                    self.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(record_id, record.to_chapter_row())
                    self.used_record_numbers.append(record_id)
                else:
                    if record_id not in self.used_record_numbers:
                        self.chapters[OTHERS_NO_TOPIC].add_row(record_id, record.to_chapter_row())
                        self.used_record_numbers.append(record_id)

    def __populate_closed_issues(self, record: IssueRecord, record_id: int | str) -> None:
        """
        Populates the service chapters with closed issues.

        @param record: The Record object representing the closed issue.
        @param nr: The number of the record.
        @return: None
        """
        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_PULL_REQUESTS
        populated = False
        pulls_count = record.pull_requests_count()

        if pulls_count == 0:
            self.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].add_row(record_id, record.to_chapter_row())
            self.used_record_numbers.append(record_id)
            populated = True

        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS
        if not record.contains_min_one_label(self.user_defined_labels):
            # check if the record is already present among the chapters
            if self.__is_row_present(record_id) and not self.duplicity_allowed():
                return

            self.chapters[CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].add_row(record_id, record.to_chapter_row())
            self.used_record_numbers.append(record_id)
            populated = True

        if pulls_count > 0:
            # the record looks to be valid closed issue with 1+ pull requests, no reason to report it
            return

        if not populated:
            if self.__is_row_present(record_id) and not self.duplicity_allowed():
                return

            if record_id in self.used_record_numbers:
                return

            self.chapters[OTHERS_NO_TOPIC].add_row(record_id, record.to_chapter_row())
            self.used_record_numbers.append(record_id)

    def __populate_pr(self, record: PullRequestRecord, record_id: int | str) -> None:
        """
        Populates the service chapters with pull requests.

        @param record: The Record object representing the pull request.
        @param nr: The number of the record.
        @return: None
        """
        if record.is_merged:
            # check record properties if it fits to a chapter: MERGED_PRS_WITHOUT_ISSUE
            if not record.contains_issue_mentions() and not record.contains_min_one_label(self.user_defined_labels):
                if self.__is_row_present(record_id) and not self.duplicity_allowed():
                    return

                self.chapters[MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(
                    record_id, record.to_chapter_row()
                )
                self.used_record_numbers.append(record_id)

            # check record properties if it fits to a chapter: MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES
            if record.contains_issue_mentions():
                if self.__is_row_present(record_id) and not self.duplicity_allowed():
                    return

                self.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(record_id, record.to_chapter_row())
                self.used_record_numbers.append(record_id)

            if not record.is_present_in_chapters:
                if self.__is_row_present(record_id) and not self.duplicity_allowed():
                    return

                if record_id in self.used_record_numbers:
                    return

                self.chapters[OTHERS_NO_TOPIC].add_row(record_id, record.to_chapter_row())
                self.used_record_numbers.append(record_id)

        # check record properties if it fits to a chapter: CLOSED_PRS_WITHOUT_ISSUE
        elif (
            record.is_closed
            and not record.contains_issue_mentions()
            and not record.contains_min_one_label(self.user_defined_labels)
        ):
            if self.__is_row_present(record_id) and not self.duplicity_allowed():
                return

            self.chapters[CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(record_id, record.to_chapter_row())
            self.used_record_numbers.append(record_id)

        else:
            if self.__is_row_present(record_id) and not self.duplicity_allowed():
                return

            if record_id in self.used_record_numbers:
                return

            # not record.is_present_in_chapters:
            self.chapters[OTHERS_NO_TOPIC].add_row(record_id, record.to_chapter_row())
            self.used_record_numbers.append(record_id)

    def __populate_direct_commit(self, record: CommitRecord, record_id: int | str) -> None:
        """
        Populates the service chapters with direct commits.

        @param record: The CommitRecord object representing the direct commit.
        @return: None
        """
        self.chapters[DIRECT_COMMITS].add_row(record_id, record.to_chapter_row())
        self.used_record_numbers.append(record_id)

    def __is_row_present(self, record_id: int | str) -> bool:
        """
        Checks if the row is already present in the chapters.

        @param nr: The number of the record.
        @return: True if the row is present, False otherwise.
        """
        return record_id in self.used_record_numbers

    @staticmethod
    def duplicity_allowed() -> bool:
        """
        Checks if duplicity is allowed in the service chapters.

        @return: True if duplicity is allowed, False otherwise.
        """
        return ActionInputs.get_duplicity_scope() in (DuplicityScopeEnum.SERVICE, DuplicityScopeEnum.BOTH)
