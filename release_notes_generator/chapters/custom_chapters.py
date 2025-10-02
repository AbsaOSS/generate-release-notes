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

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.chapters.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.record import Record
from release_notes_generator.utils.enums import DuplicityScopeEnum

logger = logging.getLogger(__name__)


class CustomChapters(BaseChapters):
    """
    A class used to represent the custom chapters in the release notes.
    """

    def populate(self, records: dict[str, Record]) -> None:
        """
        Populates the custom chapters with records.

        Parameters:
            @param records: A dictionary of records keyed by 'owner/repo#number' and values are Record objects.

        Returns:
            None
        """
        for record_id, record in records.items():  # iterate all records
            if not records[record_id].contains_change_increment():
                continue

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

                for record_label in records[record_id].labels:  # iterate all labels of the record (issue, or 1st PR)
                    if record_label in ch.labels:
                        if records[record_id].is_present_in_chapters:
                            allow_dup = ActionInputs.get_duplicity_scope() in (
                                DuplicityScopeEnum.CUSTOM,
                                DuplicityScopeEnum.BOTH,
                            )
                            if not allow_dup:
                                continue

                        if record_id not in ch.rows.keys():
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
