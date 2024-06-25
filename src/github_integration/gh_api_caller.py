import logging
import time

from datetime import datetime
from typing import Optional

from github import Github
from github.GitRelease import GitRelease
from github.RateLimit import RateLimit
from github.Repository import Repository

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
        # logging.debug(f"Processing issue {issue.number}, title: {issue.title}")
        # Hint: be careful here what you are passing to the Issue constructor
        #   when selected value not received in first API then second wave
        #   will be called !!!!
        # TODO - how about to do not parse the issue and keep the origin with ready to use link to GH API?
        parsed_issues.append(Issue(
            id=issue.id,
            number=issue.number,
            title=issue.title,
            labels=[label.name for label in issue.labels],
            body=issue.body,
            state=issue.state,
            created_at=datetime.now()
        ))

    return parsed_issues


def fetch_finished_pull_requests(repo: Repository) -> list[PullRequest]:
    # TODO - decide: pulls = repo.get_pulls(state='closed', sort='created', direction='desc')
    logging.info(f"Fetching all closed PRs for {repo.full_name}")
    pulls = repo.get_pulls(state='closed')

    pull_requests = []
    logging.info(f"Found {len(list(pulls))} PRs for {repo.full_name}")
    for pull in list(pulls):
        # logging.debug(f"Processing PR {pull.number}, title: {pull.title}")
        pr = PullRequest(
            id=pull.id,
            number=pull.number,
            title=pull.title,
            labels=[label.name for label in pull.labels],
            body=pull.body if pull.body else "",
            state=pull.state,
            created_at=pull.created_at,
            updated_at=pull.updated_at,
            closed_at=pull.closed_at if pull.closed_at else None,
            merged_at=pull.merged_at if pull.merged_at else None,
            milestone=pull.milestone.title if pull.milestone else None,
            url=pull.url,
            issue_url=pull.issue_url if pull.issue_url else None,
            html_url=pull.html_url if pull.html_url else None,
            patch_url=pull.patch_url if pull.patch_url else None,
            diff_url=pull.diff_url if pull.diff_url else None,
            assignee=pull.assignee.login if pull.assignee else None
        )
        pull_requests.append(pr)

    return pull_requests


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
