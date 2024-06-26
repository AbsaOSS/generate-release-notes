import logging
from typing import Optional

from github_integration.github_manager import GithubManager
from github_integration.model.commit import Commit
from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest


class Record:
    """
    A class used to represent a record in the release notes.
    """

    RELEASE_NOTE_DETECTION_PATTERN = "Release notes:"
    RELEASE_NOTE_LINE_MARK = "-"

    def __init__(self, issue: Optional[Issue] = None):
        """
        Constructs all the necessary attributes for the Record object.

        :param issue: An optional Issue object associated with the record.
        """
        self.__gh_issue: Issue = issue
        self.__pulls: list[PullRequest] = []
        self.__is_release_note_detected: bool = False
        self.__present_in_chapters = 0

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
        return self.__gh_issue is None

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
            return self.__pulls[0].state == PullRequest.PR_STATE_CLOSED
        else:
            return self.__gh_issue.state == Issue.ISSUE_STATE_CLOSED

    @property
    def is_closed_issue(self) -> bool:
        """
        Checks if the record is a closed issue.

        :return: A boolean indicating whether the record is a closed issue.
        """
        return self.is_issue and self.__gh_issue.state == Issue.ISSUE_STATE_CLOSED

    @property
    def is_open_issue(self) -> bool:
        """
        Checks if the record is a open issue.

        :return: A boolean indicating whether the record is a closed issue.
        """
        return self.is_issue and self.__gh_issue.state == Issue.ISSUE_STATE_OPEN

    @property
    def is_merged_pr(self) -> bool:
        """
        Checks if the record is a merged pull request.

        :return: A boolean indicating whether the record is a merged pull request.
        """
        if self.__gh_issue is None:
            return self.__pulls[0].is_merged
        return False

    @property
    def labels(self) -> list[str]:
        """
        Gets the labels of the record.

        :return: A list of the labels of the record.
        """
        if self.__gh_issue is None:
            return self.__pulls[0].labels
        else:
            return self.__gh_issue.labels

    # TODO in Issue named 'Configurable regex-based Release note detection in the PR body'
    #   - 'Release notest:' as detection pattern default - can be defined by user
    #   - '-' as leading line mark for each release note to be used
    @property
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
            body_lines = pull.body.split('\n')
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

        if self.RELEASE_NOTE_LINE_MARK in self.get_rls_notes:
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
        return self.__pulls[0].body_contains_issue_mention

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

        gh_manager = GithubManager()

        template = "[#{number}](https://github.com/{full_name}/pull/{number})"
        res = [
            template.format(number=pull.number, full_name=gh_manager.get_repository_full_name())
            for pull in self.__pulls
        ]

        return ", ".join(res)

    def pull_request(self, index: int = 0) -> PullRequest:
        """
        Gets a pull request associated with the record.

        :param index: The index of the pull request.
        :return: The PullRequest object.
        """
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
                logging.debug(f"YYY Record: Registering commit {commit.sha} to PR {pull.number}")
                pull.register_commit(commit)
                return

        logging.error(f"Commit {commit.sha} not registered in any PR of record {self.__gh_issue.number}")

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
                return f"{row}\n{self.get_rls_notes}"

            return row
        else:
            row = f"#{self.__gh_issue.number} _{self.__gh_issue.title}_"

            if self.authors is not None:
                row = f"{row}, implemented by {self.authors}"

            if self.contributors is not None:
                row = f"{row}, contributed by {self.contributors}"

            if len(self.__pulls) > 0:
                row = f"{row} in {self.pr_links}"

            if self.contains_release_notes:
                return f"{row}\n{self.get_rls_notes}"

            return row

    def contains_labels(self, labels: list[str]) -> bool:
        """
        Checks if the record contains any of the specified labels.

        :param labels: A list of labels to check for.
        :return: A boolean indicating whether the record contains any of the specified labels.
        """
        if self.is_issue:
            return self.__gh_issue.contains_labels(labels)
        else:
            return self.__pulls[0].contains_labels(labels)

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
