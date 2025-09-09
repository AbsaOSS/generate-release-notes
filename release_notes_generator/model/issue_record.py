"""
A module that defines the IssueRecord class, which represents an issue record in the release notes.
"""

import re
from typing import Optional, Any

from github.Commit import Commit
from github.Issue import Issue
from github.PullRequest import PullRequest

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.record import Record


class IssueRecord(Record):
    """
    A class used to represent an issue record in the release notes.
    Inherits from Record and provides additional functionality specific to issues.
    """

    ISSUE_STATE_CLOSED = "closed"
    ISSUE_STATE_OPEN = "open"
    ISSUE_STATE_ALL = "all"

    def __init__(self, issue: Issue, skip: bool = False):
        super().__init__(skip=skip)

        self._issue: Issue = issue
        self._issue_type: Optional[str] = None

        if issue is not None and issue.type is not None:
            self._issue_type = issue.type.name

        self._labels = {label.name for label in self._issue.get_labels()}

        self._pull_requests: dict[int, PullRequest] = {}
        self._commits: dict[int, dict[str, Commit]] = {}

    # properties - override Record properties

    @property
    def record_id(self) -> int | str:
        return self._issue.number

    @property
    def is_closed(self) -> bool:
        return self._issue.state == self.ISSUE_STATE_CLOSED

    @property
    def is_open(self) -> bool:
        return self._issue.state == self.ISSUE_STATE_OPEN

    @property
    def authors(self) -> list[str]:
        if not self._issue or not self._issue.user:
            return []
        return [f"@{self._issue.user.login}"]

    # properties - specific to IssueRecord

    @property
    def issue(self) -> Issue:
        """
        Gets the issue associated with the record.
        Returns: The issue associated with the record.
        """
        return self._issue

    @property
    def issue_type(self) -> Optional[str]:
        """
        Gets the type of the issue.
        Returns:
            str: The type of the issue.
        """
        return self._issue_type

    # methods - override Record methods

    def to_chapter_row(self) -> str:
        super().to_chapter_row()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""
        format_values: dict[str, Any] = {}

        # collect format values
        format_values["number"] = f"#{self._issue.number}"
        format_values["title"] = self._issue.title
        list_pr_links = self.get_pr_links()
        if len(list_pr_links) > 0:
            format_values["pull-requests"] = ", ".join(list_pr_links)
        else:
            format_values["pull-requests"] = ""
        format_values["authors"] = self.authors if self.authors is not None else ""
        # contributors are not used in IssueRecord, so commented out for now
        # format_values["contributors"] = self.contributors if self.contributors is not None else ""

        row = f"{row_prefix}" + ActionInputs.get_row_format_issue().format(**format_values)

        if self.contains_release_notes():
            row = f"{row}\n{self.get_rls_notes()}"

        return row

    def get_rls_notes(self, line_marks: Optional[list[str]] = None) -> str:
        release_notes = ""
        detection_pattern = ActionInputs.get_release_notes_title()

        if line_marks is None:
            line_marks = self.RELEASE_NOTE_LINE_MARKS

        # default detection regex
        detection_regex = re.compile(detection_pattern)

        # Code Rabbit detection regex
        cr_active: bool = ActionInputs.is_coderabbit_support_active()

        # Get release notes from Issue
        if self._issue.body and detection_regex.search(self._issue.body):
            release_notes += self._get_rls_notes_default(self._issue, line_marks, detection_regex)

        # Iterate over all PRs
        for pull in self._pull_requests.values():
            if pull.body and detection_regex.search(pull.body):
                release_notes += self._get_rls_notes_default(pull, line_marks, detection_regex)
            elif pull.body and cr_active:
                cr_detection_regex: re.Pattern[Any] = re.compile(ActionInputs.get_coderabbit_release_notes_title())

                if cr_detection_regex.search(pull.body):
                    release_notes += self._get_rls_notes_code_rabbit(pull, line_marks, cr_detection_regex)

        # Return the concatenated release notes
        return release_notes.rstrip()

    # methods - specific to IssueRecord

    def get_pull_request(self, number: int) -> Optional[PullRequest]:
        """
        Gets the pull request by its number.
        Parameters:
            number (int): The number of the pull request.
        Returns:
            Optional[PullRequest]: The pull request or None if not found.
        """
        if number in self._pull_requests:
            return self._pull_requests[number]
        return None

    def get_commit(self, pr_number: int, commit_sha: str) -> Optional[Commit]:
        """
        Gets the commit by its number.
        Parameters:
             pr_number (int): The number of the pull request.
             commit_sha (str): The commit sha.
        Returns:
            Optional[Commit]: The commit or None if not found.
        """
        if pr_number in self._pull_requests:
            pr_commits = self._commits.get(pr_number)
            if pr_commits and commit_sha in pr_commits:
                return pr_commits[commit_sha]
        return None

    def get_pull_request_numbers(self) -> list[int]:
        """
        Returns a list of pull request numbers.
        Returns:
            list[int]: A list of pull request numbers.
        """
        return [pull.number for pull in self._pull_requests.values()]

    def register_pull_request(self, pull: PullRequest) -> None:
        """
        Registers a Pull Request associated with the issue.
        Parameters:
            pull (PullRequest): The pull request record to register.
        Returns: None
        """
        self._pull_requests[pull.number] = pull
        self._labels.update({label.name for label in pull.get_labels()})

    def register_commit(self, pull: PullRequest, commit: Commit) -> None:
        """
        Registers a Commit associated with the issue.
        Parameters:
            pull (PullRequest): The pull request record to register.
            commit (Commit): The commit record to register.
        Returns: None
        """
        if pull.number not in self._pull_requests:
            self.register_pull_request(pull)

        if pull.number not in self._commits:
            self._commits[pull.number] = {}

        self._commits[pull.number][commit.sha] = commit

    def pull_requests_count(self) -> int:
        """
        Returns the number of pull requests associated with the issue.
        Returns:
            int: The number of pull requests associated with the issue.
        """
        return len(self._pull_requests)

    def get_pr_links(self) -> list[str]:
        """
        Returns a list of pull request links associated with the issue.
        Returns:
            list[str]: A list of pull request links associated with the issue.
        """
        if len(self._pull_requests) == 0:
            return []

        template = "#{number}"
        res = [template.format(number=pull.number) for pull in self._pull_requests.values()]

        return res

    def _get_rls_notes_default(
        self, record: Issue | PullRequest, line_marks: list[str], detection_regex: re.Pattern[str]
    ) -> str:
        """
        Extracts release notes from the pull request body based on the provided line marks and detection regex.
        Parameters:
            record (Issue or PullRequest): The issue or pull request from which to extract release notes.
            line_marks (list[str]): A list of characters that indicate the start of a release notes section.
            detection_regex (re.Pattern[str]): A regex pattern to detect the start of the release notes section.
        Returns:
            str: The extracted release notes as a string. If no release notes are found, returns an empty string.
        """
        # TODO - this code will be changes soon, there is wish from project to manage different release notes
        match record.body:
            case None | "":
                return ""
            case str() as body:
                lines = body.splitlines()

        release_notes_lines = []

        found_section = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if not found_section:
                if detection_regex.search(line):
                    found_section = True
                continue

            if stripped[0] in line_marks:
                release_notes_lines.append(f"  {line.rstrip()}")
            else:
                break

        return "\n".join(release_notes_lines) + ("\n" if release_notes_lines else "")

    def _get_rls_notes_code_rabbit(
        self, pull: PullRequest, line_marks: list[str], cr_detection_regex: re.Pattern[str]
    ) -> str:
        """
        Extracts release notes from a pull request body formatted for Code Rabbit.
        Parameters:
            pull (PullRequestRecord): The pull request from which to extract release notes.
            line_marks (list[str]): A list of characters that indicate the start of a release notes section.
            cr_detection_regex (re.Pattern[str]): A regex pattern to detect the start of the Code
        Returns:
            str: The extracted release notes as a string. If no release notes are found, returns an empty string.
        """
        # TODO - this code will be changes soon, there is wish from project to manage different release notes
        if not pull.body:
            return ""

        lines = pull.body.splitlines()
        ignore_groups: list[str] = ActionInputs.get_coderabbit_summary_ignore_groups()
        release_notes_lines = []

        inside_section = False
        skipping_group = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if not inside_section:
                if cr_detection_regex.search(line):
                    inside_section = True
                continue

            if inside_section:
                # Check if this is a bold group heading, e.g.
                first_char = stripped[0]
                if first_char in line_marks and "**" in stripped:
                    # Group heading – check if it should be skipped
                    group_name = stripped.split("**")[1]
                    skipping_group = any(group.lower() == group_name.lower() for group in ignore_groups)
                    continue

                if skipping_group and any(line.startswith(f"  {ch} ") for ch in line_marks):
                    continue

                if first_char in line_marks and any(line.startswith(f"  {ch} ") for ch in line_marks):
                    release_notes_lines.append(line.rstrip())
                else:
                    break

        return "\n".join(release_notes_lines) + ("\n" if release_notes_lines else "")
