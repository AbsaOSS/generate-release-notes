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

import json

from release_notes_generator.model.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.record import Record


class CustomChapters(BaseChapters):
    """
    A class used to represent the custom chapters in the release notes.
    """

    def populate(self, records: dict[int, Record]):
        """
        Populates the custom chapters with records.

        :param records: A dictionary of records where the key is an integer and the value is a Record object.
        """
        for nr in records:                                      # iterate all records
            for _, ch in self.chapters.items():                 # iterate all chapters
                for record_label in records[nr].labels:         # iterate all labels of the record (issue, or 1st PR)
                    if record_label in ch.labels and records[nr].pulls_count > 0:
                        if not records[nr].is_present_in_chapters:
                            ch.add_row(nr, records[nr].to_chapter_row())
                            self.populated_record_numbers_list.append(nr)

    def from_json(self, json_string: str) -> 'CustomChapters':
        """
        Populates the custom chapters from a JSON string.

        :param json_string: The JSON string containing the custom chapters.
        """
        data = json.loads(json_string)
        for item in data:
            title = item['title']
            labels = [item['label']]
            if title not in self.chapters:
                self.chapters[title] = Chapter(title, labels)
            else:
                self.chapters[title].labels.extend(labels)

        return self
