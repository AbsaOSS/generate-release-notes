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

import logging
from typing import Optional

from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit

from release_notes_generator.utils.constants import Constants
from release_notes_generator.utils.pull_reuqest_utils import extract_issue_numbers_from_body


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Record:
    """
    A class used to represent a record in the release notes.
    """

    RELEASE_NOTE_DETECTION_PATTERN = "Release notes:"
    RELEASE_NOTE_LINE_MARK = "-"

    def __init__(self, repo: Repository, issue: Optional[Issue] = None):
        """
        Constructs all the necessary attributes for the Record object.

        :param issue: An optional Issue object associated with the record.
        """
        self.__repo: Repository = repo
        self.__gh_issue: Issue = issue
        self.__pulls: list[PullRequest] = []
        self.__pull_commits: dict = {}

        self.__is_release_note_detected: bool = False
        self.__present_in_chapters = 0

    @property
    def number(self) -> int:
        """
        Gets the number of the record.

        :return: The number of the record as an integer.
        """
        if self.__gh_issue is None:
            return self.__pulls[0].number
        return self.__gh_issue.number

    @property
    def issue(self) -> Optional[Issue]:
        """
        Gets the issue associated with the record.

        :return: The Issue object associated with the record, or None if there is no issue.
        """
        return self.__gh_issue

    @property
    def pulls(self) -> list[PullRequest]:
        """
        Gets the pull requests associated with the record.

        :return: The list of PullRequest objects associated with the record.
        """
        return self.__pulls

    @property
    def commits(self) -> dict:
        """
        Gets the commits associated with the record.

        :return: The commits associated with the record.
        """
        return self.__pull_commits

    @property
    def is_present_in_chapters(self) -> bool:
        """
        Checks if the record is present in any chapters.

        :return: A boolean indicating whether the record is present in any chapters.
        """
        return self.__present_in_chapters > 0

    @property
    def is_pr(self) -> bool:
        """
        Checks if the record is a pull request.

        :return: A boolean indicating whether the record is a pull request.
        """
        return self.__gh_issue is None and len(self.__pulls) == 1

    @property
    def is_issue(self) -> bool:
        """
        Checks if the record is an issue.

        :return: A boolean indicating whether the record is an issue.
        """
        return self.__gh_issue is not None

    @property
    def is_closed(self) -> bool:
        """
        Checks if the record is closed.

        :return: A boolean indicating whether the record is closed.
        """
        if self.__gh_issue is None:
            # no issue ==> stand-alone PR
            return self.__pulls[0].state == Constants.PR_STATE_CLOSED

        return self.__gh_issue.state == Constants.ISSUE_STATE_CLOSED

    @property
    def is_closed_issue(self) -> bool:
        """
        Checks if the record is a closed issue.

        :return: A boolean indicating whether the record is a closed issue.
        """
        return self.is_issue and self.__gh_issue.state == Constants.ISSUE_STATE_CLOSED

    @property
    def is_open_issue(self) -> bool:
        """
        Checks if the record is a open issue.

        :return: A boolean indicating whether the record is a closed issue.
        """
        return self.is_issue and self.__gh_issue.state == Constants.ISSUE_STATE_OPEN

    @property
    def is_merged_pr(self) -> bool:
        """
        Checks if the record is a merged pull request.

        :return: A boolean indicating whether the record is a merged pull request.
        """
        if self.__gh_issue is None:
            return self.is_pull_request_merged(self.__pulls[0])
        return False

    @property
    def labels(self) -> list[str]:
        """
        Gets the labels of the record.

        :return: A list of the labels of the record.
        """
        if self.__gh_issue is None:
            return [label.name for label in self.__pulls[0].labels]

        return [label.name for label in self.__gh_issue.labels]

    # TODO in Issue named 'Configurable regex-based Release note detection in the PR body'
    #   - 'Release notest:' as detection pattern default - can be defined by user
    #   - '-' as leading line mark for each release note to be used
    def get_rls_notes(self, detection_pattern=RELEASE_NOTE_DETECTION_PATTERN, line_mark=RELEASE_NOTE_LINE_MARK) -> str:
        """
        Gets the release notes of the record.

        :param detection_pattern: The pattern to detect the start of the release notes.
        :param line_mark: The mark to detect the start of a line in the release notes.
        :return: The release notes as a string.
        """
        release_notes = ""

        # Iterate over all PRs
        for pull in self.__pulls:
            body_lines = pull.body.split('\n') if pull.body is not None else []
            inside_release_notes = False

            for line in body_lines:
                if detection_pattern in line:
                    inside_release_notes = True
                    continue

                if inside_release_notes:
                    if line.startswith(line_mark):
                        release_notes += f"  {line.strip()}\n"
                    else:
                        break

        # Return the concatenated release notes
        return release_notes.rstrip()

    @property
    def contains_release_notes(self) -> bool:
        """
        Checks if the record contains release notes.

        :return: A boolean indicating whether the record contains release notes.
        """
        if self.__is_release_note_detected:
            return self.__is_release_note_detected

        if self.RELEASE_NOTE_LINE_MARK in self.get_rls_notes():
            self.__is_release_note_detected = True

        return self.__is_release_note_detected

    @property
    def pulls_count(self) -> int:
        """
        Gets the number of pull requests associated with the record.

        :return: The number of pull requests associated with the record.
        """
        return len(self.__pulls)

    @property
    def pr_contains_issue_mentions(self) -> bool:
        """
        Checks if the pull request mentions an issue. The logic checks only first pr in record.

        :return: A boolean indicating whether the pull request mentions an issue.
        """
        return len(extract_issue_numbers_from_body(self.__pulls[0])) > 0

    @property
    def authors(self) -> Optional[str]:
        """
        Gets the authors of the record.

        :return: The authors of the record as a string, or None if there are no authors.
        """
        return None
        # TODO in Issue named 'Chapter line formatting - authors'
        # authors: list[str] = []
        #
        # for pull in self.__pulls:
        #     if pull.author is not None:
        #         authors.append(f"@{pull.author}")
        #
        # if len(authors) > 0:
        #     return None
        #
        # res = ", ".join(authors)
        # return res

    @property
    def contributors(self) -> Optional[str]:
        """
        Gets the contributors of the record.

        :return: The contributors of the record as a string, or None if there are no contributors.
        """
        return None

    @property
    def pr_links(self) -> Optional[str]:
        """
        Gets the links to the pull requests associated with the record.

        :return: The links to the pull requests as a string, or None if there are no pull requests.
        """
        if len(self.__pulls) == 0:
            return None

        template = "[#{number}](https://github.com/{full_name}/pull/{number})"
        res = [
            template.format(number=pull.number, full_name=self.__repo.full_name)
            for pull in self.__pulls
        ]

        return ", ".join(res)

    def pull_request_commit_count(self, pull_number: int = 0) -> int:
        """
        Gets the count of commits associated with the pull request.

        :param pull_number: The number of the pull request.
        :return: The count of commits associated with the pull request.
        """
        for pull in self.__pulls:
            if pull.number == pull_number:
                if pull.number in self.__pull_commits:
                    return len(self.__pull_commits.get(pull.number))

                return 0

        return 0

    def pull_request(self, index: int = 0) -> Optional[PullRequest]:
        """
        Gets a pull request associated with the record.

        :param index: The index of the pull request.
        :return: The PullRequest object.
        """
        if index < 0 or index >= len(self.__pulls):
            return None
        return self.__pulls[index]

    def register_pull_request(self, pull):
        """
        Registers a pull request with the record.

        :param pull: The PullRequest object to register.
        """
        self.__pulls.append(pull)

    def register_commit(self, commit: Commit):
        """
        Registers a commit with the record.

        :param commit: The Commit object to register.
        """
        for pull in self.__pulls:
            if commit.sha == pull.merge_commit_sha:
                if self.__pull_commits.get(pull.number) is None:
                    self.__pull_commits[pull.number] = []
                self.__pull_commits[pull.number].append(commit)
                return

        logging.error("Commit %s not registered in any PR of record %s", commit.sha, self.number)

    # TODO in Issue named 'Chapter line formatting - default'
    def to_chapter_row(self, row_format="", increment_in_chapters=True) -> str:
        """
        Converts the record to a row in a chapter.

        :param row_format: The format of the row.
        :param increment_in_chapters: A boolean indicating whether to increment the count of chapters.
        :return: The record as a row in a chapter.
        """
        if increment_in_chapters:
            self.increment_present_in_chapters()

        if self.__gh_issue is None:
            p = self.__pulls[0]

            row = f"PR: #{p.number} _{p.title}_"

            # Issue can have more authors (as multiple PRs can be present)
            if self.authors is not None:
                row = f"{row}, implemented by {self.authors}"

            if self.contributors is not None:
                row = f"{row}, contributed by {self.contributors}"

            if self.contains_release_notes:
                return f"{row}\n{self.get_rls_notes()}"

        else:
            row = f"#{self.__gh_issue.number} _{self.__gh_issue.title}_"

            if self.authors is not None:
                row = f"{row}, implemented by {self.authors}"

            if self.contributors is not None:
                row = f"{row}, contributed by {self.contributors}"

            if len(self.__pulls) > 0:
                row = f"{row} in {self.pr_links}"

            if self.contains_release_notes:
                row = f"{row}\n{self.get_rls_notes()}"

        return row

    def contains_min_one_label(self, labels: list[str]) -> bool:
        """
        Checks if the record contains at least one of the received labels.

        :param labels: A list of labels to check for.
        :return: A boolean indicating whether the record contains any of the specified labels.
        """
        for lbl in self.labels:
            if lbl in labels:
                return True
        return False

    def contain_all_labels(self, labels: list[str]) -> bool:
        """
        Checks if the record contains all of received labels.

        :param labels: A list of labels to check for.
        :return: A boolean indicating whether the record contains any of the specified labels.
        """
        if len(self.labels) != len(labels):
            return False

        for lbl in self.labels:
            if lbl not in labels:
                return False
        return True

    def increment_present_in_chapters(self):
        """
        Increments the count of chapters in which the record is present.
        """
        self.__present_in_chapters += 1

    def present_in_chapters(self) -> int:
        """
        Gets the count of chapters in which the record is present.

        :return: The count of chapters in which the record is present.
        """
        return self.__present_in_chapters

    def is_commit_sha_present(self, sha: str) -> bool:
        """
        Checks if the specified commit SHA is present in the record.

        :param sha: The commit SHA to check for.
        :return: A boolean indicating whether the specified commit SHA is present in the record.
        """
        for pull in self.__pulls:
            if pull.merge_commit_sha == sha:
                return True

        return False

    @staticmethod
    def is_pull_request_merged(pull: PullRequest) -> bool:
        return pull.state == Constants.PR_STATE_CLOSED and pull.merged_at is not None and pull.closed_at is not None
