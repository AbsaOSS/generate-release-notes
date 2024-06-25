from datetime import datetime
from github.Issue import Issue as GitIssue


class Issue:
    def __init__(self, issue: GitIssue):
        self.__issue = issue
        self.__labels = None

    @property
    def id(self):
        return self.__issue.id

    @property
    def number(self):
        return self.__issue.number

    @property
    def title(self):
        return self.__issue.title

    @property
    def body(self):
        return self.__issue.body if self.__issue.body else ""

    @property
    def state(self):
        return self.__issue.state

    @property
    def labels(self) -> list[str]:
        if self.__labels is None:
            self.__labels = [label.name for label in self.__issue.get_labels()]

        return self.__labels

    @property
    def created_at(self):
        return self.__issue.created_at

    def is_closed(self):
        return self.state == "closed"

    def contains_labels(self, labels: list[str]) -> bool:
        for label in labels:
            if label in self.labels:
                return True
