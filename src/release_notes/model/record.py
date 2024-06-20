from typing import Optional

from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest


class Record:
    RELEASE_NOTE_DETECTION_PATTERN = "Release notes:"
    RELEASE_NOTE_LINE_MARK = "-"

    def __init__(self, issue: Optional[Issue] = None):
        self.__gh_issue: Issue = issue
        self.__pulls: list[PullRequest] = []
        self.__is_release_note_detected: bool = False

    @property
    def is_pr(self):
        return self.__gh_issue is None

    @property
    def is_issue(self):
        return self.__gh_issue is not None

    @property
    def is_closed(self):
        if self.__gh_issue is None:
            # no issue ==> stand-alone PR
            return self.__pulls[0].is_merged
            # TODO - check if this is the final state of the PR - cancel
        else:
            return self.__gh_issue.is_closed

    @property
    def is_closed_issue(self):
        return self.is_issue and self.__gh_issue.is_closed

    @property
    def is_merged_pr(self):
        if self.__gh_issue is None:
            return self.__pulls[0].is_merged
        return False

    @property
    def is_closed_pr(self):
        if self.__gh_issue is None:
            return self.__pulls[0].is_closed
        return False

    @property
    def labels(self) -> list[str]:
        if self.__gh_issue is None:
            return self.__pulls[0].labels
        else:
            return self.__gh_issue.labels

    # TODO - 'Release notest:' as detection pattern default - can be defined by user
    # TODO - '-' as leading line mark for each release note to be used
    @property
    def get_rls_notes(self, detection_pattern=RELEASE_NOTE_DETECTION_PATTERN, line_mark=RELEASE_NOTE_LINE_MARK) -> str:
        release_notes = ""

        # Iterate over all PRs
        for pull in self.__pulls:
            body_lines = pull.body.split('\n')
            inside_release_notes = False

            for line in body_lines:
                if detection_pattern in line:
                    inside_release_notes = True
                    continue

                if inside_release_notes:
                    if line.startswith(line_mark):
                        release_notes += f"  {line.strip()}\n"
                    else:
                        break

        # Return the concatenated release notes
        return release_notes.rstrip()

    @property
    def contains_release_notes(self):
        if self.__is_release_note_detected:
            return self.__is_release_note_detected

        if self.RELEASE_NOTE_LINE_MARK in self.get_rls_notes:
            self.__is_release_note_detected = True

        return self.__is_release_note_detected

    @property
    def pulls_count(self) -> int:
        return len(self.__pulls)

    @property
    def is_pr_linked_to_issue(self):
        if self.__gh_issue is None:
            return self.__pulls[0].is_linked_to_issue
        return False

    def pull_request(self, index: int = 0):
        return self.__pulls[index]

    def register_pull_request(self, pull):
        self.__pulls.append(pull)

    # TODO add user defined row format feature
    def to_chapter_row(self, row_format=""):
        # Example of default format
        # - #37 _Example Issue without PR_ implemented by "Missing Assignee or Contributor"
        #   - Example Issue to show usage of feature label and closed Issue without linked PR.
        #   - Test release note without leading bullet
        # - #38 _Example Issue without Release notes comment_ implemented by "Missing Assignee or Contributor"

        if self.__gh_issue is None:
            return f"{self.__pulls[0].title}"
        else:
            if self.contains_release_notes:
                return f"#{self.__gh_issue.number} _{self.__gh_issue.title}_ implemented by TODO\n{self.get_rls_notes}"
            else:
                return f"#{self.__gh_issue.number} _{self.__gh_issue.title}_ implemented by TODO"
