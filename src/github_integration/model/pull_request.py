from typing import Optional


class PullRequest:
    def __init__(self, id: int, title: str, labels: list[str], linked_issue_id: Optional[int] = None):
        self.id = id
        # TODO
        self.number = id
        self.title = title
        self.labels = labels
        self.linked_issue_id = linked_issue_id
        self.url = "url-TODO"
