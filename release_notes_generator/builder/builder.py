#
# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This module contains the ReleaseNotesBuilder class which is responsible for building of the release notes.
"""
import logging

from itertools import chain

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.chapters.custom_chapters import CustomChapters
from release_notes_generator.chapters.service_chapters import ServiceChapters
from release_notes_generator.model.record.record import Record
from release_notes_generator.utils.constants import CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS

logger = logging.getLogger(__name__)


class ReleaseNotesBuilder:
    """
    A class representing the Release Notes Builder.
    The class is responsible for building the release notes based on the records, changelog URL, formatter, and custom
    chapters.
    """

    def __init__(
        self,
        records: dict[str, Record],
        changelog_url: str,
        custom_chapters: CustomChapters,
    ):
        self.records = records
        self.changelog_url = changelog_url
        self.custom_chapters = custom_chapters

        self.warnings = ActionInputs.get_warnings()
        self.print_empty_chapters = ActionInputs.get_print_empty_chapters()

    def build(self) -> str:
        """
        Build the release notes based on the records, changelog URL, formatter, and custom chapters.

        @return: The release notes as a string.
        """
        logger.info("Building Release Notes")
        self.custom_chapters.populate(self.records)
        user_defined_chapters_str = self.custom_chapters.to_string()

        user_defined_labels_nested = [
            self.custom_chapters.chapters[key].labels for key in self.custom_chapters.chapters
        ]
        user_defined_labels = list(chain.from_iterable(user_defined_labels_nested))

        if self.warnings:
            service_chapters = ServiceChapters(
                print_empty_chapters=self.print_empty_chapters,
                user_defined_labels=user_defined_labels,
                used_record_numbers=self.custom_chapters.populated_record_numbers_list,
                hidden_chapters=ActionInputs.get_hidden_service_chapters(),
            )
            service_chapters.populate(self.records)

            # Get the "Closed Issues without User Defined Labels" chapter separately
            closed_issues_no_labels_str = service_chapters.get_chapter_string(CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS)

            # Get all other service chapters, excluding the one we output separately
            other_service_chapters_str = service_chapters.to_string(
                exclude_chapters=[CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS]
            )

            # Build the release notes with the new ordering:
            # 1. User-defined chapters
            # 2. Closed Issues without User Defined Labels (if present)
            # 3. Other service chapters
            # 4. Full Changelog
            parts = []
            if user_defined_chapters_str:
                parts.append(user_defined_chapters_str)
            if closed_issues_no_labels_str:
                parts.append(closed_issues_no_labels_str)
            if other_service_chapters_str:
                parts.append(other_service_chapters_str)

            if parts:
                release_notes = "\n\n".join(parts) + f"\n\n#### Full Changelog\n{self.changelog_url}\n"
            else:
                release_notes = f"#### Full Changelog\n{self.changelog_url}\n"
        else:
            release_notes = f"""{user_defined_chapters_str}\n\n#### Full Changelog\n{self.changelog_url}\n"""

        return release_notes.lstrip()
