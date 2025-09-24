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
This module contains the CustomChapters class which is responsible for representing the custom chapters in the release
notes.
"""
import logging
from typing import cast

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.chapters.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.record import Record
from release_notes_generator.model.sub_issue_record import SubIssueRecord
from release_notes_generator.utils.enums import DuplicityScopeEnum

logger = logging.getLogger(__name__)


class CustomChapters(BaseChapters):
    """
    A class used to represent the custom chapters in the release notes.
    """

    def populate(self, records: dict[int | str, Record]) -> None:
        """
        Populates the custom chapters with records.

        @param records: A dictionary of records where the key is an integer and the value is a Record object.
        @return: None
        """
        for record_id, record in records.items():  # iterate all records
            # check if the record should be skipped
            if records[record_id].skip:
                continue

            # skip direct commits as they do not have labels
            if isinstance(record, CommitRecord):
                continue

            for ch in self.chapters.values():  # iterate all chapters
                if record_id in self.populated_record_numbers_list and ActionInputs.get_duplicity_scope() not in (
                    DuplicityScopeEnum.CUSTOM,
                    DuplicityScopeEnum.BOTH,
                ):
                    continue

                pulls_count = 1
                if isinstance(records[record_id], (HierarchyIssueRecord, IssueRecord, SubIssueRecord)):
                    pulls_count = cast(IssueRecord, records[record_id]).pull_requests_count()

                for record_label in records[record_id].labels:  # iterate all labels of the record (issue, or 1st PR)
                    if record_label in ch.labels and pulls_count > 0:
                        if not records[record_id].is_present_in_chapters:
                            ch.add_row(record_id, records[record_id].to_chapter_row(True))
                            self.populated_record_numbers_list.append(record_id)

    def from_yaml_array(self, chapters: list[dict[str, str]]) -> "CustomChapters":
        """
        Populates the custom chapters from a JSON string.

        @param chapters: A list of dictionaries where each dictionary represents a chapter.
        @return: The instance of the CustomChapters class.
        """
        for chapter in chapters:
            title = chapter["title"]
            labels = [chapter["label"]]
            if title not in self.chapters:
                self.chapters[title] = Chapter(title, labels)
            else:
                self.chapters[title].labels.extend(labels)

        return self
