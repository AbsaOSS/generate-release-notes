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
from abc import ABCMeta, abstractmethod

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.model.record import Record


class ReleaseNotesBuilder(metaclass=ABCMeta):
    """
    A class representing the Release Notes Builder.
    The class is responsible for building the release notes based on the records, changelog URL, formatter, and custom
    chapters.
    """

    def __init__(
        self,
        records: dict[int | str, Record],
        changelog_url: str,
        custom_chapters: CustomChapters,
    ):
        self.records = records
        self.changelog_url = changelog_url
        self.custom_chapters = custom_chapters

        self.warnings = ActionInputs.get_warnings()
        self.print_empty_chapters = ActionInputs.get_print_empty_chapters()

    @abstractmethod
    def build(self) -> str:
        """
        Build the release notes based on the records, changelog URL, formatter, and custom chapters.

        @return: The release notes as a string.
        """
