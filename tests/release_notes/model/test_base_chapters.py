import pytest

from release_notes.model.base_chapters import BaseChapters


class Record:
    pass


class Chapters(BaseChapters):
    def populate(self, records: dict[int, Record]):
        pass  # Implement a minimal populate method for testing


# Test cases
@pytest.fixture
def chapters():
    return Chapters()


def test_add_row(chapters):
    chapters.add_row('Chapter 1', 1, 'Row 1')

    assert 'Chapter 1' in chapters.chapters
    assert chapters.chapters['Chapter 1'].rows[1] == 'Row 1'


def test_to_string(chapters):
    chapters.add_row('Chapter 1', 1, 'Row 1')
    chapters.add_row('Chapter 1', 2, 'Row 2')

    result = chapters.to_string()

    assert 'Row 1' in result
    assert 'Row 2' in result


def test_titles(chapters):
    chapters.add_row('Chapter 1', 1, 'Row 1')
    chapters.add_row('Chapter 2', 2, 'Row 2')

    titles = chapters.titles

    assert 'Chapter 1' in titles
    assert 'Chapter 2' in titles


def test_sort_ascending(chapters):
    chapters.sort_ascending = False
    chapters.add_row('Chapter 1', 1, 'Row 1')
    chapters.add_row('Chapter 1', 2, 'Row 2')

    result = chapters.to_string()
    print(result)

    assert '- Row 2' == result.split("\n")[1]
    assert '- Row 1' == result.split("\n")[2]


def test_print_empty_chapters(chapters):
    chapters.print_empty_chapters = False
    chapters.add_row('Chapter 1', 1, 'Row 1')

    result = chapters.to_string()

    assert 'Chapter 1' in result
