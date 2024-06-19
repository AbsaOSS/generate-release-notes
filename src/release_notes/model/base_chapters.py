from abc import ABC
from release_notes.model.chapter import Chapter


class BaseChapters(ABC):
    def __init__(self, sort_ascending: bool = True):
        self.sort_ascending = sort_ascending
        self.chapters = {}

    def add_row(self, chapter_key, number: int, row: str):
        if chapter_key not in self.chapters:
            self.chapters[chapter_key] = Chapter(title=chapter_key)
        self.chapters[chapter_key].add_row(number, row)

    def to_string(self) -> str:
        return "".join([chapter.to_string(self.sort_ascending) for chapter in self.chapters.values()])

    @property
    def titles(self) -> list[str]:
        return [chapter.title for chapter in self.chapters.values()]
