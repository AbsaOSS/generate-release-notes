from typing import Optional

from github import Commit as GitCommit


class Commit:
    """
    A class used to represent a commit in GitHub.
    """

    def __init__(self, commit: GitCommit):
        """
        Constructs all the necessary attributes for the Commit object.

        :param commit: The GitCommit object.
        """
        self.__commit: GitCommit = commit

    @property
    def sha(self) -> str:
        """
        Gets the SHA of the commit.

        :return: The SHA of the commit as a string.
        """
        return self.__commit.sha

    @property
    def message(self) -> str:
        """
        Gets the message of the commit.

        :return: The message of the commit as a string.
        """
        return self.__commit.commit.message

    @property
    def author(self) -> str:
        """
        Gets the author of the commit.

        :return: The author of the commit as a string.
        """
        return self.__commit.author.login
