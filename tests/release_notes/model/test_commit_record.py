import types

from release_notes_generator.model.commit_record import CommitRecord

class DummyInnerCommit:
    def __init__(self, sha: str, message: str):
        self.sha = sha
        self.message = message

class DummyCommit:
    def __init__(self, sha: str, message: str, author_login: str | None = None):
        self.sha = sha
        self.commit = DummyInnerCommit(sha, message)
        self.author = types.SimpleNamespace(login=author_login) if author_login else None

def test_basic_properties():
    commit = DummyCommit("abcdef1234567890", "Fix: something")
    rec = CommitRecord(commit)
    assert rec.record_id == "abcdef1234567890"
    assert rec.is_closed is True
    assert rec.is_open is False
    assert rec.labels == []
    assert rec.skip is False

def test_authors_with_author():
    commit = DummyCommit("abcdef1", "Message", author_login="alice")
    rec = CommitRecord(commit)
    assert rec.authors == ["alice"]

def test_authors_no_author():
    commit = DummyCommit("abcdef1", "Message", author_login=None)
    rec = CommitRecord(commit)
    assert rec.authors == []

def test_to_chapter_row_single_occurrence(monkeypatch):
    monkeypatch.setattr(
        "release_notes_generator.model.commit_record.ActionInputs.get_duplicity_icon",
        lambda: "🔁",
    )
    commit = DummyCommit("1234567890abcd", "First line\nSecond line")
    rec = CommitRecord(commit)
    row = rec.to_chapter_row()
    # Newline in message replaced by space, no prefix on first addition
    assert row.startswith("Commit: 1234567 - First line Second line")
    assert "🔁" not in row

def test_to_chapter_row_duplicate_with_icon(monkeypatch):
    monkeypatch.setattr(
        "release_notes_generator.model.commit_record.ActionInputs.get_duplicity_icon",
        lambda: "[D]",
    )
    commit = DummyCommit("feedbeefcafebab0", "Some change")
    rec = CommitRecord(commit)
    first = rec.to_chapter_row()
    second = rec.to_chapter_row()
    assert not first.startswith("[D] ")
    assert second.startswith("[D] ")
    assert rec.present_in_chapters() == 2

def test_to_chapter_row_with_release_notes_injected(monkeypatch):
    # Force contains_release_notes to True and provide fake release notes
    monkeypatch.setattr(
        CommitRecord,
        "contains_release_notes",
        property(lambda self: True),
    )
    commit = DummyCommit("aa11bb22cc33", "Add feature")
    rec = CommitRecord(commit)
    monkeypatch.setattr(rec, "get_rls_notes", lambda line_marks=None: "Extra release notes.")
    row = rec.to_chapter_row()
    assert "\nExtra release notes." in row

def test_get_rls_notes_empty():
    commit = DummyCommit("deadbeef1234", "Refactor")
    rec = CommitRecord(commit)
    assert rec.get_rls_notes() == ""
