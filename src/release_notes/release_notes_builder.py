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
        """
        Constructs all the necessary attributes for the ReleaseNotesBuilder object.

        :param records: A dictionary of records where the key is an integer and the value is a Record object.
        :param changelog_url: The URL of the changelog.
        :param formatter: A RecordFormatter object used to format the records.
        :param custom_chapters: A CustomChapters object representing the custom chapters.
        :param warnings: A boolean indicating whether to show warnings.
        :param print_empty_chapters: A boolean indicating whether to print empty chapters.
        """
        self.records = records
        self.changelog_url = changelog_url
        self.formatter = formatter
        self.custom_chapters = custom_chapters
        self.warnings = warnings
        self.print_empty_chapters = print_empty_chapters

    def build(self) -> str:
        """
        Builds the release notes.

        :return: The release notes as a string.
        """
        logging.info("Building Release Notes")
        user_defined_chapters = self.custom_chapters
        user_defined_chapters.populate(self.records)
        user_defined_chapters_str = user_defined_chapters.to_string()

        user_defined_labels_nested = [user_defined_chapters.chapters[key].labels for key in user_defined_chapters.chapters.keys()]
        user_defined_labels = list(chain.from_iterable(user_defined_labels_nested))

        if self.warnings:
            service_chapters = ServiceChapters(print_empty_chapters=self.print_empty_chapters, user_defined_labels=user_defined_labels)
            service_chapters.populate(self.records)

            service_chapters_str = service_chapters.to_string()
            if len(service_chapters_str) > 0:
                release_notes = f"""{user_defined_chapters_str}\n\n{service_chapters_str}\n\n#### Full Changelog\n{self.changelog_url}\n"""
            else:
                release_notes = f"""{user_defined_chapters_str}\n\n#### Full Changelog\n{self.changelog_url}\n"""
        else:
            release_notes = f"""{user_defined_chapters_str}\n\n#### Full Changelog\n{self.changelog_url}\n"""

        return release_notes.lstrip()
