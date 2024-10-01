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

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit
from jsonschema.benchmarks.issue232 import issue232
from sympy.strategies.branch import debug

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
    ) -> dict[int, Record]:
        """
        Generate records for release notes.

        @param github: The GitHub instance.
        @param repo: The repository.
        @param issues: The list of issues.
        @param pulls: The list of pull requests.
        @param commits: The list of commits.
        @return: A dictionary of records.
        """
        records = {}
        pull_numbers = [pull.number for pull in pulls]

        def create_record_for_issue(r: Repository, i: Issue):
            records[i.number] = Record(r, i)
            logger.debug("Created record for issue %d: %s", i.number, i.title)

        def register_pull_request(pull: PullRequest):
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
                        create_record_for_issue(repo, parent_issue)

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

        def register_commit_to_record(commit: Commit) -> bool:
            """
            Register a commit to a record if the commit is linked to an issue or a PR.

            @param commit: The commit to register.
            @return: True if the commit was registered to a record, False otherwise
            """
            for record in records.values():
                if record.register_commit(commit):
                    return True

            logger.warning(f"Commit '{commit.url}' registered to any record.")
            return False

        rate_limiter = GithubRateLimiter(github)
        safe_call = safe_call_decorator(rate_limiter)

        real_issue_counts = len(issues)     # issues could contain PRs too - known behaviour from API
        for issue in issues:
            logger.debug("Hello for issue %s", issue)
            if issue.number not in pull_numbers:
                logger.debug("Calling create issue for number %s", issue.number)
                create_record_for_issue(repo, issue)
            else:
                logger.debug("Detected issue number among pulls one %s", issue.number)
                real_issue_counts -= 1
                logger.debug("New count of issues is %s", real_issue_counts)

        for pull in pulls:
            if not extract_issue_numbers_from_body(pull):
                records[pull.number] = Record(repo)
                records[pull.number].register_pull_request(pull)
                logger.debug("Created record for PR %d: %s", pull.number, pull.title)
            else:
                register_pull_request(pull)

        detected_prs_count = sum(register_commit_to_record(commit) for commit in commits)

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected.",
            len(records),
            real_issue_counts,
            len(pulls),
            detected_prs_count,
        )
        return records
