class Chapter:
    def __init__(self, title: str = "", labels: list[str] = list, empty_message: str="No entries detected."):
        self.title: str = title
        self.labels: list[str] = labels
        self.rows: dict[int, str] = {}
        self.empty_message = empty_message

    def add_row(self, number: int, row: str):
        self.rows[number] = row

    def to_string(self, sort_ascending: bool = True, print_empty_chapters: bool = True) -> str:
        sorted_items = sorted(self.rows.items(), key=lambda item: item[0], reverse=not sort_ascending)

        if len(sorted_items) == 0:
            if not print_empty_chapters:
                return ""
            return f"### {self.title}\n{self.empty_message}\n\n"

        return f"### {self.title}\n" + "".join([f"{value}\n" for key, value in sorted_items]) + "\n"
