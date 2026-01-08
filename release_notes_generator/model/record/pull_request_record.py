"""
A module that defines the PullRequestRecord class, which represents a pull request record in the release notes.
"""

import re
from typing import Optional, Any

from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.record.record import Record
from release_notes_generator.utils.pull_request_utils import extract_issue_numbers_from_body
from release_notes_generator.utils.record_utils import get_rls_notes_default, get_rls_notes_code_rabbit


class PullRequestRecord(Record):
    """
    A class used to represent a pull request record in the release notes.
    Inherits from Record and provides additional functionality specific to pull requests.
    """

    PR_STATE_CLOSED = "closed"
    PR_STATE_OPEN = "open"

    def __init__(self, pull: PullRequest, repo: Repository, labels: Optional[list[str]] = None, skip: bool = False):
        super().__init__(labels, skip)

        self._home_repository: Repository = repo
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
    def author(self) -> str:
        if not self._pull_request or not self._pull_request.user:
            return ""
        return f"@{self._pull_request.user.login}"

    @property
    def assignees(self) -> list[str]:
        assignees = set()

        for assignee in self._pull_request.assignees:
            assignees.add(f"@{assignee.login}")

        return sorted(assignees)

    @property
    def developers(self) -> list[str]:
        devs = set()

        # Assignees (main implementers)
        for assignee in self.assignees:
            devs.add(f"{assignee}")

        # Linked PR authors (people who created PRs closing this issue)
        for _cid, commit in self._commits.items():
            if commit.author and getattr(commit.author, "login", None):
                devs.add(f"@{commit.author.login}")

        return sorted(devs)

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
        # TODO - fix in issue #76
        if not self._pull_request:
            return []

        return []

    # methods - override Record methods

    def get_labels(self) -> list[str]:
        self._labels = [label.name for label in list(self._pull_request.get_labels())]
        return self.labels

    def to_chapter_row(self, add_into_chapters: bool = True) -> str:
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.chapter_presence_count() > 1 else ""
        format_values: dict[str, Any] = {}

        # collecting values for formatting
        format_values["number"] = f"#{self._pull_request.number}"
        format_values["title"] = self._pull_request.title
        format_values["author"] = self.author
        format_values["assignees"] = ", ".join(self.assignees)
        format_values["developers"] = ", ".join(self.developers)

        # Not supported yet - TODO - spend time to research
        # format_values["contributors"] = self.contributors

        pr_prefix = "PR: " if ActionInputs.get_row_format_link_pr() else ""
        row = f"{row_prefix}{pr_prefix}" + ActionInputs.get_row_format_pr().format(**format_values)

        if self.contains_release_notes():
            row = f"{row}\n{self.get_rls_notes()}"
        return row

    def contains_change_increment(self) -> bool:
        return True

    def get_rls_notes(self, line_marks: Optional[list[str]] = None) -> str:
        release_notes = ""
        detection_regex, line_marks, cr_active = self._get_rls_notes_setup(line_marks)

        if self._pull_request.body and detection_regex.search(self._pull_request.body):
            release_notes += get_rls_notes_default(self._pull_request.body, line_marks, detection_regex)
        elif self._pull_request.body and cr_active:
            cr_detection_regex: re.Pattern[Any] = re.compile(ActionInputs.get_coderabbit_release_notes_title())
            if cr_detection_regex.search(self._pull_request.body):
                release_notes += get_rls_notes_code_rabbit(self._pull_request.body, line_marks, cr_detection_regex)

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
        return len(extract_issue_numbers_from_body(self._pull_request, self._home_repository)) > 0
