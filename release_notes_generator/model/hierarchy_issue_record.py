"""
A module that defines the IssueRecord class, which represents an issue record in the release notes.
"""
import logging
from functools import lru_cache
from typing import Optional, Any
from github.Issue import Issue
from github.PullRequest import PullRequest

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.issue_record import IssueRecord

logger = logging.getLogger(__name__)


class HierarchyIssueRecord(IssueRecord):
    """
    A class used to represent an hierarchy issue record in the release notes.
    Inherits from IssueRecord and provides additional functionality specific to issues.
    """

    def __init__(self, issue: Issue, issue_type: Optional[str] = None, skip: bool = False, level: int = 0):
        super().__init__(issue, issue_type, skip=skip)

        self.type: Optional[str] = None
        self._level: int = level
        self._sub_issues: dict[int, IssueRecord] = {}  # sub-issues - no more sub-issues
        self._sub_hierarchy_issues: dict[int, HierarchyIssueRecord] = {}  # sub-hierarchy issues - have sub-issues

    @lru_cache(maxsize=None)
    def get_labels(self) -> set[str]:
        labels = set()
        labels.update(self._issue.get_labels())

        for sub_issue in self._sub_issues.values():
            labels.update(sub_issue.labels)

        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            labels.update(sub_hierarchy_issue.labels)

        for pull in self._pull_requests.values():
            labels.update(pull.get_labels())

        return labels

    # methods - override ancestor methods
    def to_chapter_row(self, add_into_chapters: bool = False) -> str:
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
            sub_indent = "  " * (self._level + 2)
            rls_block = "\n".join(f"{sub_indent}{line}" if line else "" for line in self.get_rls_notes().splitlines())
            row = f"{row}\n{rls_block}"

        # add sub-hierarchy issues
        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            row = f"{row}\n{sub_hierarchy_issue.to_chapter_row()}"

        # add sub-issues
        if len(self._sub_issues) > 0:
            sub_indent = "  " * (self._level + 1)
            for sub_issue in self._sub_issues.values():
                if sub_issue.is_open:
                    continue    # only closed issues are reported in release notes

                sub_issue_block = "- " + sub_issue.to_chapter_row()
                ind_child_block = "\n".join(
                    f"{sub_indent}{line}" if line else "" for line in sub_issue_block.splitlines()
                )
                row = f"{row}\n{ind_child_block}"
        # else: this will be reported in service chapters as violation of hierarchy in this initial version
        # No data loss - in service chapter there will be all detail not presented here

        return row

    def register_hierarchy_issue(self, issue: Issue) -> "HierarchyIssueRecord":
        """
        Registers a sub-hierarchy issue.

        Parameters:
            issue: The sub-hierarchy issue to register.
        Returns:
            The registered sub-hierarchy issue record.
        """
        sub_rec = HierarchyIssueRecord(issue=issue, issue_type=issue.type.name, level=self._level + 1)
        self._sub_hierarchy_issues[issue.number] = sub_rec
        logger.debug("Registered sub-hierarchy issue '%d' to parent issue '%d'", issue.number, self.issue.number)
        return sub_rec

    def register_issue(self, issue: Issue) -> IssueRecord:
        """
        Registers a sub-issue.

        Parameters:
            issue: The sub-issue to register.
        Returns:
            The registered sub-issue record.
        """
        sub_rec = IssueRecord(issue=issue)
        self._sub_issues[issue.number] = sub_rec
        logger.debug("Registered sub-issue '%d' to parent issue '%d'", issue.number, self.issue.number)
        return sub_rec

    def register_pull_request_in_hierarchy(self, issue_number: int, pull: PullRequest) -> None:
        if issue_number in self._sub_issues.keys():
            self._sub_issues[issue_number].register_pull_request(pull)
            return

        if issue_number in self._sub_hierarchy_issues.keys():
            self._sub_hierarchy_issues[issue_number].register_pull_request(pull)
            return

    def find_issue(self, issue_number: int) -> Optional["IssueRecord"]:
        if issue_number in self._sub_issues.keys():
            return self._sub_issues[issue_number]
        elif issue_number in self._sub_hierarchy_issues.keys():
            return self._sub_hierarchy_issues[issue_number]
        else:
            for rec in self._sub_hierarchy_issues.values():
                found = rec.find_issue(issue_number)
                if found is not None:
                    return found
        return None
