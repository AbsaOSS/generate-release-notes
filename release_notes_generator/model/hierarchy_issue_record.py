"""
A module that defines the IssueRecord class, which represents an issue record in the release notes.
"""

import re
from typing import Optional, Any

from github.Commit import Commit
from github.Issue import Issue
from github.PullRequest import PullRequest

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.issue_record import IssueRecord


class HierarchyIssueRecord(IssueRecord):
    """
    A class used to represent an hierarchy issue record in the release notes.
    Inherits from IssueRecord and provides additional functionality specific to issues.
    """

    def __init__(self, issue: Issue, issue_type: Optional[str] = None, skip: bool = False, level: int = 0):
        super().__init__(issue, issue_type, skip=skip)

        self._level: int = level
        self._issues: dict[int, IssueRecord] = {}   # sub-issues
        self._hierarchy_issues: dict[int, HierarchyIssueRecord] = {}    # sub-hierarchy issues

    # methods - override ancestor methods
    def to_chapter_row(self) -> str:
        self.added_into_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""
        format_values: dict[str, Any] = {}

        # collect format values
        format_values["number"] = f"#{self._issue.number}"
        format_values["title"] = self._issue.title
        format_values["type"] = self._issue.type.name

        list_pr_links = self.get_pr_links()
        if len(list_pr_links) > 0:
            format_values["pull-requests"] = ", ".join(list_pr_links)
        else:
            format_values["pull-requests"] = ""

        indent: str = "  " * self._level
        if self._level > 0:
            indent += "- "

        # create first issue row
        # TODO/Another Issue - add new service chapter for:
        #   - hierarchy issue which contains other hierarchy issues and normal issues or PRs
        #   Reason: hierarchy regime should improve readability of complex topics
        row = f"{indent}{row_prefix}" + ActionInputs.get_row_format_hierarchy_issue().format(**format_values)

        # add extra section with release notes if detected
        if self.contains_release_notes():
            sub_indent: str = "  " * (self._level + 1)
            row = f"{row}\n{sub_indent}- _Release Notes_:"
            sub_indent: str = "  " * (self._level + 2)
            rls_block = "\n".join(f"{sub_indent}{line}" if line else "" for line in self.get_rls_notes().splitlines())
            row = f"{row}\n{rls_block}"

        # add sub-hierarchy issues
        for sub_hierarchy_issue in self._hierarchy_issues.values():
            row = f"{row}\n{sub_hierarchy_issue.to_chapter_row()}"

        # add sub-issues
        if len(self._hierarchy_issues) == 0:
            sub_indent: str = "  " * (self._level + 1)
            for sub_issue in self._issues.values():
                sub_issue_block = "- " + sub_issue.to_chapter_row()
                ind_child_block = "\n".join(f"{sub_indent}{line}" if line else "" for line in sub_issue_block.splitlines())
                row = f"{row}\n{ind_child_block}"
        # else: this will be reported in service chapters as violation of hierarchy in this initial version
        # No data loss - in service chapter there will be all detail not presented here

        return row

    def register_hierarchy_issue(self, issue: Issue) -> "HierarchyIssueRecord":
        sub_rec = HierarchyIssueRecord(issue=issue, issue_type=issue.type.name, level=self._level + 1)
        self._hierarchy_issues[issue.number] = sub_rec
        return sub_rec

    def register_issue(self, issue: Issue) -> IssueRecord:
        sub_rec = IssueRecord(issue=issue)
        self._issues[issue.number] = sub_rec
        return sub_rec
