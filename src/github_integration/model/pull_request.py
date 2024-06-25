import re
from datetime import datetime
from typing import Optional

from github.PullRequest import PullRequest as GitPullRequest


class PullRequest:
    PR_STATE_CLOSED = "closed"
    PR_STATE_MERGED = "merged"

    def __init__(self, pull: GitPullRequest):
        self.__source_pull = pull

        # for local storage of data required additional API call
        self.__labels = None

        self.__body_contains_issue_mention = False
        self.__mentioned_issues: list[int] = self.extract_issue_numbers_from_body()

    @property
    def id(self) -> int:
        return self.__source_pull.id

    @property
    def number(self) -> int:
        return self.__source_pull.number

    @property
    def title(self) -> str:
        return self.__source_pull.title

    @property
    def body(self) -> str:
        return self.__source_pull.body if self.__source_pull.body else ""

    @property
    def state(self) -> str:
        return self.__source_pull.state

    @property
    def created_at(self) -> datetime:
        return self.__source_pull.created_at

    @property
    def updated_at(self) -> datetime:
        return self.__source_pull.updated_at

    @property
    def closed_at(self) -> Optional[datetime]:
        return self.__source_pull.closed_at if self.__source_pull.closed_at else None

    @property
    def merged_at(self) -> Optional[datetime]:
        return self.__source_pull.merged_at if self.__source_pull.merged_at else None

    @property
    def assignee(self) -> Optional[str]:
        return self.__source_pull.assignee.login if self.__source_pull.assignee else None

    @property
    def labels(self) -> list[str]:
        if self.__labels is None:
            self.__labels = [label.name for label in self.__source_pull.get_labels()]

        return self.__labels

    @property
    def is_merged(self) -> bool:
        return self.merged_at is not None and self.state == self.PR_STATE_MERGED

    @property
    def is_closed(self) -> bool:
        return self.closed_at is not None and self.state == self.PR_STATE_CLOSED

    @property
    def body_contains_issue_mention(self) -> bool:
        return self.__body_contains_issue_mention

    @property
    def author(self) -> Optional[str]:
        # TODO check - maybe will be filled in another way
        return self.__source_pull.user.login

    @property
    def contributors(self) -> list[str]:
        # TODO
        return []

    @property
    def merge_commit_sha(self) -> str:
        return self.__source_pull.merge_commit_sha

    def extract_issue_numbers_from_body(self) -> list[int]:
        # Regex pattern to match issue numbers following keywords like "Close", "Fix", "Resolve"
        regex_pattern = re.compile(r'([Cc]los(e|es|ed)|[Ff]ix(es|ed)?|[Rr]esolv(e|es|ed))\s*#\s*([0-9]+)')

        # Extract all issue numbers from the PR body
        issue_matches = regex_pattern.findall(self.body)

        # Extract the issue numbers from the matches
        issue_numbers = [int(match[-1]) for match in issue_matches]

        if not self.__body_contains_issue_mention and len(issue_numbers) > 0:
            self.__body_contains_issue_mention = True

        return issue_numbers

    def contains_labels(self, labels: list[str]) -> bool:
        for label in labels:
            if label in self.labels:
                return True
        return False
