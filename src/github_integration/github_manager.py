import logging
import time

from datetime import datetime
from typing import Optional

from github import Github
from github.GitRelease import GitRelease
from github.RateLimit import RateLimit
from github.Repository import Repository

from github_integration.model.commit import Commit
from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest


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


@singleton
class GithubManager:
    """
    A singleton class used to manage GitHub interactions.
    """
    def __init__(self):
        """
        Constructs all the necessary attributes for the GithubManager object.
        """
        self.__g = None
        self.__repository = None
        self.__git_release = None

    @property
    def github(self) -> Github:
        """
        Gets the g attribute.

        :return: The Github object.
        """
        return self.__g

    @github.setter
    def github(self, g: Github):
        """
        Sets the g attribute.

        :return: The Github object.
        """
        self.__g = g

    @property
    def repository(self) -> Optional[Repository]:
        """
        Gets the repository attribute.

        :return: The Repository object, or None if it is not set.
        """
        return self.__repository

    @property
    def git_release(self) -> Optional[GitRelease]:
        """
        Gets the git_release attribute.

        :return: The GitRelease object, or None if it is not set.
        """
        return self.__git_release

    # fetch method

    def fetch_repository(self, repository_id: str) -> Optional[Repository]:
        """
        Fetches a repository from GitHub using the provided repository ID.

        :param repository_id: The ID of the repository to fetch.
        :return: The fetched Repository object, or None if the repository could not be fetched.
        """
        try:
            logging.info(f"Fetching repository: {repository_id}")
            self.__repository = self.__g.get_repo(repository_id)
        except Exception as e:
            if "Not Found" in str(e):
                logging.error(f"Repository not found: {repository_id}")
                self.__repository = None
            else:
                logging.error(f"Fetching repository failed for {repository_id}: {str(e)}")
                self.__repository = None

        return self.__repository

    def fetch_latest_release(self) -> Optional[GitRelease]:
        """
        Fetches the latest release from a current repository.

        :return: The fetched GitRelease object representing the latest release, or None if there is no release or the fetch failed.
        """
        try:
            logging.info(f"Fetching latest release for {self.__repository.full_name}")
            release = self.__repository.get_latest_release()
            logging.debug(f"Found latest release: {release.tag_name}, created at: {release.created_at}, "
                          f"published at: {release.published_at}")
            self.__git_release = release

        except Exception as e:
            if "Not Found" in str(e):
                logging.error(f"Latest release not found for {self.__repository.full_name}. 1st release for repository!")
                self.__git_release = None
            else:
                logging.error(f"Fetching latest release failed for {self.__repository.full_name}: {str(e)}. "
                              f"Expected first release for repository.")
                self.__git_release = None

        return self.__git_release

    def fetch_issues(self, since: datetime = None, state: str = None) -> list[Issue]:
        """
        Fetches all issues from the current repository.
        If a since is set, fetches all issues since the defined time.

        :return: A list of Issue objects.
        """
        if self.__git_release is None:
            logging.info(f"Fetching all issues for {self.__repository.full_name}")
            issues = self.__repository.get_issues(state="all")
        else:
            logging.info(f"Fetching all issues since {self.__git_release.published_at} for {self.__repository.full_name}")
            issues = self.__repository.get_issues(state="all", since=self.__git_release.published_at)

        parsed_issues = []
        logging.info(f"Found {len(list(issues))} issues for {self.__repository.full_name}")
        for issue in list(issues):
            parsed_issues.append(Issue(issue))

        return parsed_issues

    def fetch_pull_requests(self, since: datetime = None, state: str = None) -> list[PullRequest]:
        """
        Fetches all pull requests from the current repository.
        If a 'since' datetime is provided, fetches all pull requests since that time.
        If a 'state' is provided, fetches pull requests with that state.

        :param since: The datetime to fetch pull requests since. If None, fetches all pull requests.
        :param state: The state of the pull requests to fetch. If None, fetches pull requests of all states.
        :return: A list of PullRequest objects.
        """
        logging.info(f"Fetching all closed PRs for {self.__repository.full_name}")
        if state is None:
            pulls = self.__repository.get_pulls()
        else:
            pulls = self.__repository.get_pulls(state=state)

        pull_requests = []
        logging.info(f"Found {len(list(pulls))} PRs for {self.__repository.full_name}")
        for pull in list(pulls):
            pull_requests.append(PullRequest(pull))

        return pull_requests

    def fetch_commits(self, since: datetime = None) -> list[Commit]:
        logging.info(f"Fetching all commits {self.__repository.full_name}")
        raw_commits = self.__repository.get_commits()

        commits = []
        for raw_commit in raw_commits:
            # for reference commit author - use raw_commit.author

            # logging.debug(f"Raw Commit: {raw_commit}, Author: {raw_commit.author}, Commiter: {raw_commit.committer}.")
            # logging.debug(f"Raw Commit.commit: Message: {raw_commit.commit.message}, Author: {raw_commit.commit.author}, Commiter: {raw_commit.commit.committer}.")

            commits.append(Commit(raw_commit))

        return commits

    # get methods

    def get_change_url(self, tag_name: str) -> str:
        if self.__git_release:
            # If there is a latest release, create a URL pointing to commits since the latest release
            changelog_url = f"https://github.com/{self.__repository.full_name}/compare/{self.__git_release.tag_name}...{tag_name}"

        else:
            # If there is no latest release, create a URL pointing to all commits
            changelog_url = f"https://github.com/{self.__repository.full_name}/commits/{tag_name}"

        return changelog_url

    def get_repository_full_name(self) -> Optional[str]:
        """
        Gets the full name of the repository.

        :return: The full name of the repository as a string, or None if the repository is not set.
        """
        if self.__repository is not None:
            return self.__repository.full_name
        return None

    # others

    def show_rate_limit(self):
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            return

        if self.__g is None:
            logging.error("GitHub object is not set.")
            return

        rate_limit: RateLimit = self.__g.get_rate_limit()

        if rate_limit.core.remaining < rate_limit.core.limit/10:
            reset_time = rate_limit.core.reset
            sleep_time = (reset_time - datetime.utcnow()).total_seconds() + 10
            logging.debug(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time)
        else:
            logging.debug(f"Rate limit: {rate_limit.core.remaining} remaining of {rate_limit.core.limit}")
