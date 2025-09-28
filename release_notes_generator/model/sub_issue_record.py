"""
A module for the SubIssueRecord class, which represents a sub-issue record in the release notes.
"""

import logging
from typing import Optional

from github.Issue import SubIssue, Issue

from release_notes_generator.model.issue_record import IssueRecord

logger = logging.getLogger(__name__)


class SubIssueRecord(IssueRecord):
    """
    Represents a sub-issue record in the release notes.
    Inherits from IssueRecord and specializes behavior for sub-issues.
    """

    def __init__(self, sub_issue: SubIssue | Issue, issue_labels: Optional[list[str]] = None, skip: bool = False):
        super().__init__(sub_issue, issue_labels, skip)

    # properties - override IssueRecord properties

    # @property
    # def issue(self) -> SubIssue:
    #     """
    #     Gets the issue associated with the record.
    #     Returns: The issue associated with the record.
    #     """
    #     if not isinstance(self._issue, SubIssue):
    #         raise TypeError("Expected SubIssue")
    #     return self._issue

    # properties - specific to IssueRecord
