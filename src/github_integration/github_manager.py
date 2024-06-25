from typing import Optional

from github.GitRelease import GitRelease
from github.Repository import Repository


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


# TODO - review existing method and decide their integration here
@singleton
class GithubManager:
    def __init__(self):
        self.repository = None
        self.git_release = None

    def set_repository(self, repository: Repository):
        self.repository = repository

    def set_git_release(self, release: GitRelease):
        self.git_release = release

    def get_repository(self) -> Optional[Repository]:
        return self.repository

    def get_git_release(self) -> Optional[GitRelease]:
        return self.git_release

    def get_repository_full_name(self) -> Optional[str]:
        if self.repository is not None:
            return self.repository.full_name
        return None
