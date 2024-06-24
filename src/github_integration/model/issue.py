from datetime import datetime
from typing import Optional


class Issue:
    def __init__(self, id: int, number: int, title: str, body: str, state: str, labels: list[str],
                 created_at: datetime):
        self.id: int = id
        self.number: int = number
        self.title: str = title
        self.body = body
        self.labels: list[str] = labels
        self.is_closed: bool = state == "closed"
        self.created_at: datetime = created_at

    def contains_labels(self, labels: list[str]) -> bool:
        for label in labels:
            if label in self.labels:
                return True
