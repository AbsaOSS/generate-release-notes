"""
A module that defines the IssueRecord class, which represents an issue record in the release notes.
"""

import logging
from typing import Optional, cast

from github.Commit import Commit
from github.Issue import SubIssue, Issue
from github.PullRequest import PullRequest

from release_notes_generator.model.issue_record import IssueRecord

logger = logging.getLogger(__name__)


class SubIssueRecord(IssueRecord):
    """
    A class used to represent an issue record in the release notes.
    Inherits from Record and provides additional functionality specific to issues.
    """

    def __init__(self, sub_issue: SubIssue | Issue, issue_labels: Optional[list[str]] = None, skip: bool = False):
        super().__init__(sub_issue, issue_labels, skip)

        self._labels = issue_labels if issue_labels is not None else []

        self._pull_requests: dict[int, PullRequest] = {}
        self._commits: dict[int, dict[str, Commit]] = {}

    # properties - override IssueRecord properties

    @property
    def issue(self) -> SubIssue:
        """
        Gets the issue associated with the record.
        Returns: The issue associated with the record.
        """
        return cast(SubIssue, self._issue)

    # properties - specific to IssueRecord
