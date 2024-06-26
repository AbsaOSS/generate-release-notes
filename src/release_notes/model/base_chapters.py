from abc import ABC, abstractmethod
from release_notes.model.chapter import Chapter
from release_notes.model.record import Record


class BaseChapters(ABC):
    """
    An abstract base class representing the base chapters.
    """

    def __init__(self, sort_ascending: bool = True, print_empty_chapters: bool = True):
        """
        Constructs all the necessary attributes for the BaseChapters object.

        :param sort_ascending: A boolean indicating whether to sort the chapters in ascending order.
        :param print_empty_chapters: A boolean indicating whether to print empty chapters.
        """
        self.sort_ascending = sort_ascending
        self.print_empty_chapters = print_empty_chapters
        self.chapters: dict[str, Chapter] = {}

    def add_row(self, chapter_key: str, number: int, row: str):
        """
        Adds a row to a chapter.

        :param chapter_key: The key of the chapter.
        :param number: The number of the row.
        :param row: The row to add.
        """
        if chapter_key not in self.chapters:
            self.chapters[chapter_key] = Chapter(title=chapter_key)
        self.chapters[chapter_key].add_row(number, row)

    def to_string(self) -> str:
        """
        Converts the chapters to a string.

        :return: The chapters as a string.
        """
        result = "".join([chapter.to_string(
            sort_ascending=self.sort_ascending,
            print_empty_chapters=self.print_empty_chapters) + "\n\n" for chapter in self.chapters.values()])

        # Note: strip is required to remove leading newline chars when empty chapters are not printed option
        return result.strip()

    @property
    def titles(self) -> list[str]:
        """
        Gets the titles of the chapters.

        :return: A list of the titles of the chapters.
        """
        return [chapter.title for chapter in self.chapters.values()]

    @abstractmethod
    def populate(self, records: dict[int, Record]):
        """
        Populates the chapters with records.

        :param records: A dictionary of records where the key is an integer and the value is a Record object.
        """
        pass
