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
This module contains utility functions for extracting issue numbers from pull request bodies.
"""

import re
from functools import lru_cache

import requests
from github.PullRequest import PullRequest

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import ISSUES_FOR_PRS, LINKED_ISSUES_MAX


def extract_issue_numbers_from_body(pr: PullRequest) -> set[int]:
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

    return issue_numbers


@lru_cache(maxsize=1024)
def get_issues_for_pr(pull_number: int) -> set[int]:
    """Update the placeholder values and format the graphQL query"""
    github_api_url = "https://api.github.com/graphql"
    query = ISSUES_FOR_PRS.format(
        number=pull_number,
        owner=ActionInputs.get_github_owner(),
        name=ActionInputs.get_github_repo_name(),
        first=LINKED_ISSUES_MAX,
    )
    headers = {
        "Authorization": f"Bearer {ActionInputs.get_github_token()}",
        "Content-Type": "application/json",
    }

    response = requests.post(github_api_url, json={"query": query}, headers=headers, verify=False, timeout=10)
    response.raise_for_status()  # Raise an error for HTTP issues
    data = response.json()
    if "errors" in data and data["errors"]:
        raise RuntimeError(f"GitHub GraphQL errors: {data['errors']}")
    numbers = {
        node["number"]
        for node in data["data"]["repository"]["pullRequest"]["closingIssuesReferences"]["nodes"]
    }

    return numbers
