from abc import ABC, abstractmethod
from release_notes.model.chapter import Chapter
from release_notes.model.record import Record


class BaseChapters(ABC):
    def __init__(self, sort_ascending: bool = True, print_empty_chapters: bool = True):
        self.sort_ascending = sort_ascending
        self.print_empty_chapters = print_empty_chapters
        self.chapters = {}

    def add_row(self, chapter_key, number: int, row: str):
        if chapter_key not in self.chapters:
            self.chapters[chapter_key] = Chapter(title=chapter_key)
        self.chapters[chapter_key].add_row(number, row)

    def to_string(self) -> str:
        result = "".join([chapter.to_string(
            sort_ascending=self.sort_ascending,
            print_empty_chapters=self.print_empty_chapters) + "\n\n" for chapter in self.chapters.values()])

        # Note: strip is required to remove leading newline chars when empty chapters are not printed option
        return result.strip()

    @property
    def titles(self) -> list[str]:
        return [chapter.title for chapter in self.chapters.values()]

    @abstractmethod
    def populate(self, records: dict[int, Record]):
        pass
