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
This module contains the StatsChapters class which is responsible for rendering
Statistics & Anti-game chapters in the release notes.
"""

import logging
from collections import defaultdict

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.record.pull_request_record import PullRequestRecord
from release_notes_generator.model.record.record import Record
from release_notes_generator.utils.constants import SKIP_RELEASE_NOTES_LABEL_STATS

logger = logging.getLogger(__name__)

NO_AUTHOR = "(no author)"
NO_LABEL = "(no label)"


class StatsChapters:
    """
    Statistics & Anti-game chapters.

    Collects skip-label usage statistics from all records and renders
    four sub-sections as markdown tables.
    """

    def __init__(self, print_empty_chapters: bool = True):
        self.print_empty_chapters = print_empty_chapters

        # Sub-section 1: PR Authors  {author: [total, skipped]}
        self._pr_authors: dict[str, list[int]] = defaultdict(lambda: [0, 0])

        # Sub-section 2: Issue Authors/Assignees  {person: [total, skipped]}
        self._issue_people: dict[str, list[int]] = defaultdict(lambda: [0, 0])

        # Sub-section 3: Issue Labels  {label: [total, skipped]}
        self._issue_labels: dict[str, list[int]] = defaultdict(lambda: [0, 0])

        # Sub-section 4: PR Labels  {label: [total, skipped]}
        self._pr_labels: dict[str, list[int]] = defaultdict(lambda: [0, 0])

        self._has_any_skipped = False

    def populate(self, records: dict[str, Record]) -> None:
        """
        Populate statistics from all records.

        Parameters:
            records: A dictionary of records.
        """
        skip_labels = set(ActionInputs.get_skip_release_notes_labels())

        for _record_id, record in records.items():
            is_skipped = record.skip
            if is_skipped:
                self._has_any_skipped = True

            non_skip_labels = [lbl for lbl in record.labels if lbl not in skip_labels]

            # Sub-section 1: PR Authors
            if isinstance(record, PullRequestRecord):
                author = record.author if record.author else NO_AUTHOR
                self._pr_authors[author][0] += 1
                if is_skipped:
                    self._pr_authors[author][1] += 1

            # Sub-section 2: Issue Authors/Assignees
            if isinstance(record, IssueRecord):
                people: set[str] = set()
                author = record.author if record.author else NO_AUTHOR
                people.add(author)
                for assignee in record.assignees:
                    people.add(assignee)

                for person in people:
                    self._issue_people[person][0] += 1
                    if is_skipped:
                        self._issue_people[person][1] += 1

                # Sub-section 3: Issue Labels
                label_buckets = non_skip_labels if non_skip_labels else [NO_LABEL]
                for bucket in label_buckets:
                    self._issue_labels[bucket][0] += 1
                    if is_skipped:
                        self._issue_labels[bucket][1] += 1

            # Sub-section 4: PR Labels
            if isinstance(record, PullRequestRecord):
                label_buckets = non_skip_labels if non_skip_labels else [NO_LABEL]
                for bucket in label_buckets:
                    self._pr_labels[bucket][0] += 1
                    if is_skipped:
                        self._pr_labels[bucket][1] += 1

    def to_string(self) -> str:
        """
        Render the stats chapter as a markdown string.

        Returns:
            The rendered markdown string, or empty string if nothing to show.
        """
        if not self._has_any_skipped:
            return ""

        sections: list[str] = []

        pr_section = self._render_table(
            "PR Authors",
            ["Author", "Total PRs", "Skipped PRs"],
            self._pr_authors,
        )
        if pr_section:
            sections.append(pr_section)

        issue_section = self._render_table(
            "Issue Authors / Assignees",
            ["Author / Assignee", "Total Issues", "Skipped Issues"],
            self._issue_people,
        )
        if issue_section:
            sections.append(issue_section)

        type_section = self._render_table(
            "Issue Labels",
            ["Label", "Total Issues", "Skipped Issues"],
            self._issue_labels,
        )
        if type_section:
            sections.append(type_section)

        label_section = self._render_table(
            "PR Labels",
            ["Label", "Total PRs", "Skipped PRs"],
            self._pr_labels,
        )
        if label_section:
            sections.append(label_section)

        if not sections:
            return ""

        header = f"### {SKIP_RELEASE_NOTES_LABEL_STATS}"
        return header + "\n" + "\n".join(sections)

    def _render_table(
        self,
        title: str,
        columns: list[str],
        data: dict[str, list[int]],
    ) -> str:
        """
        Render a single sub-section table.

        Parameters:
            title: The sub-section title.
            columns: Column headers [name, total_col, skipped_col].
            data: The data dict {key: [total, skipped]}.

        Returns:
            Rendered markdown or empty string if the sub-section should be omitted.
        """
        if not data:
            return ""

        has_any_skipped_in_section = any(counts[1] > 0 for counts in data.values())

        if not has_any_skipped_in_section and not self.print_empty_chapters:
            return ""

        # Sort: skipped desc, then key asc
        sorted_rows = sorted(data.items(), key=lambda item: (-item[1][1], item[0]))

        lines: list[str] = []
        lines.append(f"#### {title}")
        lines.append(f"| {columns[0]} | {columns[1]} | {columns[2]} |")
        lines.append(f"|{'-' * (len(columns[0]) + 2)}|{'-' * (len(columns[1]) + 2)}|{'-' * (len(columns[2]) + 2)}|")

        for key, counts in sorted_rows:
            lines.append(f"| {key} | {counts[0]} | {counts[1]} |")

        return "\n".join(lines) + "\n"
