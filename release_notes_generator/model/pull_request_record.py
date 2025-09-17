"""
A module that defines the PullRequestRecord class, which represents a pull request record in the release notes.
"""

import re
from typing import Optional, Any

from github.Commit import Commit
from github.PullRequest import PullRequest

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.record import Record


class PullRequestRecord(Record):
    """
    A class used to represent a pull request record in the release notes.
    Inherits from Record and provides additional functionality specific to pull requests.
    """

    PR_STATE_CLOSED = "closed"
    PR_STATE_OPEN = "open"

    def __init__(self, pull: PullRequest, labels: Optional[list[str]] = None, skip: bool = False):
        super().__init__(labels, skip)

        self._pull_request: PullRequest = pull
        self._commits: dict[str, Commit] = {}

    # properties - override Record properties

    @property
    def record_id(self) -> int | str:
        return self._pull_request.number

    @property
    def is_closed(self) -> bool:
        return (
            self._pull_request.state == self.PR_STATE_CLOSED
            and self._pull_request.merged_at is None
            and self._pull_request.closed_at is not None
        )

    @property
    def is_open(self) -> bool:
        return self._pull_request.state == self.PR_STATE_OPEN

    @property
    def authors(self) -> list[str]:
        if not self._pull_request or not self._pull_request.user:
            return []
        return [f"@{self._pull_request.user.login}"]

    # properties - specific to PullRequestRecord

    @property
    def is_merged(self) -> bool:
        """
        Checks if the pull request is a merged pull request.
        Returns:
            bool: True if the pull request is merged, False otherwise.
        """
        return (
            self._pull_request.state == self.PR_STATE_CLOSED
            and self._pull_request.merged_at is not None
            and self._pull_request.closed_at is not None
        )

    @property
    def pull_request(self) -> PullRequest:
        """
        Gets the pull request associated with the record.
        Returns: The pull request associated with the record.
        """
        return self._pull_request

    @property
    def contributors(self) -> list[str]:
        """
        Gets the GitHub usernames of all contributors to the pull request.
        Returns:
            list[str]: A sorted list of GitHub usernames of contributors, excluding the main author.
        """
        if not self._pull_request:
            return []

        return []

        # TODO - contributors have to be managed in future, make a research if get_commit can return some
        #  new information in compare to mined ones
        # Get unique contributors from commits
        contributors = set()
        # for commit in self._pull_request.get_commits():
        #     if commit.author and commit.author.login:
        #         contributors.add(f"@{commit.author.login}")
        #
        # # Remove the main author if they're also in contributors
        # if self._pull_request.user and self._pull_request.user.login:
        #     author_name = f"@{self._pull_request.user.login}"
        #     if author_name in contributors:
        #         contributors.remove(author_name)
        #
        # return sorted(list(contributors))

    # methods - override Record methods

    def get_labels(self) -> list[str]:
        return [label.name for label in self._pull_request.get_labels()]

    def to_chapter_row(self, add_into_chapters: bool = True) -> str:
        if add_into_chapters:
            self.added_into_chapters()

        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""
        format_values: dict[str, Any] = {}

        # collecting values for formatting
        format_values["number"] = f"#{self._pull_request.number}"
        format_values["title"] = self._pull_request.title
        format_values["authors"] = self.authors if self.authors is not None else ""
        format_values["contributors"] = self.contributors

        pr_prefix = "PR: " if ActionInputs.get_row_format_link_pr() else ""
        row = f"{row_prefix}{pr_prefix}" + ActionInputs.get_row_format_pr().format(**format_values)

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

        if self._pull_request.body and detection_regex.search(self._pull_request.body):
            release_notes += self._get_rls_notes_default(self._pull_request, line_marks, detection_regex)
        elif self._pull_request.body and cr_active:
            cr_detection_regex: re.Pattern[Any] = re.compile(ActionInputs.get_coderabbit_release_notes_title())
            if cr_detection_regex.search(self._pull_request.body):
                release_notes += self._get_rls_notes_code_rabbit(self._pull_request, line_marks, cr_detection_regex)

        # Return the concatenated release notes
        return release_notes.rstrip()

    # methods - specific to PullRequestRecord

    def get_commit(self, sha: str = "0") -> Optional[Commit]:
        """
        Gets the commit by the specified sha.
        Parameters:
            sha (str): The sha of the commit to retrieve.
        Returns:
            Optional[Commit]: None if the commit is not found.
        """
        if sha in self._commits:
            return self._commits[sha]
        return None

    def register_commit(self, commit: Commit) -> None:
        """
        Registers a Commit associated with the Pull Request.
        Parameters:
            commit (Commit): The commit to register.
        Returns: None
        """
        self._commits[commit.sha] = commit

    def is_commit_sha_present(self, sha: str) -> bool:
        """
        Checks if the specified commit SHA is present in the record.
        Parameters:
            sha (str): The commit SHA to check for.
        Returns:
            bool: True if the commit SHA is present, False otherwise.
        """
        return self._pull_request.merge_commit_sha == sha

    def commits_count(self) -> int:
        """
        Returns the number of commits associated with the pull request.
        """
        return len(self._commits)

    def contains_issue_mentions(self) -> bool:
        """
        Checks if the pull request contains issue mentions.

        Returns:
            bool: True if the pull request contains issue mentions, False otherwise.
        """
        # TODO call both and merge solve in issue #153, both: means - check body and call new feature
        # return len(extract_issue_numbers_from_body(self._pulls[0])) > 0
        return False

    def _get_rls_notes_default(self, pull: PullRequest, line_marks: list[str], detection_regex: re.Pattern[str]) -> str:
        """
        Extracts release notes from the pull request body based on the provided line marks and detection regex.
        Parameters:
            pull (PullRequest): The pull request from which to extract release notes.
            line_marks (list[str]): A list of characters that indicate the start of a release notes section.
            detection_regex (re.Pattern[str]): A regex pattern to detect the start of the release notes section.
        Returns:
            str: The extracted release notes as a string. If no release notes are found, returns an empty string.
        """
        # TODO - this code will be changes soon, there is wish from project to manage different release notes
        if not pull.body:
            return ""

        lines = pull.body.splitlines()
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
            pull (PullRequest): The pull request from which to extract release notes.
            line_marks (list[str]): A list of characters that indicate the start of a release notes section.
            cr_detection_regex (re.Pattern[str]): A regex pattern to detect the start of the Code Rabbit release notes
             section.
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
                # Check if this is a bold group heading, e.g., "- **Improvements**"
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
