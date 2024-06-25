from typing import Optional

from github import Commit as GitCommit


class Commit:
    def __init__(self, commit: GitCommit):
        self.__commit: GitCommit = commit

    @property
    def sha(self) -> str:
        return self.__commit.sha
