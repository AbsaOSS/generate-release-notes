import logging
import time

from datetime import datetime
from typing import Optional

from github import Github
from github.GitRelease import GitRelease
from github.RateLimit import RateLimit
from github.Repository import Repository

from .model.commit import Commit
from .model.issue import Issue
from .model.pull_request import PullRequest


def get_gh_repository(g: Github, repository_id: str) -> Optional[Repository]:
    try:
        logging.info(f"Fetching repository: {repository_id}")
        return g.get_repo(repository_id)
    except Exception as e:
        if "Not Found" in str(e):
            logging.error(f"Repository not found: {repository_id}")
            return None
        else:
            logging.error(f"Fetching repository failed for {repository_id}: {str(e)}")
            return None


def fetch_latest_release(repo: Repository) -> Optional[GitRelease]:
    try:
        logging.info(f"Fetching latest release for {repo.full_name}")
        release = repo.get_latest_release()
        logging.debug(f"Found latest release: {release.tag_name}, created at: {release.created_at}, "
                      f"published at: {release.published_at}")
        return release

    except Exception as e:
        if "Not Found" in str(e):
            logging.error(f"Latest release not found for {repo.full_name}. 1st release for repository!")
            return None
        else:
            logging.error(f"Fetching latest release failed for {repo.full_name}: {str(e)}. "
                            f"Expected first release for repository.")
            return None


def fetch_all_issues(repo: Repository, release: Optional[GitRelease]) -> list[Issue]:
    if release is None:
        logging.info(f"Fetching all issues for {repo.full_name}")
        issues = repo.get_issues(state="all")
    else:
        logging.info(f"Fetching all issues since {release.published_at} for {repo.full_name}")
        issues = repo.get_issues(state="all", since=release.published_at)

    parsed_issues = []
    logging.info(f"Found {len(list(issues))} issues for {repo.full_name}")
    for issue in list(issues):
        parsed_issues.append(Issue(issue))

    return parsed_issues


def fetch_finished_pull_requests(repo: Repository) -> list[PullRequest]:
    # TODO - decide: pulls = repo.get_pulls(state='closed', sort='created', direction='desc')
    logging.info(f"Fetching all closed PRs for {repo.full_name}")
    pulls = repo.get_pulls(state='closed')

    pull_requests = []
    logging.info(f"Found {len(list(pulls))} PRs for {repo.full_name}")
    for pull in list(pulls):
        pull_requests.append(PullRequest(pull))

    return pull_requests


def fetch_commits(repo: Repository) -> list[Commit]:
    logging.info(f"Fetching all commits {repo.full_name}")
    raw_commits = repo.get_commits()

    commits = []
    for raw_commit in raw_commits:
        # for reference commit auhtor - use raw_commit.author

        # logging.debug(f"Raw Commit: {raw_commit}, Author: {raw_commit.author}, Commiter: {raw_commit.committer}.")
        # logging.debug(f"Raw Commit.commit: Message: {raw_commit.commit.message}, Author: {raw_commit.commit.author}, Commiter: {raw_commit.commit.committer}.")

        commits.append(Commit(raw_commit))

    return commits


def generate_change_url(repo: Repository, release: Optional[GitRelease], tag_name: str) -> str:
    if release:
        # If there is a latest release, create a URL pointing to commits since the latest release
        changelog_url = f"https://github.com/{repo.full_name}/compare/{release.tag_name}...{tag_name}"

    else:
        # If there is no latest release, create a URL pointing to all commits
        changelog_url = f"https://github.com/{repo.full_name}/commits/{tag_name}"

    logging.debug(f"Changelog URL: {changelog_url}")
    return changelog_url


def show_rate_limit(g: Github):
    rate_limit: RateLimit = g.get_rate_limit()

    if rate_limit.core.remaining < 10:
        reset_time = rate_limit.core.reset
        sleep_time = (reset_time - datetime.utcnow()).total_seconds() + 10
        logging.debug(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
    else:
        logging.debug(f"Rate limit: {rate_limit.core.remaining} remaining of {rate_limit.core.limit}")
