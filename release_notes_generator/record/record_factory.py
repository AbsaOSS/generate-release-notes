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

import logging

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit

from release_notes_generator.model.record import Record

from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from release_notes_generator.utils.pull_reuqest_utils import extract_issue_numbers_from_body


class RecordFactory:
    """
    A class used to generate records for release notes.
    """

    @staticmethod
    def generate(github: Github, repo: Repository, issues: list[Issue], pulls: list[PullRequest], commits: list[Commit]) -> dict[int, Record]:
        """
        Generates a dictionary of ReleaseNotesRecord instances.
        The key is the issue or pr number.

        :param github: The Github instance.
        :param repo: The Repository instance.
        :param issues: The list of Issue instances.
        :param pulls: The list of PullRequest instances.
        :param commits: The list of Commit instances.
        :return: The dictionary of ReleaseNotesRecord instances.
        """
        records = {}
        pull_numbers = [pull.number for pull in pulls]

        def create_record_for_issue(r: Repository, i: Issue):
            records[i.number] = Record(r, i)
            logging.debug(f"Created record for issue {i.number}: {i.title}")

        def register_pull_request(pull: PullRequest):
            for parent_issue_number in extract_issue_numbers_from_body(pull):
                if parent_issue_number not in records:
                    logging.warning(
                        f"Detected PR {pull.number} linked to issue {parent_issue_number} which is not in the list of received issues. Fetching ..."
                    )
                    parent_issue = safe_call(repo.get_issue)(parent_issue_number)
                    if parent_issue is not None:
                        create_record_for_issue(repo, parent_issue)

                if parent_issue_number in records:
                    records[parent_issue_number].register_pull_request(pull)
                    logging.debug(
                        f"Registering PR {pull.number}: {pull.title} to Issue {parent_issue_number}"
                    )
                else:
                    records[pull.number] = Record(repo)
                    records[pull.number].register_pull_request(pull)
                    logging.debug(
                        f"Registering stand-alone PR {pull.number}: {pull.title} as mentioned Issue {parent_issue_number} not found."
                    )

        def register_commit_to_record(commit: Commit):
            for record in records.values():
                if record.is_commit_sha_present(commit.sha):
                    record.register_commit(commit)
                    return True
            return False

        rate_limiter = GithubRateLimiter(github)
        safe_call = safe_call_decorator(rate_limiter)

        for issue in issues:
            if issue.number not in pull_numbers:
                create_record_for_issue(repo, issue)

        for pull in pulls:
            if not extract_issue_numbers_from_body(pull):
                records[pull.number] = Record(repo)
                records[pull.number].register_pull_request(pull)
                logging.debug(f"Created record for PR {pull.number}: {pull.title}")
            else:
                register_pull_request(pull)

        detected_prs_count = sum(register_commit_to_record(commit) for commit in commits)

        logging.info(f"Generated {len(records)} records from {len(issues)} issues and {len(pulls)} PRs, with {detected_prs_count} commits detected.")
        return records
