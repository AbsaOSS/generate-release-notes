from typing import Optional

from github.GitRelease import GitRelease
from github.Repository import Repository


def singleton(cls):
    """
    A decorator for making a class a singleton.

    :param cls: The class to make a singleton.
    :return: The singleton instance of the class.
    """

    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


# TODO - review existing method and decide their integration here
@singleton
class GithubManager:
    """
    A singleton class used to manage GitHub interactions.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the GithubManager object.
        """
        self.repository = None
        self.git_release = None

    def set_repository(self, repository: Repository):
        """
        Sets the repository attribute.

        :param repository: The Repository object to set.
        """
        self.repository = repository

    def set_git_release(self, release: GitRelease):
        """
        Sets the git_release attribute.

        :param release: The GitRelease object to set.
        """
        self.git_release = release

    def get_repository(self) -> Optional[Repository]:
        """
        Gets the repository attribute.

        :return: The Repository object, or None if it is not set.
        """
        return self.repository

    def get_git_release(self) -> Optional[GitRelease]:
        """
        Gets the git_release attribute.

        :return: The GitRelease object, or None if it is not set.
        """
        return self.git_release

    def get_repository_full_name(self) -> Optional[str]:
        """
        Gets the full name of the repository.

        :return: The full name of the repository as a string, or None if the repository is not set.
        """
        if self.repository is not None:
            return self.repository.full_name
        return None
