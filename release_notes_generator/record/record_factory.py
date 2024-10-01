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
This module contains the RecordFactory class which is responsible for generating records for release notes.
"""

import logging

from typing import Optional

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit

from release_notes_generator.model.isolated_commits_record import IsolatedCommitsRecord
from release_notes_generator.model.record import Record

from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.pull_reuqest_utils import extract_issue_numbers_from_body

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class RecordFactory:
    """
    A class used to generate records for release notes.
    """

    @staticmethod
    def generate(
        github: Github, repo: Repository, issues: list[Issue], pulls: list[PullRequest], commits: list[Commit]
    ) -> dict[int|str, Record]:
        """
        Generate records for release notes.

        @param github: The GitHub instance.
        @param repo: The repository.
        @param issues: The list of issues.
        @param pulls: The list of pull requests.
        @param commits: The list of commits.
        @return: A dictionary of records.
        """
        records: dict[int|str, Record] = {}
        pull_numbers = [pull.number for pull in pulls]

        real_issue_counts = len(issues)     # issues could contain PRs too - known behaviour from API
        for issue in issues:
            logger.debug("Hello for issue %s", issue)
            if issue.number not in pull_numbers:
                logger.debug("Calling create issue for number %s", issue.number)
                RecordFactory.__create_record_for_issue(records, repo, issue)
            else:
                logger.debug("Detected pr number %s among issues", issue.number)
                real_issue_counts -= 1

        for pull in pulls:
            if not extract_issue_numbers_from_body(pull):
                records[pull.number] = Record(repo)
                records[pull.number].register_pull_request(pull)
                logger.debug("Created record for PR %d: %s", pull.number, pull.title)
            else:
                RecordFactory.__register_pull_request(github, records, repo, pull)

        for commit in commits:
            logger.debug("DEBUG - Before - count of records is '%s', keys %s", len(records), records.keys())
            logger.debug("DEBUG - checking commit with sha: %s", commit.sha)

            isolated_r = RecordFactory.__register_commit_to_record(records, repo, commit)
            logger.debug("DEBUG - isolated record is '%s'", isolated_r)
            if isolated_r is not None:
                logger.debug("DEBUG - Adding new isolated record to records dict")
                records[commit.sha] = isolated_r

                if commit.sha in records.keys():
                    logger.debug("DEBUG - found in keys")
                else:
                    logger.debug("DEBUG - not found in keys")
            else:
                logger.debug("DEBUG - Adding normal record to records dict")

            logger.debug("DEBUG - After - count of records is '%s', keys %s", len(records), records.keys())

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected. %d of commits are isolated",
            len(records),
            real_issue_counts,
            len(pulls),
            len(commits),
            sum(isinstance(r, IsolatedCommitsRecord) for r in records)
        )
        return records

    @staticmethod
    def __create_record_for_issue(records: dict[int|str, Record], r: Repository, i: Issue):
        records[i.number] = Record(r, i)
        logger.debug("Created record for issue %d: %s", i.number, i.title)

    @staticmethod
    def __register_pull_request(github: Github, records: dict[int|str, Record], repo: Repository, pull: PullRequest):
        rate_limiter = GithubRateLimiter(github)
        safe_call = safe_call_decorator(rate_limiter)

        for parent_issue_number in extract_issue_numbers_from_body(pull):
            if parent_issue_number not in records:
                logger.warning(
                    "Detected PR %d linked to issue %d which is not in the list of received issues. "
                    "Fetching ...",
                    pull.number,
                    parent_issue_number,
                )
                parent_issue = safe_call(repo.get_issue)(parent_issue_number)
                if parent_issue is not None:
                    RecordFactory.__create_record_for_issue(records, repo, parent_issue)

            if parent_issue_number in records:
                records[parent_issue_number].register_pull_request(pull)
                logger.debug("Registering PR %d: %s to Issue %d", pull.number, pull.title, parent_issue_number)
            else:
                records[pull.number] = Record(repo)
                records[pull.number].register_pull_request(pull)
                logger.debug(
                    "Registering stand-alone PR %d: %s as mentioned Issue %d not found.",
                    pull.number,
                    pull.title,
                    parent_issue_number,
                )

    @staticmethod
    def __register_commit_to_record(records: dict[int|str, Record], repo: Repository, c: Commit) -> Optional[IsolatedCommitsRecord]:
        """
        Register a commit to a record if the commit is linked to an issue or a PR.

        @param c: The commit to register.
        @return: TODO
        """
        # try to register normal commit to existing records
        for record in records.values():
            if record.register_commit(c):
                return None

        # if not registered, create a new isolated record
        iso_record = IsolatedCommitsRecord(repo)
        iso_record.register_commit(c)
        logger.debug("DEBUG - Returning isolated record %s", iso_record)
        return iso_record
