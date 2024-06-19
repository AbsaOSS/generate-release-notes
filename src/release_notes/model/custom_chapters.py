import json

from release_notes.model.base_chapters import BaseChapters
from release_notes.model.chapter import Chapter


class CustomChapters(BaseChapters):
    def from_json(self, json_string: str):
        data = json.loads(json_string)
        for item in data:
            title = item['title']
            labels = [item['label']]
            if title not in self.chapters:
                self.chapters[title] = Chapter(title, labels)
            else:
                self.chapters[title].labels.extend(labels)
