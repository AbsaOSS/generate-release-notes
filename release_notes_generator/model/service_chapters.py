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
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.record import Record
from release_notes_generator.utils.constants import (
    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
    MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
    OTHERS_NO_TOPIC,
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
        user_defined_labels: list[str] = None,
        used_record_numbers: list[int] = None,
    ):
        super().__init__(sort_ascending, print_empty_chapters)

        self.user_defined_labels = user_defined_labels if user_defined_labels is not None else []
        self.sort_ascending = sort_ascending

        if used_record_numbers is None:
            self.used_record_numbers: list[int] = []
        else:
            self.used_record_numbers: list[int] = used_record_numbers

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
            OTHERS_NO_TOPIC: Chapter(
                title=OTHERS_NO_TOPIC, empty_message="Previous filters caught all Issues or Pull Requests."
            ),
        }
        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_merged_pr_without_issue_and_labels = True
        self.show_chapter_closed_pr_without_issue_and_labels = True

        self.show_chapter_merged_prs_linked_to_open_issues = True

    def populate(self, records: dict[int, Record]) -> None:
        """
        Populates the service chapters with records.

        @param records: A dictionary of records.
        @return: None
        """
        # iterate all records
        for nr in records:
            if records[nr].skip:
                continue

            # skip the record when used in used and not allowed to be duplicated in Service chapters
            if self.__is_row_present(nr) and not self.duplicity_allowed():
                continue

            if records[nr].is_closed_issue:
                self.__populate_closed_issues(records[nr], nr)

            elif records[nr].is_pr:
                self.__populate_pr(records[nr], nr)

            else:
                if records[nr].is_open_issue and records[nr].pulls_count == 0:
                    pass
                elif records[nr].is_open_issue and records[nr].pulls_count > 0:
                    self.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(nr, records[nr].to_chapter_row())
                    self.used_record_numbers.append(nr)
                else:
                    self.chapters[OTHERS_NO_TOPIC].add_row(nr, records[nr].to_chapter_row())
                    self.used_record_numbers.append(nr)

    def __populate_closed_issues(self, record: Record, nr: int) -> None:
        """
        Populates the service chapters with closed issues.

        @param record: The Record object representing the closed issue.
        @param nr: The number of the record.
        @return: None
        """
        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_PULL_REQUESTS
        populated = False
        if record.pulls_count == 0:
            self.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].add_row(nr, record.to_chapter_row())
            self.used_record_numbers.append(nr)
            populated = True

        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS
        if not record.contains_min_one_label(self.user_defined_labels):
            # check if the record is already present among the chapters
            if self.__is_row_present(nr) and not self.duplicity_allowed():
                return

            self.chapters[CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())
            self.used_record_numbers.append(nr)
            populated = True

        if record.pulls_count > 0:
            # the record looks to be valid closed issue with 1+ pull requests
            return

        if not populated:
            if self.__is_row_present(nr) and not self.duplicity_allowed():
                return

            self.chapters[OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())
            self.used_record_numbers.append(nr)

    def __populate_pr(self, record: Record, nr: int) -> None:
        """
        Populates the service chapters with pull requests.

        @param record: The Record object representing the pull request.
        @param nr: The number of the record.
        @return: None
        """
        if record.is_merged_pr:
            # check record properties if it fits to a chapter: MERGED_PRS_WITHOUT_ISSUE
            if not record.pr_contains_issue_mentions and not record.contains_min_one_label(self.user_defined_labels):
                if self.__is_row_present(nr) and not self.duplicity_allowed():
                    return

                self.chapters[MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())
                self.used_record_numbers.append(nr)

            # check record properties if it fits to a chapter: MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES
            if record.pr_contains_issue_mentions:
                if self.__is_row_present(nr) and not self.duplicity_allowed():
                    return

                self.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(nr, record.to_chapter_row())
                self.used_record_numbers.append(nr)

            if not record.is_present_in_chapters:
                if self.__is_row_present(nr) and not self.duplicity_allowed():
                    return

                self.chapters[OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())
                self.used_record_numbers.append(nr)

        # check record properties if it fits to a chapter: CLOSED_PRS_WITHOUT_ISSUE
        elif (
            record.is_closed
            and not record.pr_contains_issue_mentions
            and not record.contains_min_one_label(self.user_defined_labels)
        ):
            if self.__is_row_present(nr) and not self.duplicity_allowed():
                return

            self.chapters[CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())
            self.used_record_numbers.append(nr)

        else:
            if self.__is_row_present(nr) and not self.duplicity_allowed():
                return

            # not record.is_present_in_chapters:
            self.chapters[OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())
            self.used_record_numbers.append(nr)

    def __is_row_present(self, nr: int) -> bool:
        """
        Checks if the row is already present in the chapters.

        @param nr: The number of the record.
        @return: True if the row is present, False otherwise.
        """
        return nr in self.used_record_numbers

    @staticmethod
    def duplicity_allowed() -> bool:
        """
        Checks if duplicity is allowed in the service chapters.

        @return: True if duplicity is allowed, False otherwise.
        """
        return ActionInputs.get_duplicity_scope() in (DuplicityScopeEnum.SERVICE, DuplicityScopeEnum.BOTH)
