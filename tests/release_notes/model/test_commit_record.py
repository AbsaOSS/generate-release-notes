from release_notes_generator.model.commit_record import CommitRecord


def test_basic_properties(mock_commit):
    rec = CommitRecord(mock_commit)
    assert rec.record_id == "merge_commit_sha"
    assert rec.is_closed is True
    assert rec.is_open is False
    assert rec.skip is False

def test_authors_with_author(mock_commit):
    rec = CommitRecord(mock_commit)
    assert rec.authors == ["author"]

def test_authors_no_author(mock_commit):
    mock_commit.author = None
    rec = CommitRecord(mock_commit)
    assert rec.authors == []

def test_to_chapter_row_single_occurrence(monkeypatch, mock_commit):
    monkeypatch.setattr(
        "release_notes_generator.model.commit_record.ActionInputs.get_duplicity_icon",
        lambda: "🔁",
    )
    rec = CommitRecord(mock_commit)
    row = rec.to_chapter_row()
    # Newline in message replaced by space, no prefix on first addition
    assert row.startswith("Commit: merge_c... - Fixed bug")
    assert "🔁" not in row

def test_to_chapter_row_duplicate_with_icon(monkeypatch, mock_commit):
    monkeypatch.setattr(
        "release_notes_generator.model.commit_record.ActionInputs.get_duplicity_icon",
        lambda: "[D]",
    )
    rec = CommitRecord(mock_commit)
    first = rec.to_chapter_row(True)
    second = rec.to_chapter_row(True)
    assert not first.startswith("[D] ")
    assert second.startswith("[D] ")
    assert rec.present_in_chapters() == 2

def test_to_chapter_row_with_release_notes_injected(monkeypatch, mock_commit):
    # Force contains_release_notes to True and provide fake release notes
    monkeypatch.setattr(
        CommitRecord,
        "contains_release_notes",
        lambda _: True,
    )
    rec = CommitRecord(mock_commit)
    monkeypatch.setattr(rec, "get_rls_notes", lambda _line_marks=None: "Extra release notes.")
    row = rec.to_chapter_row()
    assert "\nExtra release notes." in row

def test_get_rls_notes_empty(mock_commit):
    rec = CommitRecord(mock_commit)
    assert rec.get_rls_notes() == ""
