class Chapter:
    def __init__(self, title: str = "", labels: list[str] = list):
        self.title: str = title
        self.labels: list[str] = labels
        self.rows: dict[int, str] = {}

    def add_row(self, number: int, row: str):
        self.rows[number] = row

    def to_string(self, sort_ascending: bool = True):
        sorted_items = sorted(self.rows.items(), key=lambda item: item[0], reverse=not sort_ascending)
        return f"### {self.title}\n" + "\n".join([f"{value}" for key, value in sorted_items]) + "\n"
