import logging
from itertools import chain

from release_notes.formatter.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.model.service_chapters import ServiceChapters


class ReleaseNotesBuilder:
    def __init__(self, records: dict[int, Record], changelog_url: str,
                 formatter: RecordFormatter, custom_chapters: CustomChapters,
                 warnings: bool = True, print_empty_chapters: bool = True):
        self.records = records
        self.changelog_url = changelog_url
        self.formatter = formatter
        self.custom_chapters = custom_chapters
        self.warnings = warnings
        self.print_empty_chapters = print_empty_chapters

    def build(self) -> str:
        user_defined_chapters = self.custom_chapters
        user_defined_chapters.populate(self.records)
        user_defined_chapters_str = user_defined_chapters.to_string()

        user_defined_labels_nested = [user_defined_chapters.chapters[key].labels for key in user_defined_chapters.chapters.keys()]
        user_defined_labels = list(chain.from_iterable(user_defined_labels_nested))

        if self.warnings:
            service_chapters = ServiceChapters(print_empty_chapters=self.print_empty_chapters, user_defined_labels=user_defined_labels)
            service_chapters.populate(self.records)

            service_chapters_str = service_chapters.to_string()
            release_notes = f"""{user_defined_chapters_str}\n\n{service_chapters_str}\n\n#### Full Changelog\n{self.changelog_url}\n"""
        else:
            release_notes = f"""{user_defined_chapters_str}\n\n#### Full Changelog\n{self.changelog_url}\n"""

        return release_notes
