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
This module contains the DefaultRecordFactory class which is responsible for generating
"""
import abc
import logging

from github import Github
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.model.record import Record

logger = logging.getLogger(__name__)


class RecordFactory(metaclass=abc.ABCMeta):
    """
    A class used to generate records for release notes.
    """

    @abc.abstractmethod
    def generate(self, github: Github, data: MinedData) -> dict[int | str, Record]:
        """
        Generate records for release notes.
        Parameters:
            github (GitHub): The GitHub instance to generate records for.
            data (MinedData): The MinedData instance containing repository, issues, pull requests, and commits.
        Returns:
            dict[int|str, Record]: A dictionary of records where the key is the issue or pull request number.
        """

    # TODO - do review of children and decide if more useful method could be defined here for inheritation
    #   fix unit test first to detect breaking changes
