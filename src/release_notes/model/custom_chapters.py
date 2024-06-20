import json

from release_notes.model.base_chapters import BaseChapters
from release_notes.model.chapter import Chapter
from release_notes.model.record import Record


class CustomChapters(BaseChapters):
    def populate(self, records: dict[int, Record]):
        for nr in records.keys():                               # iterate all records
            for ch_key in self.chapters.keys():                 # iterate all chapters
                for record_label in records[nr].labels:         # iterate all labels of the record (issue, or 1st PR)
                    if record_label in self.chapters[ch_key].labels:
                        self.chapters[ch_key].add_row(nr, records[nr].to_chapter_row())

    def from_json(self, json_string: str):
        data = json.loads(json_string)
        for item in data:
            title = item['title']
            labels = [item['label']]
            if title not in self.chapters:
                self.chapters[title] = Chapter(title, labels)
            else:
                self.chapters[title].labels.extend(labels)
