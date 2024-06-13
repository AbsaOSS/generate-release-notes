from typing import Optional


class PullRequest:
    def __init__(self, id: int, title: str, linked_issue_id: Optional[int] = None):
        self.id = id
        self.title = title
        self.linked_issue_id = linked_issue_id
