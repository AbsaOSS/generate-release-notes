from release_notes.model.base_chapters import BaseChapters
from release_notes.model.chapter import Chapter
from release_notes.model.record import Record


class ServiceChapters(BaseChapters):

    CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: str = "Closed Issues without Pull Request ⚠️"
    CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: str = "Closed Issues without User Defined Labels ⚠️"
    CLOSED_ISSUES_WITHOUT_RELEASE_NOTES: str = "Closed Issues without Release Notes ⚠️"
    MERGED_PRS_WITHOUT_LINKED_ISSUE: str = "Merged PRs without Linked Issue⚠️"
    MERGED_PRS_WITHOUT_LABELS: str = "Merged PRs without Labels ⚠️"
    MERGED_PRS_LINKED_TO_OPEN_ISSUES: str = "Merged PRs Linked to Open Issue ⚠️"
    CLOSED_PRS_WITHOUT_LINKED_ISSUE: str = "Closed PRs without Linked Issue ⚠️"
    CLOSED_PRS_WITHOUT_LABELS: str = "Closed PRs without Labels ⚠️"

    def __init__(self, sort_ascending: bool = True, print_empty_chapters: bool = True, user_defined_labels: list[str] = []):
        super().__init__(sort_ascending, print_empty_chapters)

        self.user_defined_labels = user_defined_labels
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
            self.MERGED_PRS_WITHOUT_LINKED_ISSUE: Chapter(
                title=self.MERGED_PRS_WITHOUT_LINKED_ISSUE,
                empty_message="All merged PRs are linked to issues."
            ),
            self.MERGED_PRS_WITHOUT_LABELS: Chapter(
                title=self.MERGED_PRS_WITHOUT_LABELS,
                empty_message="All merged PRs have label."
            ),
            self.MERGED_PRS_LINKED_TO_OPEN_ISSUES: Chapter(
                title=self.MERGED_PRS_LINKED_TO_OPEN_ISSUES,
                empty_message="All merged PRs are linked to Closed issues."
            ),
            self.CLOSED_PRS_WITHOUT_LINKED_ISSUE: Chapter(
                title=self.CLOSED_PRS_WITHOUT_LINKED_ISSUE,
                empty_message="All closed PRs are linked to issues."
            ),
            self.CLOSED_PRS_WITHOUT_LABELS: Chapter(
                title=self.CLOSED_PRS_WITHOUT_LABELS,
                empty_message="All closed PRs have label."
            )
        }
        self.show_chapter_closed_issues_without_pull_requests = True
        self.show_chapter_closed_issues_without_user_defined_labels = True
        self.show_chapter_closed_issues_without_release_notes = True
        self.show_chapter_merged_prs_without_linked_issue = True
        self.show_chapter_merged_prs_without_labels = True
        self.show_chapter_merged_prs_linked_to_open_issues = True
        self.show_chapter_closed_prs_without_linked_issue = True
        self.show_chapter_closed_prs_without_labels = True

    def populate(self, records: dict[int, Record]):
        for nr in records.keys():                               # iterate all records
            # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_PULL_REQUESTS
            if self.__is_closed_issues_without_pr(records[nr]):
                self.chapters[self.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].add_row(nr, records[nr].to_chapter_row())

            # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS
            if self.__is_closed_issues_without_user_labels(records[nr]):
                self.chapters[self.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].add_row(nr, records[nr].to_chapter_row())

            # check record properties if it fits to a chapter: CLOSED_ISSUES_WITHOUT_RELEASE_NOTES
            if self.__is_closed_issues_without_release_notes(records[nr]):
                self.chapters[self.CLOSED_ISSUES_WITHOUT_RELEASE_NOTES].add_row(nr, records[nr].to_chapter_row())

            # check record properties if it fits to a chapter: MERGED_PRS_WITHOUT_LINKED_ISSUE
            if self.__is_merged_pull_request_without_link_to_issue(records[nr]):
                self.chapters[self.MERGED_PRS_WITHOUT_LINKED_ISSUE].add_row(nr, records[nr].to_chapter_row())

            # check record properties if it fits to a chapter: MERGED_PRS_WITHOUT_LABELS
            if self.__is_merged_pull_request_without_link_to_issue(records[nr]):
                self.chapters[self.MERGED_PRS_WITHOUT_LABELS].add_row(nr, records[nr].to_chapter_row())

            # check record properties if it fits to a chapter: MERGED_PRS_LINKED_TO_OPEN_ISSUES
            if True:
                self.chapters[self.MERGED_PRS_LINKED_TO_OPEN_ISSUES].add_row(nr, records[nr].to_chapter_row())

            # check record properties if it fits to a chapter: CLOSED_PRS_WITHOUT_LINKED_ISSUE
            if True:
                self.chapters[self.CLOSED_PRS_WITHOUT_LINKED_ISSUE].add_row(nr, records[nr].to_chapter_row())

            # check record properties if it fits to a chapter: CLOSED_PRS_WITHOUT_LABELS
            if True:
                self.chapters[self.CLOSED_PRS_WITHOUT_LABELS].add_row(nr, records[nr].to_chapter_row())

    # TODO - check no issue PRs for visibility in service chapters
    #   - all issue chapters
    #   - Merged PRs without Linked Issue
    #   - Merged PRs without Labels
    #   - Merged PRs Linked to Open Issue
    #   - Closed PRs without Linked Issue
    #   - Closed PRs without Labels

    def __is_closed_issues_without_pr(self, record: Record) -> bool:
        return record.is_closed_issue and record.pulls_count == 0

    def __is_closed_issues_without_user_labels(self, record: Record) -> bool:
        contains_user_defined_labels = False
        for label in record.labels:
            if label in self.user_defined_labels:
                contains_user_defined_labels = True

        return record.is_closed_issue and not contains_user_defined_labels

    def __is_closed_issues_without_release_notes(self, record: Record) -> bool:
        return record.is_closed_issue and not record.contains_release_notes

    # TODO - check option when PR does not link to Issue in body but contains issue link
    def __is_merged_pull_request_without_link_to_issue(self, record: Record) -> bool:
        return record.is_merged_pr and record.is_pr_linked_to_issue

    def __is_merged_pull_request_without_label(self, record: Record) -> bool:
        return record.is_merged_pr and len(record.labels) == 0

    def __is_merged_pull_request_linked_to_open_issue(self, record: Record) -> bool:
        # TODO - implement later - it required additional API call (100%)
        return False

    def __is_closed_pull_request_without_link_to_issue(self, record: Record) -> bool:
        return record.is_closed_pr and record.is_pr_linked_to_issue

    def __is_closed_pull_request_without_label(self, record: Record) -> bool:
        return record.is_closed_pr and len(record.labels) == 0
