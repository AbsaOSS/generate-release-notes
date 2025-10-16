# Baseline legacy snapshot test for custom chapters output (T001)
# Ensures backward compatibility before multi-label feature implementation.

from release_notes_generator.chapters.custom_chapters import CustomChapters


def build_mock_record(record_id: str, labels: list[str]):
    class R:
        def __init__(self, _id: str, _labels: list[str]):
            self.id = _id
            self.labels = _labels
            self.skip = False
            self.is_present_in_chapters = False

        def contains_change_increment(self):  # matches code expectation in populate
            return True

        def to_chapter_row(self, _include_prs: bool):  # simplified row rendering
            return f"{self.id} row"

    return R(record_id, labels)


def test_legacy_single_label_snapshot():
    chapters_yaml = [
        {"title": "Bugfixes 🛠️", "label": "bug"},
        {"title": "Enhancements 🎉", "label": "enhancement"},
    ]

    custom = CustomChapters()
    custom.from_yaml_array(chapters_yaml)

    records = {
        "org/repo#1": build_mock_record("org/repo#1", ["bug"]),
        "org/repo#2": build_mock_record("org/repo#2", ["enhancement"]),
        "org/repo#3": build_mock_record("org/repo#3", ["other"]),  # should not appear
    }

    custom.populate(records)
    output = custom.to_string()

    expected = (
        "### Bugfixes 🛠️\n"
        "- org/repo#1 row\n\n"
        "### Enhancements 🎉\n"
        "- org/repo#2 row"
    )

    assert output == expected, f"Legacy snapshot changed.\nExpected:\n{expected}\nActual:\n{output}"


def test_multi_label_integration_snapshot():  # T019
    chapters_yaml = [
        {"title": "Changes", "labels": "bug, enhancement"},
        {"title": "Platform", "labels": ["platform", "infra"]},
        {"title": "Mixed", "labels": "feature\nbug"},
    ]
    custom = CustomChapters()
    custom.from_yaml_array(chapters_yaml)

    records = {
        "org/repo#10": build_mock_record("org/repo#10", ["bug", "enhancement"]),  # appears once in Changes, once in Mixed
        "org/repo#11": build_mock_record("org/repo#11", ["platform"]),  # appears in Platform only
        "org/repo#12": build_mock_record("org/repo#12", ["infra", "platform"]),  # Platform only once
        "org/repo#13": build_mock_record("org/repo#13", ["feature"])  # Mixed only
    }
    custom.populate(records)
    out = custom.to_string()

    # Validate intra-chapter uniqueness
    assert out.count("org/repo#10") == 2  # appears in two chapters
    assert out.count("org/repo#11") == 1
    assert out.count("org/repo#12") == 1
    assert out.count("org/repo#13") == 1
