import re
from datetime import datetime
from typing import Optional


class PullRequest:
    PR_STATE_CLOSED = "closed"
    PR_STATE_MERGED = "merged"

    def __init__(self, id: int, number: int, title: str, labels: list[str], body: str, state: str,
                 created_at: datetime, updated_at: datetime, closed_at: Optional[datetime],
                 merged_at: Optional[datetime], milestone: Optional[str],
                 url: str, issue_url: Optional[str], html_url: Optional[str], patch_url: Optional[str], diff_url: Optional[str]):
        self.id = id
        self.number = number
        self.title = title
        self.labels = labels            # TODO - is additional hiden API call needed to get labels?
        self.state = state
        # self.user = user              # TODO - is support needed ?
        # self.assignee = assignee      # TODO - is support needed ? often no assigned user
        self.body = body

        self.created_at = created_at
        self.updated_at = updated_at
        self.closed_at = closed_at
        self.merged_at = merged_at

        self.milestone = milestone

        # TODO - these values have to be composed from known paths and PR values
        self.url = url
        self.issue_url = issue_url
        self.html_url = html_url
        self.patch_url = patch_url
        self.diff_url = diff_url

        self.__body_contains_issue_mention = False
        self.__mentioned_issues: list[int] = self.extract_issue_numbers_from_body()

    @property
    def is_merged(self):
        return self.merged_at is not None and self.state == self.PR_STATE_MERGED

    @property
    def is_closed(self):
        return self.closed_at is not None and self.state == self.PR_STATE_CLOSED

    @property
    def body_contains_issue_mention(self):
        return self.__body_contains_issue_mention

    def extract_issue_numbers_from_body(self) -> list[int]:
        # Regex pattern to match issue numbers following keywords like "Close", "Fix", "Resolve"
        regex_pattern = re.compile(r'([Cc]los(e|es|ed)|[Ff]ix(es|ed)?|[Rr]esolv(e|es|ed))\s*#\s*([0-9]+)')

        # Extract all issue numbers from the PR body
        issue_matches = regex_pattern.findall(self.body)

        # Extract the issue numbers from the matches
        issue_numbers = [int(match[-1]) for match in issue_matches]

        if not self.__body_contains_issue_mention and len(issue_numbers) > 0:
            self.__body_contains_issue_mention = True

        return issue_numbers
