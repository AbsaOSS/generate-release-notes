"""
A module that defines the IssueRecord class, which represents an issue record in the release notes.
"""

import logging
from typing import Optional

from github.Issue import SubIssue, Issue

from release_notes_generator.model.issue_record import IssueRecord

logger = logging.getLogger(__name__)


class SubIssueRecord(IssueRecord):
    """
    A class used to represent an issue record in the release notes.
    Inherits from Record and provides additional functionality specific to issues.
    """

    def __init__(self, sub_issue: SubIssue | Issue, issue_labels: Optional[list[str]] = None, skip: bool = False):
        super().__init__(sub_issue, issue_labels, skip)

    # properties - override IssueRecord properties

    @property
    def issue(self) -> SubIssue:
        """
        Gets the issue associated with the record.
        Returns: The issue associated with the record.
        """
        if not isinstance(self._issue, SubIssue):
            raise TypeError("SubIssueRecord.issue is expected to be a SubIssue")
        return self._issue

    # properties - specific to IssueRecord
