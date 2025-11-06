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
This module contains utility functions for extracting and fetching issue numbers from pull requests.
"""

import re
from functools import lru_cache

from github import GithubException
from github.Requester import Requester
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import ISSUES_FOR_PRS, LINKED_ISSUES_MAX


def extract_issue_numbers_from_body(pr: PullRequest, repository: Repository) -> set[str]:
    """
    Extracts the numbers of the issues mentioned in the body of the pull request.

    Parameters:
        pr (PullRequest): The pull request to extract numbers from.

    Returns:
        Set of issue numbers mentioned in the pull request body.
    """
    # Regex pattern to match issue numbers following keywords like "Close", "Fix", "Resolve"
    regex_pattern = re.compile(r"([Cc]los(e|es|ed)|[Ff]ix(es|ed)?|[Rr]esolv(e|es|ed))\s*#\s*([0-9]+)")

    # Extract all issue numbers from the PR body
    issue_matches = regex_pattern.findall(pr.body if pr.body else "")

    # Extract the issue numbers from the matches
    issue_numbers = {int(match[-1]) for match in issue_matches}
    issue_ids = {f"{repository.full_name}#{number}" for number in issue_numbers}

    return issue_ids


@lru_cache(maxsize=1024)
def get_issues_for_pr(pull_number: int, requester: Requester) -> set[str]:
    """Fetch closing issue numbers for a PR via GitHub GraphQL and return them as a set."""
    owner = ActionInputs.get_github_owner()
    name = ActionInputs.get_github_repo_name()
    query = ISSUES_FOR_PRS.format(
        number=pull_number,
        owner=owner,
        name=name,
        first=LINKED_ISSUES_MAX,
    )
    headers = {
        "Authorization": f"Bearer {ActionInputs.get_github_token()}",
        "Content-Type": "application/json",
    }

    try:
        headers, payload = requester.graphql_query(query, headers)
    except GithubException as e:
        # e.status (int), e.data (dict/str) often contains useful details
        raise RuntimeError(f"GitHub HTTP error {getattr(e, 'status', '?')}: {getattr(e, 'data', e)}") from e

    if not isinstance(payload, dict):
        raise RuntimeError(f"Malformed response payload type: {type(payload)}")

    # GraphQL-level errors come inside a successful HTTP 200
    if "errors" in payload:
        messages = "; ".join(err.get("message", str(err)) for err in payload["errors"])
        raise RuntimeError(f"GitHub GraphQL errors: {messages}")

    if "data" not in payload:
        raise RuntimeError("Malformed GraphQL response: missing 'data'")

    test_set = {
        f"{owner}/{name}#{node['number']}"
        for node in payload["data"]["repository"]["pullRequest"]["closingIssuesReferences"]["nodes"]
    }

    return test_set
