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

from release_notes_generator.model.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.record import Record


# pylint: disable=too-many-instance-attributes
class ServiceChapters(BaseChapters):
    """
    A class used to represent the service chapters in the release notes.
    """

    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: str = "Closed Issues without Pull Request ⚠️"
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: str = "Closed Issues without User Defined Labels ⚠️"

    MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Merged PRs without Issue and User Defined Labels ⚠️"
    CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Closed PRs without Issue and User Defined Labels ⚠️"

    MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES: str = "Merged PRs Linked to 'Not Closed' Issue ⚠️"

    OTHERS_NO_TOPIC: str = "Others - No Topic ⚠️"

    def __init__(self, sort_ascending: bool = True, print_empty_chapters: bool = True,
                 user_defined_labels: list[str] = None, used_record_numbers: list[int] = None):
        """
        Constructs all the necessary attributes for the ServiceChapters object.

        :param sort_ascending: A boolean indicating whether to sort the chapters in ascending order.
        :param print_empty_chapters: A boolean indicating whether to print empty chapters.
        :param user_defined_labels: A list of user-defined labels.
        """

        super().__init__(sort_ascending, print_empty_chapters)

        self.user_defined_labels = user_defined_labels if user_defined_labels is not None else []
        self.sort_ascending = sort_ascending

        if used_record_numbers is None:
            self.used_record_numbers = []
        else:
            self.used_record_numbers = used_record_numbers

        self.chapters = {
            self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: Chapter(
                title=self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
                empty_message="All closed issues linked to a Pull Request."
            ),
            self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: Chapter(
                title=self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
                empty_message="All closed issues contain at least one of user defined labels."
            ),
            self.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: Chapter(
                title=self.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
                empty_message="All merged PRs are linked to issues."
            ),
            self.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: Chapter(
                title=self.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
                empty_message="All closed PRs are linked to issues."
            ),
            self.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES: Chapter(
                title=self.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
                empty_message="All merged PRs are linked to Closed issues."
            ),
            self.OTHERS_NO_TOPIC: Chapter(
                title=self.OTHERS_NO_TOPIC,
                empty_message="Previous filters caught all Issues or Pull Requests."
            )
        }
        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_merged_pr_without_issue_and_labels = True
        self.show_chapter_closed_pr_without_issue_and_labels = True

        self.show_chapter_merged_prs_linked_to_open_issues = True

    def populate(self, records: dict[int, Record]):
        """
        Populates the service chapters with records.

        :param records: A dictionary of records where the key is an integer and the value is a Record object.
        """
        for nr in records:
            if nr in self.used_record_numbers:
                # TODO - duplicities not allowed in this version in default
                continue

            # iterate all records
            if records[nr].is_closed_issue:
                self.__populate_closed_issues(records[nr], nr)

            elif records[nr].is_pr:
                self.__populate_pr(records[nr], nr)

            else:
                if records[nr].is_open_issue and records[nr].pulls_count == 0:
                    pass
                elif records[nr].is_open_issue and records[nr].pulls_count > 0:
                    self.chapters[self.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(nr, records[nr].to_chapter_row())
                else:
                    self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, records[nr].to_chapter_row())

    def __populate_closed_issues(self, record: Record, nr: int):
        """
        Populates the service chapters with closed issues.

        :param record: The Record object representing the closed issue.
        :param nr: The number of the record.
        """
        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_PULL_REQUESTS
        populated = False
        if record.pulls_count == 0:
            self.chapters[self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].add_row(nr, record.to_chapter_row())
            populated = True

        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS
        if not record.contains_min_one_label(self.user_defined_labels):
            self.chapters[self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())
            populated = True

        if not populated:
            self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())

    def __populate_pr(self, record: Record, nr: int):
        """
        Populates the service chapters with pull requests.

        :param record: The Record object representing the pull request.
        :param nr: The number of the record.
        """
        if record.is_merged_pr:
            # check record properties if it fits to a chapter: MERGED_PRS_WITHOUT_ISSUE
            if not record.pr_contains_issue_mentions and not record.contains_min_one_label(self.user_defined_labels):
                self.chapters[self.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(nr,
                                                                                             record.to_chapter_row())

            # check record properties if it fits to a chapter: MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES
            if record.pr_contains_issue_mentions:
                self.chapters[self.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(nr, record.to_chapter_row())

            if not record.is_present_in_chapters:
                self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())

        # check record properties if it fits to a chapter: CLOSED_PRS_WITHOUT_ISSUE
        elif record.is_closed and not record.pr_contains_issue_mentions and not record.contains_min_one_label(
                self.user_defined_labels):
            self.chapters[self.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())

        else:
            # not record.is_present_in_chapters:
            self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())
