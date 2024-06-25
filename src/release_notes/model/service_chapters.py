from github_integration.model.pull_request import PullRequest
from release_notes.model.base_chapters import BaseChapters
from release_notes.model.chapter import Chapter
from release_notes.model.record import Record


class ServiceChapters(BaseChapters):

    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: str = "Closed Issues without Pull Request ⚠️"
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: str = "Closed Issues without User Defined Labels ⚠️"

    MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Merged PRs without Issue and User Defined Labels ⚠️"
    CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Closed PRs without Issue and User Defined Labels ⚠️"

    MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES: str = "Merged PRs Linked to 'Not Closed' Issue ⚠️"

    OTHERS_NO_TOPIC: str = "Others - No Topic ⚠️"

    def __init__(self, sort_ascending: bool = True, print_empty_chapters: bool = True, user_defined_labels: list[str] = None):
        super().__init__(sort_ascending, print_empty_chapters)

        self.user_defined_labels = user_defined_labels if user_defined_labels is not None else []
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
            self.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: Chapter(
                title=self.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
                empty_message="All merged PRs are linked to issues."
            ),
            self.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: Chapter(
                title=self.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS,
                empty_message="All closed PRs are linked to issues."
            ),
            self.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES: Chapter(
                title=self.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES,
                empty_message="All merged PRs are linked to Closed issues."
            ),
            self.OTHERS_NO_TOPIC: Chapter(
                title=self.OTHERS_NO_TOPIC,
                empty_message="Previous filters caught all Issues or Pull Requests."
            )
        }
        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_merged_pr_without_issue_and_labels = True
        self.show_chapter_closed_pr_without_issue_and_labels = True

        self.show_chapter_merged_prs_linked_to_open_issues = True

    def populate(self, records: dict[int, Record]):
        for nr in records.keys():                               # iterate all records
            if records[nr].is_closed_issue:
                self.__populate_closed_issues(records[nr], nr)

            elif records[nr].is_pr:
                self.__populate_pr(records[nr], nr)

            else:
                if not records[nr].is_present_in_chapters:
                    self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, records[nr].to_chapter_row())

    def __populate_closed_issues(self, record: Record, nr: int):
        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_PULL_REQUESTS
        if record.pulls_count == 0:
            self.chapters[self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].add_row(nr, record.to_chapter_row())

        # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS
        if not record.contains_labels(self.user_defined_labels):
            self.chapters[self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())

        if not record.is_present_in_chapters:
            self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())

    def __populate_pr(self, record: Record, nr: int):
        if record.is_merged_pr:
            # check record properties if it fits to a chapter: MERGED_PRS_WITHOUT_ISSUE
            if not record.does_pr_mention_issue and not record.contains_labels(self.user_defined_labels):
                self.chapters[self.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())

            # check record properties if it fits to a chapter: MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES
            if record.does_pr_mention_issue:
                self.chapters[self.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].add_row(nr, record.to_chapter_row())

            if not record.is_present_in_chapters:
                self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())

        # check record properties if it fits to a chapter: CLOSED_PRS_WITHOUT_ISSUE
        elif record.is_closed and not record.does_pr_mention_issue and not record.contains_labels(self.user_defined_labels):
            self.chapters[self.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].add_row(nr, record.to_chapter_row())

        if not record.is_present_in_chapters:
            self.chapters[self.OTHERS_NO_TOPIC].add_row(nr, record.to_chapter_row())
