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

from github.PullRequest import PullRequest

from release_notes_generator.model.record import Record


class RecordFormatter:
    """
    A class used to format records for release notes.
    """

    DEFAULT_ISSUE_PATTERN: str = "- #{number} _{title}_ implemented by {developers} in {pull_requests}\n{release_note_rows}"
    DEFAULT_PULL_REQUESTS_PATTERN: str = "[#{number}]({url})"

    def __init__(self, issue_pattern: str = DEFAULT_ISSUE_PATTERN,
                 pull_requests_pattern: str = DEFAULT_PULL_REQUESTS_PATTERN):
        """
        Constructs all the necessary attributes for the RecordFormatter object.

        :param issue_pattern: A string pattern for formatting issues.
        :param pull_requests_pattern: A string pattern for formatting pull requests.
        """
        self.issue_pattern = issue_pattern
        self.pull_requests_pattern = pull_requests_pattern

    def format(self, record: Record) -> str:
        """
        Formats a record.

        :param record: The Record object to format.
        :return: The formatted record as a string.
        """
        # create a dict of supported keys and values - from record
        params = {
            "title": record.issue.title if record.issue is not None else record.pulls[0].title,
            "number": record.issue.number if record.issue is not None else record.pulls[0].number,
            "labels": record.labels,
            "is_closed": record.is_closed,
            "is_pr": record.is_pr,
            "is_issue": record.is_issue,
            "developers": self._format_developers(record),
            "release_note_rows": self._format_release_note_rows(record),
            "pull_requests": self._format_pulls(record.pulls)
        }

        # apply to pattern
        return self.issue_pattern.format(**params)

    def _format_pulls(self, pulls: list['PullRequest']) -> str:
        """
        Formats a list of pull requests.

        :param pulls: The list of PullRequest objects to format.
        :return: The formatted pull requests as a string.
        """
        return ", ".join([self.pull_requests_pattern.format(number=pr.number, url=pr.url) for pr in pulls])

    def _format_developers(self, record: 'Record') -> str:
        """
        Formats the developers of a record.

        :param record: The Record object whose developers to format.
        :return: The formatted developers as a string.
        """
        developers = []
        # if record.gh_issue and record.gh_issue.assignees:
        #     developers.extend(record.gh_issue.assignees)
        # for pr in record.pulls:
        #     if pr.assignees:
        #         developers.extend(pr.assignees)
        return ', '.join(developers) if developers else "developers"

    def _format_release_note_rows(self, record: 'Record') -> str:
        """
        Formats the release note rows of a record.

        :param record: The Record object whose release note rows to format.
        :return: The formatted release note rows as a string.
        """
        return "  - release notes 1\n  - release notes 2"
        # return "\n  - ".join(record.release_note_rows()) if record.release_note_rows() else "  - No release notes"
