from datetime import datetime
from typing import Optional


class PullRequest:
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

        self.url = url
        self.issue_url = issue_url
        self.html_url = html_url
        self.patch_url = patch_url
        self.diff_url = diff_url
