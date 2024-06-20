from release_notes.model.service_chapters import ServiceChapters


# __init__

def test_init():
    service_chapters = ServiceChapters()
    assert service_chapters.sort_ascending == True
    assert isinstance(service_chapters.chapters, dict)
    assert len(service_chapters.chapters) == 8


def test_chapter_titles():
    service_chapters = ServiceChapters()
    expected_titles = [
        "Closed Issues without Pull Request ⚠️",
        "Closed Issues without User Defined Labels ⚠️",
        "Closed Issues without Release Notes ⚠️",
        "Merged PRs without Linked Issue⚠️",
        "Merged PRs without Labels ⚠️",
        "Merged PRs Linked to Open Issue ⚠️",
        "Closed PRs without Linked Issue ⚠️",
        "Closed PRs without Labels ⚠️"
    ]
    actual_titles = [chapter.title for chapter in service_chapters.chapters.values()]
    assert actual_titles == expected_titles
