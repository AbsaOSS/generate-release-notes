import logging
from typing import Optional

from github_integration.github_manager import GithubManager
from github_integration.model.commit import Commit
from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest


class Record:
    RELEASE_NOTE_DETECTION_PATTERN = "Release notes:"
    RELEASE_NOTE_LINE_MARK = "-"

    def __init__(self, issue: Optional[Issue] = None):
        self.__gh_issue: Issue = issue
        self.__pulls: list[PullRequest] = []
        self.__is_release_note_detected: bool = False
        self.__present_in_chapters = 0

    @property
    def is_present_in_chapters(self) -> bool:
        return self.__present_in_chapters > 0

    @property
    def is_pr(self) -> bool:
        return self.__gh_issue is None

    @property
    def is_issue(self) -> bool:
        return self.__gh_issue is not None

    @property
    def is_closed(self) -> bool:
        if self.__gh_issue is None:
            # no issue ==> stand-alone PR
            return self.__pulls[0].state == PullRequest.PR_STATE_CLOSED
            # TODO - check if this is the final state of the PR - cancel
        else:
            return self.__gh_issue.state == Issue.ISSUE_STATE_CLOSED

    @property
    def is_closed_issue(self) -> bool:
        return self.is_issue and self.__gh_issue.state == Issue.ISSUE_STATE_CLOSED

    @property
    def is_merged_pr(self) -> bool:
        if self.__gh_issue is None:
            return self.__pulls[0].is_merged
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
    def contains_release_notes(self) -> bool:
        if self.__is_release_note_detected:
            return self.__is_release_note_detected

        if self.RELEASE_NOTE_LINE_MARK in self.get_rls_notes:
            self.__is_release_note_detected = True

        return self.__is_release_note_detected

    @property
    def pulls_count(self) -> int:
        return len(self.__pulls)

    @property
    def does_pr_mention_issue(self) -> bool:
        # TODO - cela ta metoda je divna - mozna zmena kontextu

        if self.__gh_issue is None:
            # TODO - reimplement this to detect issues from body, the link not usable
            return "#" in self.__pulls[0].body      # this is only testing code
        return False

    @property
    def authors(self) -> Optional[str]:
        for pull in self.__pulls:
            if pull.author is not None:
                return pull.author

        return None

    @property
    def contributors(self) -> Optional[str]:
        return None

    @property
    def pr_links(self) -> Optional[str]:
        if len(self.__pulls) == 0:
            return None

        gh_manager = GithubManager()

        template = "[#{number}](https://github.com/{full_name}/pull/{number})"
        res = [
            template.format(number=pull.number, full_name=gh_manager.get_repository_full_name())
            for pull in self.__pulls
        ]

        return ", ".join(res)

    def pull_request(self, index: int = 0) -> PullRequest:
        return self.__pulls[index]

    def register_pull_request(self, pull):
        self.__pulls.append(pull)

    def register_commit(self, pull_nr: int, commit: Commit):
        for pull in self.__pulls:
            if pull.number == pull_nr:
                pull.register_commit(commit)
                return

        logging.error(f"Commit {commit.sha} not registered in any PR of record {self.__gh_issue.number}")

    # TODO add user defined row format feature
    #   - what else replaceable information could be interesting?
    def to_chapter_row(self, row_format="", increment_in_chapters=True) -> str:
        if increment_in_chapters:
            self.increment_present_in_chapters()

        if self.__gh_issue is None:
            p = self.__pulls[0]

            row = f"PR: #{p.number} _{p.title}_"

            # Issue can have more authors (as multiple PRs can be present)
            if self.authors is not None:
                row = f"{row}, implemented by {self.authors}"

            if self.contributors is not None:
                row = f"{row}, contributed by {self.contributors}"

            if self.contains_release_notes:
                return f"{row}\n{self.get_rls_notes}"

            return row
        else:
            row = f"#{self.__gh_issue.number} _{self.__gh_issue.title}_"

            if self.authors is not None:
                row = f"{row}, implemented by {self.authors}"

            if self.contributors is not None:
                row = f"{row}, contributed by {self.contributors}"

            if len(self.__pulls) > 0:
                row = f"{row} in {self.pr_links}"

            if self.contains_release_notes:
                return f"{row}\n{self.get_rls_notes}"

            return row

    def contains_labels(self, labels: list[str]) -> bool:
        if self.is_issue:
            return self.__gh_issue.contains_labels(labels)
        else:
            return self.__pulls[0].contains_labels(labels)

    def increment_present_in_chapters(self):
        self.__present_in_chapters += 1

    def present_in_chapters(self) -> int:
        return self.__present_in_chapters

    def is_commit_sha_present(self, sha: str) -> bool:
        for pull in self.__pulls:
            if pull.merge_commit_sha == sha:
                return True

        return False
