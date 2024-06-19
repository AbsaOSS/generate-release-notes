import logging

from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.formatter.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.model.service_chapters import ServiceChapters


class ReleaseNotesBuilder:
    def __init__(self, records: dict[int, Record], changelog_url: str,
                 formatter: RecordFormatter, custom_chapters: CustomChapters,
                 warnings: bool = True, print_empty_chapters: bool = True):
        self.records = records
        self.changelog_url = changelog_url
        self.formatter = formatter
        self.custom_chapters = custom_chapters
        self.warnings = warnings
        self.print_empty_chapters = print_empty_chapters

    def _get_sorted_issues_without_pr(self) -> list[Issue]:
        return []
        # return [issue for issue in self.issues if issue.is_closed]

    def _get_closed_issues_without_user_labels(self) -> list[Issue]:
        return []
        # return [issue for issue in self.issues if issue.is_closed and not issue.labels]

    def _get_closed_issues_without_release_notes_labels(self) -> list[Issue]:
        release_notes_labels = {"release-note", "changelog"}
        return []
        # return [issue for issue in self.issues if issue.is_closed and not any(label in issue.labels for label in release_notes_labels)]

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
        user_defined_chapters = self.custom_chapters

        # TODO - generate custom chapter's rows

        user_defined_chapters_str = user_defined_chapters.to_string()

        if self.warnings:
            logging.debug("Generating warnings...")
            service_chapters = ServiceChapters(print_empty_chapters=self.print_empty_chapters)



            # TODO - generate service chapter's rows


            # sorted_issues_without_pr = self._get_sorted_issues_without_pr()
            # if len(sorted_issues_without_pr) == 0 and self.print_empty_chapters:
            #     sorted_issues_without_pr_str = "All closed issues linked to a Pull Request.\n\n"
            # else:
            #     # sorted_issues_without_pr_str = self._format_issues(sorted_issues_without_pr)
            #     sorted_issues_without_pr_str = "To be done"
            #
            # closed_issues_without_user_labels = self._get_closed_issues_without_user_labels()
            # if len(closed_issues_without_user_labels) == 0 and self.print_empty_chapters:
            #     closed_issues_without_user_labels_str = "All closed issues contain at least one of user defined labels.\n\n"
            # else:
            #     # closed_issues_without_user_labels_str = self._format_issues(closed_issues_without_user_labels)
            #     closed_issues_without_user_labels_str = "To be done"
            #
            # closed_issues_without_release_notes_labels = self._get_closed_issues_without_release_notes_labels()
            # if len(closed_issues_without_release_notes_labels) == 0 and self.print_empty_chapters:
            #     closed_issues_without_release_notes_labels_str = "All closed issues have release notes.\n\n"
            # else:
            #     # closed_issues_without_release_notes_labels_str = self._format_issues(closed_issues_without_release_notes_labels)
            #     closed_issues_without_release_notes_labels_str = "To be done"
            #
            # merged_pulls_without_link_to_issue = self._get_merged_pulls_without_link_to_issue()
            # if len(merged_pulls_without_link_to_issue) == 0 and self.print_empty_chapters:
            #     merged_pulls_without_link_to_issue_str = "All merged PRs are linked to issues.\n\n"
            # else:
            #     # merged_pulls_without_link_to_issue_str = self._format_pulls(merged_pulls_without_link_to_issue)
            #     merged_pulls_without_link_to_issue_str = "To be done"
            #
            # merged_pulls_linked_to_open_issue = self._get_merged_pulls_linked_to_open_issue()
            # if len(merged_pulls_linked_to_open_issue) == 0 and self.print_empty_chapters:
            #     merged_pulls_linked_to_open_issue_str = "All merged PRs are linked to Closed issues.\n\n"
            # else:
            #     # merged_pulls_linked_to_open_issue_str = self._format_pulls(merged_pulls_linked_to_open_issue)
            #     merged_pulls_linked_to_open_issue_str = "To be done"
            #
            # closed_pulls_without_link_to_issue = self._get_closed_pulls_without_link_to_issue()
            # if len(closed_pulls_without_link_to_issue) == 0 and self.print_empty_chapters:
            #     closed_pulls_without_link_to_issue_str = "All closed PRs are linked to issues.\n\n"
            # else:
            #     # closed_pulls_without_link_to_issue_str = self._format_pulls(closed_pulls_without_link_to_issue)
            #     closed_pulls_without_link_to_issue_str = "To be done"

            service_chapters_str = service_chapters.to_string()
            release_notes = f"""{user_defined_chapters_str}{service_chapters_str}#### Full Changelog\n{self.changelog_url}\n"""
        else:
            release_notes = f"""{user_defined_chapters_str}#### Full Changelog\n{self.changelog_url}\n"""

        logging.debug(f"Release notes: \n{release_notes}")
        return release_notes
