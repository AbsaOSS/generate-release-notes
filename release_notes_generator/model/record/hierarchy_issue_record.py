#
# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
A module that defines the HierarchyIssueRecord class for hierarchical issue rendering.
"""

import logging
from github.Issue import Issue

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.sub_issue_record import SubIssueRecord
from release_notes_generator.utils.record_utils import format_row_with_suppression

logger = logging.getLogger(__name__)


class HierarchyIssueRecord(IssueRecord):
    """
    A class used to represent an hierarchy issue record in the release notes.
    Inherits from IssueRecord and provides additional functionality specific to issues.
    """

    def __init__(self, issue: Issue, issue_labels: list[str] | None = None, skip: bool = False):
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

    @property
    def progress(self) -> str:
        """
        The sub-issue completion count for this hierarchy node as 'X/Y done'.

        Returns:
            '' when this node has no direct sub-issues; otherwise 'X/Y done'
            counting direct children only (sub-issues + sub-hierarchy-issues, no recursion).
            Note: adjacent delimiter characters are not stripped when empty.
        """
        total = len(self._sub_issues) + len(self._sub_hierarchy_issues)
        if total == 0:
            return ""
        closed = sum(1 for s in self._sub_issues.values() if s.is_closed)
        closed += sum(1 for s in self._sub_hierarchy_issues.values() if s.is_closed)
        return f"{closed}/{total} done"

    @property
    def developers(self) -> list[str]:
        """Unique, sorted list of developers across this issue and all descendants."""
        issue = self._issue
        if not issue:
            return []

        devs = set()

        # Assignees (main implementers)
        for assignee in self.assignees:
            devs.add(f"{assignee}")

        # hierarchy sub-issues
        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            for dev in sub_hierarchy_issue.developers:
                devs.add(dev)

        # sub-issues
        for sub_issue in self._sub_issues.values():
            for dev in sub_issue.developers:
                devs.add(dev)

        return sorted(devs)

    def pull_requests_count(self) -> int:
        """Return the total number of pull requests across this issue and all descendants."""
        count = super().pull_requests_count()

        for sub_issue in self._sub_issues.values():
            if sub_issue.is_cross_repo:
                count += 1
            else:
                count += sub_issue.pull_requests_count()

        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            if sub_hierarchy_issue.is_cross_repo:
                count += 1
            else:
                count += sub_hierarchy_issue.pull_requests_count()

        return count

    def contains_change_increment(self) -> bool:
        """
        Returns True only when this hierarchy sub-tree has at least one closed descendant with a change.

        A closed descendant with a PR (or a cross-repo placeholder) is the only evidence of finished
        work that belongs in release notes.  Open sub-issues whose PRs have not yet been merged must
        not cause the parent to appear in the output.
        """
        if self.is_cross_repo:
            return True

        # Direct PRs attached to this hierarchy issue itself (IssueRecord level, no sub-tree)
        if super().pull_requests_count() > 0:
            return True

        # Only closed leaf sub-issues contribute; recurse to check their own PRs/cross-repo flag
        for sub_issue in self._sub_issues.values():
            if sub_issue.is_closed and sub_issue.contains_change_increment():
                return True

        # Recurse into sub-hierarchy-issues; the same closed-descendant rule applies at every level
        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            if sub_hierarchy_issue.contains_change_increment():
                return True

        return False

    def get_labels(self) -> list[str]:
        """Return all labels from this issue, its sub-issues, sub-hierarchy-issues, and attached PRs."""
        labels: set[str] = set()
        labels.update(label.name for label in self._issue.get_labels())

        for sub_issue in self._sub_issues.values():
            labels.update(sub_issue.labels)

        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            labels.update(sub_hierarchy_issue.get_labels())

        for pull in self._pull_requests.values():
            labels.update(label.name for label in pull.get_labels())

        return list(labels)

    def has_matching_labels(self, label_filter: list[str]) -> bool:
        """Check if this hierarchy issue or any descendant has labels matching the filter.

        Parameters:
            label_filter: Labels to check against.

        Returns:
            True if this record or any descendant has at least one matching label.
        """
        if any(lbl in label_filter for lbl in self.labels):
            return True
        for sub_issue in self._sub_issues.values():
            if any(lbl in label_filter for lbl in sub_issue.labels):
                return True
        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            if sub_hierarchy_issue.has_matching_labels(label_filter):
                return True
        return False

    def has_unmatched_descendants(self, all_super_labels: list[str]) -> bool:
        """Check if any descendant does NOT match any label in the combined super-chapter label set.

        Parameters:
            all_super_labels: Union of all super-chapter labels.

        Returns:
            True if at least one descendant has no label intersecting *all_super_labels*.
        """
        for sub_issue in self._sub_issues.values():
            if not any(lbl in all_super_labels for lbl in sub_issue.labels):
                return True
        for sub_hierarchy_issue in self._sub_hierarchy_issues.values():
            if sub_hierarchy_issue.has_unmatched_descendants(all_super_labels):
                return True
            # A leaf HierarchyIssueRecord (no children of its own) is unmatched if
            # its own labels don't intersect the SC set.  Intermediate nodes are
            # pure containers — their own organisational labels are irrelevant.
            is_leaf = not sub_hierarchy_issue.sub_issues and not sub_hierarchy_issue.sub_hierarchy_issues
            if is_leaf and not any(lbl in all_super_labels for lbl in sub_hierarchy_issue.labels):
                return True
        return False

    # methods - override ancestor methods

    def _collect_format_values(self) -> dict[str, str]:
        """Collect template substitution values for the hierarchy issue row format string."""
        format_values: dict[str, str] = {}
        format_values["number"] = f"#{self.issue.number}"
        format_values["title"] = self.issue.title
        format_values["author"] = self.author
        format_values["assignees"] = ", ".join(self.assignees)
        format_values["developers"] = ", ".join(self.developers)
        format_values["type"] = self.issue_type if self.issue_type is not None else ""
        format_values["progress"] = self.progress
        list_pr_links = self.get_pr_links()
        format_values["pull-requests"] = ", ".join(list_pr_links) if list_pr_links else ""
        return format_values

    def _append_release_notes_block(self, row: str) -> str:
        """Append an indented Release Notes section to *row* when present."""
        if not self.contains_release_notes():
            return row
        sub_indent: str = "  " * (self._level + 1)
        row = f"{row}\n{sub_indent}- _Release Notes_:"
        rls_block = "\n".join(f"{sub_indent}{line}" if line else "" for line in self.get_rls_notes().splitlines())
        return f"{row}\n{rls_block}"

    def _build_open_sub_hierarchy_row(
        self,
        sub_hierarchy_issue: "HierarchyIssueRecord",
        label_filter: list[str] | None,
        exclude_labels: list[str] | None,
    ) -> str:
        """Render an open sub-hierarchy issue row and insert the open-hierarchy icon after the list marker.

        Highlight open children under a closed parent to signal incomplete work.
        Insert icon after the list marker ('- ') to preserve Markdown structure,
        and skip insertion entirely when the icon is empty.
        """
        sub_row = sub_hierarchy_issue.to_chapter_row(label_filter=label_filter, exclude_labels=exclude_labels)
        icon = ActionInputs.get_open_hierarchy_sub_issue_icon()
        if not icon:
            return sub_row
        header_line, newline, remaining_lines = sub_row.partition("\n")
        header_text = header_line.lstrip()
        spaces = header_line[: len(header_line) - len(header_text)]
        if header_text.startswith("- "):
            marker, content = "- ", header_text[2:]
        else:
            marker, content = "", header_text
        return f"{spaces}{marker}{icon} {content}{newline}{remaining_lines}"

    def _append_sub_hierarchy_rows(
        self,
        row: str,
        label_filter: list[str] | None,
        exclude_labels: list[str] | None,
    ) -> str:
        """Append rendered rows for all qualifying sub-hierarchy issues to *row*."""
        for sub_hierarchy_issue in sorted(self._sub_hierarchy_issues.values(), key=lambda r: r.issue.number):
            logger.debug("Rendering sub-hierarchy issue row for #%s", sub_hierarchy_issue.issue.number)
            if label_filter and not sub_hierarchy_issue.has_matching_labels(label_filter):
                continue
            if (
                exclude_labels
                and not sub_hierarchy_issue.has_unmatched_descendants(exclude_labels)
                and sub_hierarchy_issue.has_matching_labels(exclude_labels)
            ):
                continue
            if self.is_open and not sub_hierarchy_issue.contains_change_increment():
                continue
            # Closed parent: render all sub-hierarchy issues regardless of state or change increment
            logger.debug("Rendering sub-hierarchy issue #%s", sub_hierarchy_issue.issue.number)
            if self.is_closed and sub_hierarchy_issue.is_open:
                sub_row = self._build_open_sub_hierarchy_row(sub_hierarchy_issue, label_filter, exclude_labels)
            else:
                sub_row = sub_hierarchy_issue.to_chapter_row(label_filter=label_filter, exclude_labels=exclude_labels)
            row = f"{row}\n{sub_row}"
        return row

    def _append_sub_issue_rows(
        self,
        row: str,
        label_filter: list[str] | None,
        exclude_labels: list[str] | None,
    ) -> str:
        """Append rendered rows for all qualifying direct sub-issues to *row*."""
        if not self._sub_issues:
            # No sub-issues: violations of hierarchy are reported in service chapters (no data loss)
            return row
        sub_indent = "  " * (self._level + 1)
        for sub_issue in sorted(self._sub_issues.values(), key=lambda r: r.issue.number):
            logger.debug("Rendering sub-issue row for issue #%s", sub_issue.issue.number)
            if label_filter and not any(lbl in label_filter for lbl in sub_issue.labels):
                continue
            if exclude_labels and any(lbl in exclude_labels for lbl in sub_issue.labels):
                continue
            if self.is_open:
                if sub_issue.is_open:
                    continue  # only closed issues are reported in release notes
                if not sub_issue.contains_change_increment():
                    continue  # skip sub-issues without change increment
            # Closed parent: render all sub-issues regardless of state or change increment
            logger.debug("Rendering sub-issue #%s", sub_issue.issue.number)
            open_icon_prefix = ""
            if self.is_closed and sub_issue.is_open:
                # Highlight open children under a closed parent to signal incomplete work
                open_icon_prefix = ActionInputs.get_open_hierarchy_sub_issue_icon() + " "
            sub_issue_block = "- " + open_icon_prefix + sub_issue.to_chapter_row()
            ind_child_block = "\n".join(f"{sub_indent}{line}" if line else "" for line in sub_issue_block.splitlines())
            row = f"{row}\n{ind_child_block}"
        return row

    def to_chapter_row(
        self,
        add_into_chapters: bool = True,
        label_filter: list[str] | None = None,
        exclude_labels: list[str] | None = None,
    ) -> str:
        logger.debug("Rendering hierarchy issue row for issue #%s", self.issue.number)
        row_prefix = f"{ActionInputs.get_duplicity_icon()} " if self.chapter_presence_count() > 1 else ""
        indent: str = "  " * self._level
        if self._level > 0:
            indent += "- "
        row = f"{indent}{row_prefix}" + format_row_with_suppression(
            ActionInputs.get_row_format_hierarchy_issue(), self._collect_format_values()
        )
        row = self._append_release_notes_block(row)
        row = self._append_sub_hierarchy_rows(row, label_filter, exclude_labels)
        row = self._append_sub_issue_rows(row, label_filter, exclude_labels)
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
