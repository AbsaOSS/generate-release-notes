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

"""
Utilities for working with GitHub issue/PR/commit identifiers.
"""

import logging
import re
from functools import lru_cache
from typing import Any, cast

from github.Commit import Commit
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs

logger = logging.getLogger(__name__)

ISSUE_ID_RE = re.compile(r"^(?P<org>[^/\s]+)/(?P<repo>[^#\s]+)#(?P<num>\d+)$")


class IssueIdParseError(ValueError):
    """Raised when an issue ID cannot be parsed."""


def get_id(obj, repository: Repository) -> str:
    """
    Get a stable identifier for an Issue, PullRequest, or Commit within a given repository.
    Parameters:
        obj: The object to get the ID for (Issue, PullRequest, or Commit).
        repository: The Repository the object belongs to.
    Returns:
        A string identifier for the object.
    """
    if isinstance(obj, Issue):
        issue = cast(Issue, obj)
        return _entity_id(repository.full_name, issue.number)

    if isinstance(obj, PullRequest):
        pr = cast(PullRequest, obj)
        return _entity_id(repository.full_name, pr.number)

    if isinstance(obj, Commit):
        commit = cast(Commit, obj)
        return f"{commit.sha}"

    return str(obj)


@lru_cache(maxsize=2048)
def _entity_id(repo_full_name: str, number: int) -> str:
    """Format 'org/repo#123' from components."""
    return f"{repo_full_name}#{number}"


def parse_issue_id(issue_id: str) -> tuple[str, str, int]:
    """
    Parse 'org/repo#123' -> (org, repo, 123).
    Raises IssueIdParseError on malformed input.
    """
    m = ISSUE_ID_RE.match(issue_id.strip())
    if not m:
        raise IssueIdParseError(f"Invalid issue id '{issue_id}', expected 'org/repo#number'")
    return m.group("org"), m.group("repo"), int(m.group("num"))


def format_issue_id(org: str, repo: str, number: int) -> str:
    """Format 'org/repo#123' from components."""
    return f"{org}/{repo}#{number}"


def get_rls_notes_default(body: str, line_marks: list[str], detection_regex: re.Pattern[str]) -> str:
    """
    Extracts release notes from the pull request body based on the provided line marks and detection regex.
    Parameters:
        body: The body of the issue or pull request from which to extract release notes.
        line_marks (list[str]): A list of characters that indicate the start of a release notes section.
        detection_regex (re.Pattern[str]): A regex pattern to detect the start of the release notes section.
    Returns:
        str: The extracted release notes as a string. If no release notes are found, returns an empty string.
    """
    # TODO - Refactor with issue #190
    match body:
        case None | "":
            return ""

    release_notes_lines = []

    found_section = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if not found_section:
            if detection_regex.search(line):
                found_section = True
            continue

        if stripped[0] in line_marks:
            release_notes_lines.append(f"  {line.rstrip()}")
        else:
            break

    return "\n".join(release_notes_lines) + ("\n" if release_notes_lines else "")


def get_rls_notes_code_rabbit(body: str, line_marks: list[str], cr_detection_regex: re.Pattern[str]) -> str:
    """
    Extracts release notes from a pull request body formatted for Code Rabbit.
    Parameters:
        body: The body of the issue or pull request from which to extract release notes.
        line_marks (list[str]): A list of characters that indicate the start of a release notes section.
        cr_detection_regex (re.Pattern[str]): A regex pattern to detect the start of the Code
    Returns:
        str: The extracted release notes as a string. If no release notes are found, returns an empty string.
    """
    # TODO - Refactor with issue #190
    match body:
        case None | "":
            return ""

    lines = body.splitlines()
    ignore_groups: list[str] = ActionInputs.get_coderabbit_summary_ignore_groups()
    release_notes_lines = []

    inside_section = False
    skipping_group = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if not inside_section:
            if cr_detection_regex.search(line):
                inside_section = True
            continue

        if inside_section:
            # Check if this is a bold group heading, e.g.
            first_char = stripped[0]
            if first_char in line_marks and "**" in stripped:
                # Group heading – check if it should be skipped
                group_name = stripped.split("**")[1]
                skipping_group = any(group.lower() == group_name.lower() for group in ignore_groups)
                continue

            if skipping_group and any(line.startswith(f"  {ch} ") for ch in line_marks):
                continue

            if first_char in line_marks and any(line.startswith(f"  {ch} ") for ch in line_marks):
                release_notes_lines.append(line.rstrip())
            else:
                break

    return "\n".join(release_notes_lines) + ("\n" if release_notes_lines else "")


def format_row_with_suppression(template: str, values: dict[str, Any]) -> str:
    """
    Format a row template while suppressing fragments for empty values.

    Parameters:
        template: The format string with placeholders like "{type}: {number} _{title}_".
        values: Mapping of placeholder keys to values (may be empty strings).

    Returns:
        The formatted string.
    """

    def is_empty(key: str) -> bool:
        return not str(values.get(key, "")).strip()

    def placeholder(key: str) -> str:
        return r"\{" + re.escape(key) + r"\}"

    result = template

    if is_empty("developers") and is_empty("pull-requests"):
        result = re.sub(
            rf"developed\s+by\s+{placeholder('developers')}\s+in\s+{placeholder('pull-requests')}",
            "",
            result,
            flags=re.IGNORECASE,
        )
    elif is_empty("pull-requests"):
        result = re.sub(
            rf"\s+in\s+{placeholder('pull-requests')}",
            "",
            result,
            flags=re.IGNORECASE,
        )

    if is_empty("assignees"):
        result = re.sub(
            rf"assigned\s+to\s+{placeholder('assignees')}",
            "",
            result,
            flags=re.IGNORECASE,
        )

    if is_empty("type"):
        result = re.sub(
            rf"^\s*{placeholder('type')}:?\s*",
            "",
            result,
            flags=re.IGNORECASE,
        )

    for key, value in values.items():
        result = re.sub(placeholder(key), str(value), result, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", result).strip()
