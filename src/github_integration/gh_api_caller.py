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
        return g.get_repo(repository_id)
    except Exception as e:
        if "Not Found" in str(e):
            print(f"Repository not found: {repository_id}")
            return None
        else:
            print(f"Fetching repository failed for {repository_id}: {str(e)}")
            return None


def fetch_latest_release(repo: Repository) -> Optional[GitRelease]:
    try:
        release = repo.get_latest_release()
        print(f"Found latest release: {release.tag_name}, created at: {release.created_at}, "
                      f"published at: {release.published_at}")
        return release

    except Exception as e:
        if "Not Found" in str(e):
            print(f"Latest release not found for {repo.owner}/{repo.name}. 1st release for repository!")
            return None
        else:
            print(f"Fetching latest release failed for {repo.owner}/{repo.name}: {str(e)}. "
                            f"Expected first release for repository.")
            return None


def fetch_closed_issues(repo: Repository, release: Optional[GitRelease]) -> list[Issue]:
    # TODO add input controls - slow implementation
    if release is None:
        issues = repo.get_issues(state='closed')
    else:
        issues = repo.get_issues(state='closed', since=release.published_at)

    parsed_issues = []
    for issue in list(issues):
        linked_pr_id = None
        # if issue.pull_request:
        #     linked_pr_id = int(issue.pull_request.url.split('/')[-1])
        parsed_issues.append(Issue(
            id=issue.id,
            title=issue.title,
            labels=[label.name for label in issue.labels],
            is_closed=True,
            linked_pr_id=linked_pr_id
        ))

    print(f"Found {len(parsed_issues)} closed issues for {repo.full_name}")
    return parsed_issues


def fetch_finished_pull_requests(repo: Repository) -> list[PullRequest]:
    # TODO - decide: pulls = repo.get_pulls(state='closed', sort='created', direction='desc')
    pulls = repo.get_pulls(state='closed')

    pull_requests = []
    for pull in list(pulls):
        pr = PullRequest(
            id=pull.id,
            title=pull.title,
            linked_issue_id=pull.issue_url.split('/')[-1] if pull.issue_url else None
        )
        pull_requests.append(pr)

    print(f"Found {len(pull_requests)} PRs for {repo.full_name}")
    return pull_requests


def generate_change_url(repo: Repository, release: Optional[GitRelease], tag_name: str) -> str:
    if release:
        # If there is a latest release, create a URL pointing to commits since the latest release
        changelog_url = f"https://github.com/{repo.owner}/{repo.name}/compare/{release.tag_name}...{tag_name}"

    else:
        # If there is no latest release, create a URL pointing to all commits
        changelog_url = f"https://github.com/{repo.owner}/{repo.name}/commits/{tag_name}"

    print(f"Changelog URL: {changelog_url}")
    return changelog_url


def show_rate_limit(g: Github):
    rate_limit: RateLimit = g.get_rate_limit()

    if rate_limit.core.remaining < 10:
        reset_time = rate_limit.core.reset
        sleep_time = (reset_time - datetime.utcnow()).total_seconds() + 10
        print(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
    else:
        print(f"Rate limit: {rate_limit.core.remaining} remaining of {rate_limit.core.limit}")
