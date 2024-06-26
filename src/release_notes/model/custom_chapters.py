import json
import logging

from release_notes.model.base_chapters import BaseChapters
from release_notes.model.chapter import Chapter
from release_notes.model.record import Record


class CustomChapters(BaseChapters):
    """
    A class used to represent the custom chapters in the release notes.
    """

    def populate(self, records: dict[int, Record]):
        """
        Populates the custom chapters with records.

        :param records: A dictionary of records where the key is an integer and the value is a Record object.
        """
        for nr in records.keys():                               # iterate all records
            for ch_key in self.chapters.keys():                 # iterate all chapters
                for record_label in records[nr].labels:         # iterate all labels of the record (issue, or 1st PR)
                    if record_label in self.chapters[ch_key].labels and records[nr].pulls_count > 0:
                        if not records[nr].is_present_in_chapters:
                            self.chapters[ch_key].add_row(nr, records[nr].to_chapter_row())

    def from_json(self, json_string: str):
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
