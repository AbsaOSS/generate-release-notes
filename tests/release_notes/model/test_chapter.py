from src.release_notes.model.chapter import Chapter


# __init__

def test_chapter_init():
    chapter = Chapter("Test Title", ["label1", "label2"])
    assert chapter.title == "Test Title"
    assert chapter.labels == ["label1", "label2"]
    assert chapter.rows == {}


# add_row

def test_add_row():
    chapter = Chapter("Test Title", ["label1", "label2"])
    chapter.add_row(1, "Test Row")
    assert {1: "Test Row"} == chapter.rows


# to_string

def test_to_string_ascending():
    chapter = Chapter("Test Title", ["label1", "label2"])
    chapter.add_row(1, "Test Row 1")
    chapter.add_row(2, "Test Row 2")
    expected_output = "### Test Title\nTest Row 1\nTest Row 2\n\n"
    assert expected_output == chapter.to_string(sort_ascending=True)


def test_to_string_descending():
    chapter = Chapter("Test Title", ["label1", "label2"])
    chapter.add_row(1, "Test Row 1")
    chapter.add_row(2, "Test Row 2")
    expected_output = "### Test Title\nTest Row 2\nTest Row 1\n\n"
    assert expected_output == chapter.to_string(sort_ascending=False)
