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

import logging
from typing import Optional, cast

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.chapters.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.record.commit_record import CommitRecord
from release_notes_generator.model.record.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.pull_request_record import PullRequestRecord
from release_notes_generator.model.record.record import Record
from release_notes_generator.model.record.sub_issue_record import SubIssueRecord
from release_notes_generator.utils.constants import (
    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
    MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
    MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
    OTHERS_NO_TOPIC,
    DIRECT_COMMITS,
    DEFAULT_SERVICE_CHAPTER_ORDER,
    GLOBAL_EXCLUDE_KEY,
)
from release_notes_generator.utils.enums import DuplicityScopeEnum

logger = logging.getLogger(__name__)


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
        hidden_chapters: Optional[list[str]] = None,
        chapter_order: Optional[list[str]] = None,
        chapter_exclude: Optional[dict[str, list[list[str]]]] = None,
    ):
        super().__init__(sort_ascending, print_empty_chapters)

        self.user_defined_labels = user_defined_labels if user_defined_labels is not None else []
        self.sort_ascending = sort_ascending
        self.used_record_numbers: list[int | str] = used_record_numbers if used_record_numbers is not None else []
        self.hidden_chapters: list[str] = hidden_chapters if hidden_chapters is not None else []

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

        # Define the order in which service chapters should appear in the output
        self.chapter_order = chapter_order if chapter_order is not None else list(DEFAULT_SERVICE_CHAPTER_ORDER)

        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_merged_pr_without_issue_and_labels = True
        self.show_chapter_closed_pr_without_issue_and_labels = True

        self.show_chapter_merged_prs_linked_to_open_issues = True

        chapter_exclude = chapter_exclude if chapter_exclude is not None else {}
        self._global_exclude_groups: list[list[str]] = chapter_exclude.get(GLOBAL_EXCLUDE_KEY, [])
        self._per_chapter_exclude_groups: dict[str, list[list[str]]] = {
            k: v for k, v in chapter_exclude.items() if k != GLOBAL_EXCLUDE_KEY
        }

    def populate(self, records: dict[str, Record]) -> None:
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

            # global exclusion: if any "*" group is a subset of the record labels, drop entirely
            if self._is_globally_excluded(record):
                logger.debug("Record %s globally excluded by '*' rule.", record_id)
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
                pr_count = cast(IssueRecord, record).pull_requests_count()
                is_issue_like = isinstance(record, (IssueRecord, SubIssueRecord))
                is_hierarchy = isinstance(record, HierarchyIssueRecord)

                if record.is_open:
                    if is_hierarchy and record.is_present_in_chapters:
                        logger.debug("Skipping open HierarchyIssueRecord %s (pr_count=%d)", record_id, pr_count)
                    elif is_issue_like and pr_count > 0:
                        # Open issue/sub-issue with linked PRs → add to the specific chapter
                        if not self._is_excluded_from_chapter(record, MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES):
                            record.add_to_chapter_presence(MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES)
                            self.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(
                                record_id, record.to_chapter_row()
                            )
                            logger.debug("Linked PRs for open issue %s; added to chapter.", record_id)
                            self.used_record_numbers.append(record_id)
                    else:
                        # Open issue/sub-issue with no PRs → explicitly do nothing (keeps original behavior)
                        pass
                else:
                    if record_id not in self.used_record_numbers:
                        if not self._is_excluded_from_chapter(record, OTHERS_NO_TOPIC):
                            record.add_to_chapter_presence(OTHERS_NO_TOPIC)
                            self.chapters[OTHERS_NO_TOPIC].add_row(record_id, record.to_chapter_row())
                            self.used_record_numbers.append(record_id)

    def __populate_closed_issues(self, record: IssueRecord, record_id: int | str) -> None:
        """
        Populates the service chapters with closed issues.

        Parameters:
            record: The record to populate.
            record_id: The ID of the record.

        Returns:
            None
        """
        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_PULL_REQUESTS
        populated = False
        pulls_count = record.pull_requests_count()

        if pulls_count == 0:
            if not self._is_excluded_from_chapter(record, CLOSED_ISSUES_WITHOUT_PULL_REQUESTS):
                record.add_to_chapter_presence(CLOSED_ISSUES_WITHOUT_PULL_REQUESTS)
                self.chapters[CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].add_row(record_id, record.to_chapter_row())
                self.used_record_numbers.append(record_id)
            populated = True

        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS
        if not record.contains_min_one_label(self.user_defined_labels):
            # check if the record is already present among the chapters
            if self.__is_row_present(record_id) and not self.duplicity_allowed():
                return

            if not self._is_excluded_from_chapter(record, CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS):
                record.add_to_chapter_presence(CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS)
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

            if not self._is_excluded_from_chapter(record, OTHERS_NO_TOPIC):
                record.add_to_chapter_presence(OTHERS_NO_TOPIC)
                self.chapters[OTHERS_NO_TOPIC].add_row(record_id, record.to_chapter_row())
                self.used_record_numbers.append(record_id)

    def __populate_pr(self, record: PullRequestRecord, record_id: int | str) -> None:
        """
        Populates the service chapters with pull requests.

        Parameters:
            record: The record to populate.
            record_id: The ID of the record.

        Returns:
            None
        """
        if record.is_merged:
            consumed = False
            # check record properties if it fits to a chapter: MERGED_PRS_WITHOUT_ISSUE
            if not record.contains_issue_mentions() and not record.contains_min_one_label(self.user_defined_labels):
                if self.__is_row_present(record_id) and not self.duplicity_allowed():
                    return

                if not self._is_excluded_from_chapter(record, MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS):
                    record.add_to_chapter_presence(MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS)
                    self.chapters[MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(
                        record_id, record.to_chapter_row()
                    )
                    self.used_record_numbers.append(record_id)
                consumed = True

            # check record properties if it fits to a chapter: MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES
            if record.contains_issue_mentions():
                if self.__is_row_present(record_id) and not self.duplicity_allowed():
                    return

                if not self._is_excluded_from_chapter(record, MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES):
                    record.add_to_chapter_presence(MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES)
                    self.chapters[MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(record_id, record.to_chapter_row())
                    self.used_record_numbers.append(record_id)
                consumed = True

            if not consumed and not record.is_present_in_chapters:
                if self.__is_row_present(record_id) and not self.duplicity_allowed():
                    return

                if record_id in self.used_record_numbers:
                    return

                if not self._is_excluded_from_chapter(record, OTHERS_NO_TOPIC):
                    record.add_to_chapter_presence(OTHERS_NO_TOPIC)
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

            if not self._is_excluded_from_chapter(record, CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS):
                record.add_to_chapter_presence(CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS)
                self.chapters[CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(
                    record_id, record.to_chapter_row()
                )
                self.used_record_numbers.append(record_id)

        else:
            if self.__is_row_present(record_id) and not self.duplicity_allowed():
                return

            if record_id in self.used_record_numbers:
                return

            # not record.is_present_in_chapters:
            if not self._is_excluded_from_chapter(record, OTHERS_NO_TOPIC):
                record.add_to_chapter_presence(OTHERS_NO_TOPIC)
                self.chapters[OTHERS_NO_TOPIC].add_row(record_id, record.to_chapter_row())
                self.used_record_numbers.append(record_id)

    def __populate_direct_commit(self, record: CommitRecord, record_id: int | str) -> None:
        """
        Populates the service chapters with direct commits.

        @param record: The CommitRecord object representing the direct commit.
        @return: None
        """
        if not self._is_excluded_from_chapter(record, DIRECT_COMMITS):
            record.add_to_chapter_presence(DIRECT_COMMITS)
            self.chapters[DIRECT_COMMITS].add_row(record_id, record.to_chapter_row())
            self.used_record_numbers.append(record_id)

    def __is_row_present(self, record_id: int | str) -> bool:
        """
        Checks if the row is already present in the chapters.

        @param nr: The number of the record.
        @return: True if the row is present, False otherwise.
        """
        return record_id in self.used_record_numbers

    def _is_globally_excluded(self, record: Record) -> bool:
        """Check if the record matches any global (``"*"``) exclusion group."""
        return self._matches_any_group(record, self._global_exclude_groups)

    def _is_excluded_from_chapter(self, record: Record, chapter_title: str) -> bool:
        """Check if the record matches any per-chapter exclusion group for *chapter_title*."""
        groups = self._per_chapter_exclude_groups.get(chapter_title, [])
        return self._matches_any_group(record, groups)

    @staticmethod
    def _matches_any_group(record: Record, groups: list[list[str]]) -> bool:
        """Return True if the record labels are a superset of any label group."""
        if not groups:
            return False
        record_labels = set(record.labels)
        return any(record_labels.issuperset(group) for group in groups if group)

    @staticmethod
    def duplicity_allowed() -> bool:
        """
        Checks if duplicity is allowed in the service chapters.

        @return: True if duplicity is allowed, False otherwise.
        """
        return ActionInputs.get_duplicity_scope() in (DuplicityScopeEnum.SERVICE, DuplicityScopeEnum.BOTH)

    def to_string(self) -> str:
        """
        Converts the chapters to a string, excluding hidden chapters.
        Chapters are rendered in the order defined by self.chapter_order.

        @return: The chapters as a string.
        """
        result = ""
        for chapter_title in self.chapter_order:
            # Skip chapters that are in the hidden list
            if chapter_title in self.hidden_chapters:
                logger.debug("Skipping hidden service chapter: %s", chapter_title)
                continue

            chapter = self.chapters.get(chapter_title)
            if chapter is None:
                logger.error("Chapter %s not found in chapters dictionary.", chapter_title)
                continue

            chapter_string = chapter.to_string(
                sort_ascending=self.sort_ascending, print_empty_chapters=self.print_empty_chapters
            )
            if chapter_string:
                result += chapter_string + "\n\n"

        # Note: strip is required to remove leading newline chars when empty chapters are not printed option
        return result.strip()
