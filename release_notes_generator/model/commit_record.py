"""
A module that defines the CommitRecord class, which represents a direct commit record in the release notes.
"""

from typing import Optional

from github.Commit import Commit

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.record import Record


class CommitRecord(Record):
    """
    A class used to represent a direct commit record in the release notes.
    Inherits from Record and provides additional functionality specific to direct commits.
    """

    def __init__(self, commit: Commit, skip: bool = False):
        super().__init__(skip=skip)

        self._commit: Commit = commit

    # properties - override Record properties

    @property
    def record_id(self) -> int | str:
        return self._commit.sha

    @property
    def is_closed(self) -> bool:
        return True

    @property
    def is_open(self) -> bool:
        return False

    @property
    def authors(self) -> list[str]:
        return [self._commit.author.login] if self._commit.author else []

    # properties - specific to CommitRecord

    @property
    def commit(self) -> Commit:
        """
        Gets the commits associated with the record.
        Returns: The commits associated with the record.
        """
        return self._commit

    # methods - override Record methods

    def to_chapter_row(self, add_into_chapters: bool = True) -> str:
        if add_into_chapters:
            self.added_into_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""

        # collecting values for formatting
        commit_message = self._commit.commit.message.replace("\n", " ")
        row = f"{row_prefix}Commit: {self._commit.sha[:7]}... - {commit_message}"

        if self.contains_release_notes():
            row = f"{row}\n{self.get_rls_notes()}"

        return row

    def contains_change_increment(self) -> bool:
        return True

    def get_rls_notes(self, line_marks: Optional[list[str]] = None) -> str:
        # Hint: direct commits does not support release notes
        return ""

    def get_labels(self) -> list[str]:
        return []

    # methods - specific to CommitRecord
