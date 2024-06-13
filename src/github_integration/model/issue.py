from typing import Optional


class Issue:
    def __init__(self, id: int, title: str, labels: list[str], is_closed: bool, linked_pr_id: Optional[int] = None):
        self.id = id
        self.title = title
        self.labels = labels
        self.is_closed = is_closed
        self.linked_pr_id = linked_pr_id
