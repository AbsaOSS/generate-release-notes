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


class Chapter:
    """
    A class used to represent a chapter in the release notes.
    """

    def __init__(self, title: str = "", labels: list[str] = None, empty_message: str = "No entries detected."):
        """
        Constructs all the necessary attributes for the Chapter object.

        :param title: The title of the chapter.
        :param labels: A list of labels associated with the chapter.
        :param empty_message: The message to display when the chapter is empty.
        """
        self.title: str = title
        if labels is None:
            self.labels = []
        else:
            self.labels: list[str] = labels
        self.rows: dict[int, str] = {}
        self.empty_message = empty_message

    def add_row(self, number: int, row: str):
        """
        Adds a row to the chapter.

        :param number: The number of the row.
        :param row: The row to add.
        """
        self.rows[number] = row

    def to_string(self, sort_ascending: bool = True, print_empty_chapters: bool = True) -> str:
        """
        Converts the chapter to a string.

        :param sort_ascending: A boolean indicating whether to sort the rows in ascending order.
        :param print_empty_chapters: A boolean indicating whether to print empty chapters.
        :return: The chapter as a string.
        """
        sorted_items = sorted(self.rows.items(), key=lambda item: item[0], reverse=not sort_ascending)

        if len(sorted_items) == 0:
            if not print_empty_chapters:
                return ""
            return f"### {self.title}\n{self.empty_message}"

        result = f"### {self.title}\n" + "".join([f"- {value}\n" for key, value in sorted_items])
        # Note: do not return with '\n' on start end end position of string - keep formating on superior level
        return result.strip()
