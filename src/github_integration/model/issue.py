from datetime import datetime
from typing import Optional

from github.Issue import Issue as GitIssue


class Issue:
    ISSUE_STATE_CLOSED = "closed"

    def __init__(self, issue: GitIssue):
        self.__issue: GitIssue = issue
        self.__labels: Optional[list[str]] = None

    @property
    def id(self) -> int:
        return self.__issue.id

    @property
    def number(self) -> int:
        return self.__issue.number

    @property
    def title(self) -> str:
        return self.__issue.title

    @property
    def body(self) -> str:
        return self.__issue.body if self.__issue.body else ""

    @property
    def state(self) -> str:
        return self.__issue.state

    @property
    def labels(self) -> list[str]:
        if self.__labels is None:
            self.__labels = [label.name for label in self.__issue.get_labels()]

        return self.__labels

    @property
    def created_at(self) -> datetime:
        return self.__issue.created_at

    def is_closed(self) -> bool:
        return self.state == "closed"

    def contains_labels(self, labels: list[str]) -> bool:
        for label in labels:
            if label in self.labels:
                return True
        return False
