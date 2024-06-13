import json

from ..github_integration.model.issue import Issue
from ..github_integration.model.pull_request import PullRequest


class ReleaseNotesBuilder:
    def __init__(self, issues: list[Issue], pulls: list[PullRequest], changelog_url: str, chapters_json: str,
                 warnings: bool, print_empty_chapters: bool):
        self.issues = issues
        self.pulls = pulls
        self.changelog_url = changelog_url
        self.chapters = json.loads(chapters_json)
        self.warnings = warnings
        self.print_empty_chapters = print_empty_chapters

    def _get_user_defined_chapters(self) -> str:
        release_notes = ""
        chapter_entries = {chapter['title']: [] for chapter in self.chapters}

        for issue in self.issues:
            if issue.is_closed:
                for chapter in self.chapters:
                    if chapter['label'] in issue.labels:
                        chapter_entries[chapter['title']].append((issue.id, f"- {issue.title} (#{issue.id})"))

        for pr in self.pulls:
            for chapter in self.chapters:
                chapter_entries[chapter['title']].append((pr.id, f"- {pr.title} (#{pr.id})"))

        for chapter in self.chapters:
            chapter_title = chapter['title']
            entries = chapter_entries[chapter_title]
            entries.sort()  # Sort by issue/PR number

            if entries or self.print_empty_chapters:
                release_notes += f"\n\n{chapter_title}\n"
                if entries:
                    release_notes += "\n".join([entry[1] for entry in entries]) + "\n\n\n"
                elif self.print_empty_chapters:
                    release_notes += "No entries for this chapter.\n\n\n"

        return release_notes

    def _get_sorted_issues_without_pr(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.is_closed]

    def _get_closed_issues_without_user_labels(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.is_closed and not issue.labels]

    def _get_closed_issues_without_release_notes_labels(self) -> list[Issue]:
        release_notes_labels = {"release-note", "changelog"}
        return [issue for issue in self.issues if issue.is_closed and not any(label in issue.labels for label in release_notes_labels)]

    def _get_merged_pulls_without_link_to_issue(self) -> list[PullRequest]:
        return []
        # return [pr for pr in self.pulls if pr.is_merged and pr.linked_issue_id is None]

    def _get_merged_pulls_linked_to_open_issue(self) -> list[PullRequest]:
        return []
        # return [pr for pr in self.pulls if pr.is_merged and pr.linked_issue_id and any(issue.id == pr.linked_issue_id and not issue.is_closed for issue in self.issues)]

    def _get_closed_pulls_without_link_to_issue(self) -> list[PullRequest]:
        return []
        # return [pr for pr in self.pulls if not pr.is_merged and pr.linked_issue_id is None]

    def _format_issues(self, issues: list[Issue]):
        return "\n".join([f"- {issue.title} (#{issue.id})" for issue in issues])

    def _format_pulls(self, pulls: list[PullRequest]):
        return "\n".join([f"- {pr.title} (#{pr.id})" for pr in pulls])

    def build(self) -> str:
        # TODO - add logic to create/control title issue/pr format
        # TODO - create new list of TODOs - missing inputs + differeces from previous version

        # TODO - add new features and bugs

        release_notes = self._get_user_defined_chapters()

        if self.warnings:
            sorted_issues_without_pr = self._get_sorted_issues_without_pr()
            if len(sorted_issues_without_pr) == 0 and self.print_empty_chapters:
                sorted_issues_without_pr_str = "All closed issues linked to a Pull Request.\n\n"
            else:
                sorted_issues_without_pr_str = self._format_issues(sorted_issues_without_pr)

            closed_issues_without_user_labels = self._get_closed_issues_without_user_labels()
            if len(closed_issues_without_user_labels) == 0 and self.print_empty_chapters:
                closed_issues_without_user_labels_str = "All closed issues contain at least one of user defined labels.\n\n"
            else:
                closed_issues_without_user_labels_str = self._format_issues(closed_issues_without_user_labels)

            closed_issues_without_release_notes_labels = self._get_closed_issues_without_release_notes_labels()
            if len(closed_issues_without_release_notes_labels) == 0 and self.print_empty_chapters:
                closed_issues_without_release_notes_labels_str = "All closed issues have release notes.\n\n"
            else:
                closed_issues_without_release_notes_labels_str = self._format_issues(closed_issues_without_release_notes_labels)

            merged_pulls_without_link_to_issue = self._get_merged_pulls_without_link_to_issue()
            if len(merged_pulls_without_link_to_issue) == 0 and self.print_empty_chapters:
                merged_pulls_without_link_to_issue_str = "All merged PRs are linked to issues.\n\n"
            else:
                merged_pulls_without_link_to_issue_str = self._format_pulls(merged_pulls_without_link_to_issue)

            merged_pulls_linked_to_open_issue = self._get_merged_pulls_linked_to_open_issue()
            if len(merged_pulls_linked_to_open_issue) == 0 and self.print_empty_chapters:
                merged_pulls_linked_to_open_issue_str = "All merged PRs are linked to Closed issues.\n\n"
            else:
                merged_pulls_linked_to_open_issue_str = self._format_pulls(merged_pulls_linked_to_open_issue)

            closed_pulls_without_link_to_issue = self._get_closed_pulls_without_link_to_issue()
            if len(closed_pulls_without_link_to_issue) == 0 and self.print_empty_chapters:
                closed_pulls_without_link_to_issue_str = "All closed PRs are linked to issues.\n\n"
            else:
                closed_pulls_without_link_to_issue_str = self._format_pulls(closed_pulls_without_link_to_issue)

            release_notes += f"### Closed Issues without Pull Request ⚠️\n{sorted_issues_without_pr_str}\n\n\n"
            release_notes += f"### Closed Issues without User Defined Labels ⚠️\n{closed_issues_without_user_labels_str}\n\n\n"
            release_notes += f"### Closed Issues without Release Notes ⚠️\n{closed_issues_without_release_notes_labels_str}\n\n\n"
            release_notes += f"### Merged PRs without Linked Issue and Custom Labels ⚠️\n{merged_pulls_without_link_to_issue_str}\n\n\n"
            release_notes += f"### Merged PRs Linked to Open Issue ⚠️\n{merged_pulls_linked_to_open_issue_str}\n\n\n"
            release_notes += f"### Closed PRs without Linked Issue and Custom Labels ⚠️\n{closed_pulls_without_link_to_issue_str}\n\n\n"

        release_notes += "#### Full Changelog\n" + self.changelog_url
        return release_notes
