import re

from github.PullRequest import PullRequest


def extract_issue_numbers_from_body(pr: PullRequest) -> list[int]:
    """
    Extracts the numbers of the issues mentioned in the body of the pull request.

    :param pr: The pull request to extract the issue numbers from.
    :return: The numbers of the issues mentioned in the body of the pull request as a list of integers.
    """
    # Regex pattern to match issue numbers following keywords like "Close", "Fix", "Resolve"
    regex_pattern = re.compile(r'([Cc]los(e|es|ed)|[Ff]ix(es|ed)?|[Rr]esolv(e|es|ed))\s*#\s*([0-9]+)')

    # Extract all issue numbers from the PR body
    issue_matches = regex_pattern.findall(pr.body if pr.body else "")

    # Extract the issue numbers from the matches
    issue_numbers = [int(match[-1]) for match in issue_matches]

    return issue_numbers
