#
# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This module contains logic for mining data from GitHub, including issues, pull requests, commits, and releases.
"""
import logging
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed, CancelledError
from typing import Optional, Callable

import semver
from github import Github
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.data.utils.bulk_sub_issue_collector import CollectorConfig, BulkSubIssueCollector
from release_notes_generator.model.record.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.model.record.pull_request_record import PullRequestRecord
from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.record_utils import get_id, parse_issue_id

logger = logging.getLogger(__name__)


class DataMiner:
    """
    Class responsible for mining data from GitHub.
    """

    def __init__(self, github_instance: Github, rate_limiter: GithubRateLimiter):
        self.github_instance = github_instance
        self._safe_call = safe_call_decorator(rate_limiter)

    def mine_data(self) -> MinedData:
        """
        Mines data from GitHub, including repository information, issues, pull requests, commits, and releases.
        """
        logger.info("Starting data mining from GitHub...")
        repo: Optional[Repository] = self.get_repository(ActionInputs.get_github_repository())
        if repo is None:
            raise ValueError("Repository not found")

        data = MinedData(repo)
        data.release = self.get_latest_release(repo)

        self._get_issues(data)

        # pulls and commits, and then reduce them by the latest release since time
        pull_requests = list(
            self._safe_call(repo.get_pulls)(state=PullRequestRecord.PR_STATE_CLOSED, base=repo.default_branch)
        )
        data.pull_requests = {pr: data.home_repository for pr in pull_requests}
        if data.since:
            commits = list(self._safe_call(repo.get_commits)(since=data.since))
        else:
            commits = list(self._safe_call(repo.get_commits)())
        data.commits = {c: data.home_repository for c in commits}

        logger.info("Initial data mining from GitHub completed.")

        logger.info("Filtering duplicated issues from the list of issues...")
        de_duplicated_data = self.__filter_duplicated_issues(data)
        logger.info("Filtering duplicated issues from the list of issues finished.")

        return de_duplicated_data

    def mine_missing_sub_issues(self, data: MinedData) -> tuple[dict[Issue, Repository], dict[str, list[PullRequest]]]:
        """
        Mines missing sub-issues from GitHub.
        Parameters:
            data (MinedData): The mined data containing origin sets of issues and pull requests.
        Returns:
            dict[Issue, Repository]: A dictionary mapping fetched issues to their repositories.
            dict[str, list[PullRequest]]: A dictionary mapping fetched cross-repo issue with its pull requests.
        """
        logger.info("Mapping sub-issues...")
        data.parents_sub_issues = self._scan_sub_issues_for_parents([get_id(i, r) for i, r in data.issues.items()])

        logger.info("Fetch all repositories in cache...")
        self._fetch_all_repositories_in_cache(data)

        logger.info("Fetching missing issues...")
        fetched_issues = self._fetch_missing_issues(data)

        logger.info("Getting PRs and Commits for missing issues...")
        prs_of_fetched_cross_repo_issues = self._fetch_prs_for_fetched_cross_issues(fetched_issues)

        return fetched_issues, prs_of_fetched_cross_repo_issues

    def _make_bulk_sub_issue_collector(self) -> BulkSubIssueCollector:
        cfg = CollectorConfig(verify_tls=False)
        return BulkSubIssueCollector(ActionInputs.get_github_token(), cfg)

    def _scan_sub_issues_for_parents(self, parents_to_check: list[str]) -> dict[str, list[str]]:
        """
        Scan sub-issues for parents.

        Parameters:
            parents_to_check (list[str]): List of parent issue IDs to check.
        Returns:
            dict[str, list[str]]: A dictionary mapping parent issue IDs to their sub-issue IDs.
        """
        new_parent_ids: list[str] = parents_to_check
        bulk_sub_issue_collector = self._make_bulk_sub_issue_collector()
        parents_sub_issues: dict[str, list[str]] = {}

        # run in cycle to get all levels of hierarchy
        while new_parent_ids:
            logger.debug("Scanning sub-issues with parent ids: %s", new_parent_ids)
            new_parent_ids = bulk_sub_issue_collector.scan_sub_issues_for_parents(new_parent_ids)
            parents_sub_issues.update(bulk_sub_issue_collector.parents_sub_issues)

        return parents_sub_issues

    def _fetch_all_repositories_in_cache(self, data: MinedData) -> None:
        def _check_repo_and_add(iid: str):
            org, repo, _num = parse_issue_id(iid)
            full_name = f"{org}/{repo}"
            if data.get_repository(full_name) is None:
                new_repo = self._fetch_repository(full_name=full_name)
                if new_repo is None:
                    logger.error("Repository fetch returned None for %s", full_name)
                    return

                data.add_repository(new_repo)
                logger.debug("Fetched missing repository: %s", full_name)

        # check keys
        for iid in data.parents_sub_issues.keys():
            _check_repo_and_add(iid)

        # check values
        for ids in data.parents_sub_issues.values():
            for iid in ids:
                _check_repo_and_add(iid)

    def _fetch_missing_issues(
        self,
        data: MinedData,
        max_workers: int = 8,
    ) -> dict[Issue, Repository]:
        """
        Parallel version of _fetch_missing_issues.
        Threaded to speed up GitHub API calls while avoiding data races.
        """
        fetched_issues: dict[Issue, Repository] = {}
        origin_issue_ids = {get_id(i, r) for i, r in data.issues.items()}

        # Worklist: only parents not already present among origin_issue_ids
        to_check: list[str] = [pid for pid in data.parents_sub_issues.keys() if pid not in origin_issue_ids]

        # Collect IDs to remove (those that don't meet criteria) and errors
        issues_for_remove: set[str] = set()
        errors: list[tuple[str, str]] = []  # (parent_id, error_msg)

        if not to_check:
            logger.debug("Fetched 0 missing issues (nothing to check).")
            return fetched_issues

        # Thread pool
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="fetch-issue") as ex:
            futures = {ex.submit(self.__worker, pid, data, self._safe_call): pid for pid in to_check}
            for fut in as_completed(futures):
                parent_id = futures[fut]
                try:
                    pid, issue, repo, err = fut.result()
                except CancelledError as e:
                    errors.append((parent_id, f"worker cancelled: {e}"))
                    continue
                except TimeoutError as e:
                    errors.append((parent_id, f"worker timed out: {e}"))
                    continue
                except Exception as e:  # pylint: disable=broad-exception-caught
                    errors.append((parent_id, f"worker crash: {e}"))
                    continue

                if err:
                    logger.error("Error fetching %s: %s", pid, err)

                if issue is None:
                    # Did not meet criteria => schedule removal
                    issues_for_remove.add(pid)
                else:
                    # Add to results
                    fetched_issues[issue] = repo  # type: ignore[assignment]

        # Apply removals AFTER parallelism to avoid concurrent mutation
        if issues_for_remove:
            for iid in issues_for_remove:
                data.parents_sub_issues.pop(iid, None)
                for sub_issues in data.parents_sub_issues.values():
                    # parents_sub_issues can be dict[str, list[str]] or now dict[str, str] per your later change;
                    # if it's list[str], this removal is ok; if changed to str, guard it.
                    if isinstance(sub_issues, list) and iid in sub_issues:
                        sub_issues.remove(iid)

        logger.debug(
            "Fetched %d missing issues in parallel (removed %d).",
            len(fetched_issues),
            len(issues_for_remove),
        )

        return fetched_issues

    @staticmethod
    def __should_fetch(issue: Issue, data: MinedData) -> bool:
        # Mirrors original logic
        if not issue.closed_at:
            return False
        if data.since:
            # if since > closed_at => skip
            if issue.closed_at and data.since > issue.closed_at:
                return False
        return True

    @staticmethod
    def __worker(
        parent_id: str, data: MinedData, safe_call: Callable
    ) -> tuple[str, Optional[Issue], Optional[Repository], Optional[str]]:
        """
        Returns (parent_id, issue|None, repo|None, error|None)
        - issue=None & error=None  => mark for remove (didn't meet criteria)
        - issue=None & error!=None => log error
        """
        try:
            org, repo, num = parse_issue_id(parent_id)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return (parent_id, None, None, f"parse_issue_id failed: {e}")

        r = data.get_repository(f"{org}/{repo}")
        if r is None:
            return (parent_id, None, None, f"Cannot get repository for {org}/{repo}")

        # GitHub call
        try:
            logger.debug("Fetching missing issue: %s", parent_id)
            issue = safe_call(r.get_issue)(num)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return (parent_id, None, r, f"get_issue failed: {e}")

        if issue is None:
            return (parent_id, None, r, "Issue not found")

        # Criteria
        if DataMiner.__should_fetch(issue, data):
            return (parent_id, issue, r, None)

        return (parent_id, None, r, None)  # means: mark for remove

    def _fetch_repository(self, full_name: str) -> Optional[Repository]:
        """
        Fetch a repository by its full name.

        Returns:
            Optional[Repository]: The GitHub repository if found, None otherwise.
        """
        repo: Optional[Repository] = self._safe_call(self.github_instance.get_repo)(full_name)
        if repo is None:
            logger.error("Repository not found: %s", full_name)
            return None
        return repo

    def check_repository_exists(self) -> bool:
        """
        Checks if the specified GitHub repository exists.

        Returns:
            bool: True if the repository exists, False otherwise.
        """
        repo: Repository = self._safe_call(self.github_instance.get_repo)(ActionInputs.get_github_repository())
        if repo is None:
            logger.error("Repository not found: %s", ActionInputs.get_github_repository())
            return False
        return True

    def get_repository(self, full_name: str) -> Optional[Repository]:
        """
        Retrieves the specified GitHub repository.

        Returns:
            Optional[Repository]: The GitHub repository if found, None otherwise.
        """
        repo: Optional[Repository] = self._safe_call(self.github_instance.get_repo)(full_name)
        if repo is None:
            logger.error("Repository not found: %s", full_name)
            return None
        return repo

    def get_latest_release(self, repository: Repository) -> Optional[GitRelease]:
        """
        Get the latest release of the repository.

        @param repository: The repository to get the latest release from.
        @return: The latest release of the repository, or None if no releases are found.
        """

        rls: Optional[GitRelease] = None

        # check if from-tag name is defined
        if ActionInputs.is_from_tag_name_defined():
            logger.info("Getting latest release by from-tag name %s", ActionInputs.get_from_tag_name())
            rls = self._safe_call(repository.get_release)(ActionInputs.get_from_tag_name())

            if rls is None:
                logger.error(
                    "Latest release not found for received from-tag %s. Ending!", ActionInputs.get_from_tag_name()
                )
                sys.exit(1)

        else:
            logger.info("Getting latest release by semantic ordering (could not be the last one by time).")
            gh_releases: list = list(self._safe_call(repository.get_releases)())
            rls = self.__get_latest_semantic_release(gh_releases)

            if rls is None:
                logger.info("Latest release not found for %s. 1st release for repository!", repository.full_name)
                return None

        if rls is not None:
            logger.debug(
                "Latest release with tag:'%s' created_at: %s, published_at: %s",
                rls.tag_name,
                rls.created_at,
                rls.published_at,
            )

        return rls

    def _get_issues(self, data: MinedData) -> None:
        """
        Populate data.issues.

        Logic:
          - If no release: fetch all issues.
          - If release exists: fetch issues updated since the release timestamp AND all currently open issues
            (to include long-lived open issues not updated recently). De-duplicate by issue.number.
        """
        assert data.home_repository is not None, "Repository must not be None"
        logger.info("Fetching issues from repository...")

        if data.release is None:
            issues = list(self._safe_call(data.home_repository.get_issues)(state=IssueRecord.ISSUE_STATE_ALL))
            data.issues = {i: data.home_repository for i in issues}

            logger.info("Fetched %d issues", len(data.issues.items()))
            return

        # Derive 'since' from release
        prefer_published = ActionInputs.get_published_at()
        # Ensure data.since is only set if a valid datetime is available
        data.since = None
        if prefer_published and getattr(data.release, "published_at", None) is not None:
            data.since = data.release.published_at  # type: ignore[assignment]
        elif getattr(data.release, "created_at", None) is not None:
            data.since = data.release.created_at  # type: ignore[assignment]

        issues_since = self._safe_call(data.home_repository.get_issues)(
            state=IssueRecord.ISSUE_STATE_ALL,
            since=data.since,
        )
        open_issues = self._safe_call(data.home_repository.get_issues)(
            state=IssueRecord.ISSUE_STATE_OPEN,
        )

        issues_since = list(issues_since or [])
        open_issues = list(open_issues or [])

        by_number = {}
        for issue in issues_since:
            num = getattr(issue, "number", None)
            if num is not None and num not in by_number:
                by_number[num] = issue
        for issue in open_issues:
            num = getattr(issue, "number", None)
            if num is not None and num not in by_number:
                by_number[num] = issue

        data.issues = {i: data.home_repository for i in list(by_number.values())}
        logger.info("Fetched %d issues (deduplicated).", len(data.issues))

    @staticmethod
    def __get_latest_semantic_release(releases) -> Optional[GitRelease]:
        published_releases = [release for release in releases if not release.draft and not release.prerelease]
        latest_version: Optional[semver.Version] = None
        rls: Optional[GitRelease] = None

        for release in published_releases:
            try:
                version_str = release.tag_name.lstrip("v")
                current_version: Optional[semver.Version] = semver.VersionInfo.parse(version_str)
            except ValueError:
                logger.error("Skipping invalid value of version tag: %s", release.tag_name)
                continue
            except TypeError as error:
                logger.error("Skipping invalid type of version tag: %s | Error: %s", release.tag_name, str(error))
                logger.error("Full traceback:\n%s", traceback.format_exc())
                continue

            if latest_version is None or current_version > latest_version:  # type: ignore[operator]
                # mypy: check for None is done first
                latest_version = current_version
                rls = release

        return rls

    @staticmethod
    def __filter_duplicated_issues(data: MinedData) -> "MinedData":
        """
        Filters out duplicated issues from the list of issues.
        This method address problem in output of GitHub API where issues list contains PR values.

        Parameters:
            data (MinedData): The mined data containing issues and pull requests.

        Returns:
            MinedData: The mined data with duplicated issues removed.
        """
        filtered_issues = {issue: repo for issue, repo in data.issues.items() if "/issues/" in issue.html_url}

        logger.debug("Duplicated issues removed: %s", len(data.issues.items()) - len(filtered_issues.items()))

        data.issues = filtered_issues
        return data

    def _fetch_prs_for_fetched_cross_issues(self, issues: dict[Issue, Repository]) -> dict[str, list[PullRequest]]:
        prs_of_cross_repo_issues: dict[str, list[PullRequest]] = {}
        for i, repo in issues.items():
            prs_of_cross_repo_issues[iid := get_id(i, repo)] = []
            try:
                for ev in i.get_timeline():  # timeline includes cross-references
                    if ev.event == "cross-referenced" and getattr(ev, "source", None):
                        # <- this is a github.Issue.Issue
                        src_issue = ev.source.issue  # type: ignore[union-attr]
                        if getattr(src_issue, "pull_request", None):
                            pr = src_issue.as_pull_request()  # github.PullRequest.PullRequest
                            prs_of_cross_repo_issues[iid].append(pr)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to fetch timeline events for issue %s: %s", iid, str(e))

        return prs_of_cross_repo_issues
