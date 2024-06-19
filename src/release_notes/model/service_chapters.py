from release_notes.model.base_chapters import BaseChapters
from release_notes.model.chapter import Chapter


class ServiceChapters(BaseChapters):
    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: int = 1
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: int = 2
    CLOSED_ISSUES_WITHOUT_RELEASE_NOTES: int = 3
    MERGED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: int = 4
    MERGED_PRS_LINKED_TO_OPEN_ISSUES: int = 5
    CLOSED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: int = 6

    def __init__(self, sort_ascending: bool = True):
        super().__init__(sort_ascending)

        self.sort_ascending = sort_ascending
        self.chapters = {
            self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: Chapter(title="Closed Issues without Pull Request ⚠️"),
            self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: Chapter(title="Closed Issues without User Defined Labels ⚠️"),
            self.CLOSED_ISSUES_WITHOUT_RELEASE_NOTES: Chapter(title="Closed Issues without Release Notes ⚠️"),
            self.MERGED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: Chapter(title="Merged PRs without Linked Issue and Custom Labels ⚠️"),
            self.MERGED_PRS_LINKED_TO_OPEN_ISSUES: Chapter(title="Merged PRs Linked to Open Issue ⚠️"),
            self.CLOSED_PRS_WITHOUT_LINKED_ISSUE_AND_CUSTOM_LABELS: Chapter(title="Closed PRs without Linked Issue and Custom Labels ⚠️")
        }
        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_closed_issues_without_release_notes = True
        self.show_chapter_merged_prs_without_linked_issue_and_custom_labels = True
        self.show_chapter_merged_prs_linked_to_open_issues = True
        self.show_chapter_closed_prs_without_linked_issue_and_custom_labels = True
