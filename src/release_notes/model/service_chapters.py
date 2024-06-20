from release_notes.model.base_chapters import BaseChapters
from release_notes.model.chapter import Chapter
from release_notes.model.record import Record


class ServiceChapters(BaseChapters):

    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: str = "Closed Issues without Pull Request ⚠️"
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: str = "Closed Issues without User Defined Labels ⚠️"
    CLOSED_ISSUES_WITHOUT_RELEASE_NOTES: str = "Closed Issues without Release Notes ⚠️"
    MERGED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: str = "Merged PRs without Linked Issue and Custom Labels ⚠️"
    MERGED_PRS_LINKED_TO_OPEN_ISSUES: str = "Merged PRs Linked to Open Issue ⚠️"
    CLOSED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: str = "Closed PRs without Linked Issue and Custom Labels ⚠️"

    def __init__(self, sort_ascending: bool = True, print_empty_chapters: bool = True):
        super().__init__(sort_ascending, print_empty_chapters)

        self.sort_ascending = sort_ascending
        self.chapters = {
            self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: Chapter(
                title=self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS,
                empty_message="All closed issues linked to a Pull Request."
            ),
            self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: Chapter(
                title=self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS,
                empty_message="All closed issues contain at least one of user defined labels."
            ),
            self.CLOSED_ISSUES_WITHOUT_RELEASE_NOTES: Chapter(
                title=self.CLOSED_ISSUES_WITHOUT_RELEASE_NOTES,
                empty_message="All closed issues have release notes."
            ),
            self.MERGED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: Chapter(
                title=self.MERGED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS,
                empty_message="All merged PRs are linked to issues."
            ),
            self.MERGED_PRS_LINKED_TO_OPEN_ISSUES: Chapter(
                title=self.MERGED_PRS_LINKED_TO_OPEN_ISSUES,
                empty_message="All merged PRs are linked to Closed issues."
            ),
            self.CLOSED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: Chapter(
                title=self.CLOSED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS,
                empty_message="All closed PRs are linked to issues."
            )
        }
        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_closed_issues_without_release_notes = True
        self.show_chapter_merged_prs_without_linked_issue_and_custom_labels = True
        self.show_chapter_merged_prs_linked_to_open_issues = True
        self.show_chapter_closed_prs_without_linked_issue_and_custom_labels = True

    def populate(self, records: dict[int, Record]):
        pass
