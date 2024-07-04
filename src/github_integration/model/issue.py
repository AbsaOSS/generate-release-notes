from datetime import datetime
from typing import Optional

from github import Issue as GitIssue


class Issue:
    """
    A class used to represent an issue in GitHub.
    """

    ISSUE_STATE_CLOSED = "closed"
    ISSUE_STATE_OPEN = "open"

    def __init__(self, issue: GitIssue):
        """
        Constructs all the necessary attributes for the Issue object.

        :param issue: The GitIssue object.
        """
        self.__issue: GitIssue = issue
        self.__labels: Optional[list[str]] = None

    @property
    def id(self) -> int:
        """
        Gets the ID of the issue.

        :return: The ID of the issue as an integer.
        """
        return self.__issue.id

    @property
    def number(self) -> int:
        """
        Gets the number of the issue.

        :return: The number of the issue as an integer.
        """
        return self.__issue.number

    @property
    def title(self) -> str:
        """
        Gets the title of the issue.

        :return: The title of the issue as a string.
        """
        return self.__issue.title

    @property
    def body(self) -> str:
        """
        Gets the body of the issue.

        :return: The body of the issue as a string, or an empty string if there is no body.
        """
        return self.__issue.body if self.__issue.body else ""

    @property
    def state(self) -> str:
        """
        Gets the state of the issue.

        :return: The state of the issue as a string.
        """
        return self.__issue.state

    @property
    def labels(self) -> list[str]:
        """
        Gets the labels of the issue.

        :return: The labels of the issue as a list of strings.
        """
        if self.__labels is None:
            self.__labels = [label.name for label in self.__issue.get_labels()]

        return self.__labels

    @property
    def created_at(self) -> datetime:
        """
        Gets the creation date of the issue.

        :return: The creation date of the issue as a datetime object.
        """
        return self.__issue.created_at

    @property
    def authors(self) -> list[str]:
        """
        Gets the authors of the issue.

        :return: The authors of the issue as a list of strings.
        """
        # TODO in Issue named 'Chapter line formatting - authors'
        return []

    @property
    def contributors(self) -> list[str]:
        """
        Gets the contributors of the issue.

        :return: The contributors of the issue as a list of strings.
        """
        # TODO in Issue named 'Chapter line formatting - contributors'
        return []

    @property
    def state_reason(self) -> Optional[str]:
        """
        Gets the reason for the state of the issue.

        :return: The reason for the state of the issue as a string.
        """
        return self.__issue.state_reason

    def is_closed(self) -> bool:
        """
        Checks if the issue is closed.

        :return: True if the issue is closed, False otherwise.
        """
        return self.state == "closed"

    def contains_labels(self, labels: list[str]) -> bool:
        """
        Checks if the issue contains any of the specified labels.

        :param labels: The labels to check for.
        :return: True if the issue contains any of the specified labels, False otherwise.
        """
        for label in labels:
            if label in self.labels:
                return True
        return False
