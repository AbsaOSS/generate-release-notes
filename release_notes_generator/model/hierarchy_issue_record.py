"""
A module that defines the HierarchyIssueRecord class for hierarchical issue rendering.
"""

import logging
from typing import Optional, Any
from github.Issue import Issue

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.sub_issue_record import SubIssueRecord

logger = logging.getLogger(__name__)


class HierarchyIssueRecord(IssueRecord):
    """
    A class used to represent an hierarchy issue record in the release notes.
    Inherits from IssueRecord and provides additional functionality specific to issues.
    """

    def __init__(self, issue: Issue, issue_labels: Optional[list[str]] = None, skip: bool = False):
        super().__init__(issue, issue_labels, skip)

        self._level: int = 0
        self._sub_issues: dict[str, SubIssueRecord] = {}
        self._sub_hierarchy_issues: dict[str, "HierarchyIssueRecord"] = {}

    @property
    def level(self) -> int:
        """
        The level of the hierarchy issue.
        """
        return self._level

    @level.setter
    def level(self, value: int) -> None:
        """
        Sets the level of the hierarchy issue.

        Parameters:
            value (int): The level of the hierarchy issue.
        """
        self._level = value

    @property
    def sub_issues(self):
        """
        The list of sub-issues for the hierarchy issue.
        """
        return self._sub_issues

    @property
    def sub_hierarchy_issues(self):
        """
        The list of sub-hierarchy issues for the hierarchy issue.
        """
        return self._sub_hierarchy_issues

    def pull_requests_count(self) -> int:
        count = super().pull_requests_count()

        for sub_issue in self._sub_issues.values():
            count += sub_issue.pull_requests_count()

        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            count += sub_hierarchy_issue.pull_requests_count()

        return count

    def get_labels(self) -> list[str]:
        labels: set[str] = set()
        labels.update(label.name for label in self._issue.get_labels())

        for sub_issue in self._sub_issues.values():
            labels.update(sub_issue.labels)

        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            labels.update(sub_hierarchy_issue.labels)

        for pull in self._pull_requests.values():
            labels.update(label.name for label in pull.get_labels())

        return list(labels)

    # methods - override ancestor methods
    def to_chapter_row(self, add_into_chapters: bool = True) -> str:
        if add_into_chapters:
            self.added_into_chapters()
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.present_in_chapters() > 1 else ""
        format_values: dict[str, Any] = {}

        # collect format values
        format_values["number"] = f"#{self.issue.number}"
        format_values["title"] = self.issue.title
        if self.issue_type is not None:
            format_values["type"] = self.issue_type
        else:
            format_values["type"] = "None"

        list_pr_links = self.get_pr_links()
        if len(list_pr_links) > 0:
            format_values["pull-requests"] = ", ".join(list_pr_links)
        else:
            format_values["pull-requests"] = ""

        indent: str = "  " * self._level
        if self._level > 0:
            indent += "- "

        # create first issue row
        row = f"{indent}{row_prefix}" + ActionInputs.get_row_format_hierarchy_issue().format(**format_values)

        # add extra section with release notes if detected
        if self.contains_release_notes():
            sub_indent: str = "  " * (self._level + 1)
            row = f"{row}\n{sub_indent}- _Release Notes_:"
            rls_block = "\n".join(f"{sub_indent}{line}" if line else "" for line in self.get_rls_notes().splitlines())
            row = f"{row}\n{rls_block}"

        # add sub-hierarchy issues
        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            if sub_hierarchy_issue.contains_change_increment():
                row = f"{row}\n{sub_hierarchy_issue.to_chapter_row()}"

        # add sub-issues
        if len(self._sub_issues) > 0:
            sub_indent = "  " * (self._level + 1)
            for sub_issue in self._sub_issues.values():
                if sub_issue.is_open:
                    continue  # only closed issues are reported in release notes

                if not sub_issue.contains_change_increment():
                    continue  # skip sub-issues without change increment

                sub_issue_block = "- " + sub_issue.to_chapter_row()
                ind_child_block = "\n".join(
                    f"{sub_indent}{line}" if line else "" for line in sub_issue_block.splitlines()
                )
                row = f"{row}\n{ind_child_block}"
        # else: this will be reported in service chapters as violation of hierarchy in this initial version
        # No data loss - in service chapter there will be all detail not presented here

        return row

    def order_hierarchy_levels(self, level: int = 0) -> None:
        """
        Orders the hierarchy levels of the issue and its sub-issues recursively.

        Parameters:
            level (int): The starting level for the hierarchy. Default is 0.

        Returns:
            None
        """
        self._level = level
        for sub_hierarchy_record in self.sub_hierarchy_issues.values():
            sub_hierarchy_record.order_hierarchy_levels(level=level + 1)
