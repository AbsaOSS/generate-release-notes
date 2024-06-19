from release_notes.model.chapter import Chapter
from release_notes.model.custom_chapters import CustomChapters


# __init__

def test_chapters_init():
    chapters = CustomChapters()

    assert chapters.sort_ascending == True
    assert chapters.chapters == {}


# add_row

def test_chapters_add_row():
    chapters = CustomChapters()
    chapters.add_row("Test Chapter", 1, "Test Row")

    assert "Test Chapter" in chapters.chapters
    assert {1: "Test Row"} == chapters.chapters["Test Chapter"].rows


# to_string

def test_chapters_to_string():
    chapters = CustomChapters()
    chapters.add_row("Test Chapter", 1, "Test Row")
    expected_output = "### Test Chapter\n- Test Row"

    print(f"Actual:\nx{chapters.to_string()}x")
    print(f"Expected:\nx{expected_output}x")

    assert expected_output == chapters.to_string()


# from_json

def test_custom_chapters_from_json():
    custom_chapters = CustomChapters()
    json_string = '''
    [
        {"title": "Breaking Changes 💥", "label": "breaking-change"},
        {"title": "New Features 🎉", "label": "enhancement"},
        {"title": "New Features 🎉", "label": "feature"},
        {"title": "Bugfixes 🛠", "label": "bug"}
    ]
    '''
    custom_chapters.from_json(json_string)

    assert "Breaking Changes 💥" in custom_chapters.titles
    assert "New Features 🎉" in custom_chapters.titles
    assert "Bugfixes 🛠" in custom_chapters.titles
    assert isinstance(custom_chapters.chapters["Breaking Changes 💥"], Chapter)
    assert isinstance(custom_chapters.chapters["New Features 🎉"], Chapter)
    assert isinstance(custom_chapters.chapters["Bugfixes 🛠"], Chapter)
    assert ["breaking-change"] == custom_chapters.chapters["Breaking Changes 💥"].labels
    assert ["enhancement", "feature"] == custom_chapters.chapters["New Features 🎉"].labels
    assert ["bug"] == custom_chapters.chapters["Bugfixes 🛠"].labels
