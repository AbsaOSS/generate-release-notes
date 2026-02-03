"""
Utilities for working with GitHub issue/PR/commit identifiers.
"""

import logging
import re
from functools import lru_cache
from typing import cast, Any

from github.Commit import Commit
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import (
    SUPPORTED_ROW_FORMAT_KEYS_ISSUE,
    SUPPORTED_ROW_FORMAT_KEYS_HIERARCHY_ISSUE,
)

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
    Format a row template with intelligent suppression of empty-field fragments.

    When a placeholder value is empty, this function removes not just the placeholder
    but also the surrounding "fragment" (prefix/label text) to avoid dangling phrases like:
    - "N/A:" when type is missing
    - "assigned to " when assignees is empty
    - "developed by  in " when developers and pull-requests are empty

    NOTE: This function is designed to work with the default row format templates.
    Custom templates using different phrase structures may not benefit from all
    suppression rules. The following patterns are detected and suppressed:
    - "{type}:" or "{type} " prefix
    - "assigned to {assignees}" phrase
    - "developed by {developers} in {pull-requests}" phrase
    - " in {pull-requests}" suffix

    Parameters:
        template: Format string with placeholders like "{type}: {number} _{title}_"
        values: Dict mapping placeholder names to their values (may be empty strings)

    Returns:
        Formatted string with empty-field fragments intelligently suppressed.

    Examples:
        >>> format_row_with_suppression("{type}: {number}", {"type": "Task", "number": "#123"})
        'Task: #123'
        >>> format_row_with_suppression("{type}: {number}", {"type": "", "number": "#123"})
        '#123'
        >>> format_row_with_suppression("assigned to {assignees}", {"assignees": ""})
        ''
        >>> format_row_with_suppression("by {developers} in {pull-requests}", {"developers": "", "pull-requests": ""})
        ''
    """
    # Strategy: Parse the template and conditionally include segments based on placeholder values

    # Field name constants for suppression rules
    # Note: These field names are defined in constants.py as part of SUPPORTED_ROW_FORMAT_KEYS_*
    # They contain only alphanumeric chars and hyphens, which don't require escaping in regex
    # patterns (hyphens are only special inside character classes).
    # The triple-brace syntax {{{var}}} in f-strings produces {{var}} which becomes
    # \{var\} in the final regex pattern, correctly matching literal braces.
    FIELD_TYPE = SUPPORTED_ROW_FORMAT_KEYS_ISSUE[0]  # "type"
    FIELD_ASSIGNEES = SUPPORTED_ROW_FORMAT_KEYS_ISSUE[4]  # "assignees"
    FIELD_DEVELOPERS = SUPPORTED_ROW_FORMAT_KEYS_ISSUE[5]  # "developers"
    FIELD_PULL_REQUESTS = SUPPORTED_ROW_FORMAT_KEYS_ISSUE[6]  # "pull-requests"

    result = template

    # handle compound patterns (both developers and pull-requests)
    if not values.get(FIELD_DEVELOPERS, "").strip() and not values.get(FIELD_PULL_REQUESTS, "").strip():
        # Both are empty, remove the entire "developed by ... in ..." fragment
        result = re.sub(
            rf"developed\s+by\s+\{{{FIELD_DEVELOPERS}\}}\s+in\s+\{{{FIELD_PULL_REQUESTS}\}}",
            "",
            result,
            flags=re.IGNORECASE,
        )
    elif not values.get(FIELD_PULL_REQUESTS, "").strip():
        # pull-requests is empty but developers is not, remove just " in {pull-requests}"
        result = re.sub(rf"\s+in\s+\{{{FIELD_PULL_REQUESTS}\}}", "", result, flags=re.IGNORECASE)

    # handle individual patterns
    # Remove "assigned to {assignees}" when assignees is empty
    if not values.get(FIELD_ASSIGNEES, "").strip():
        result = re.sub(rf"assigned\s+to\s+\{{{FIELD_ASSIGNEES}\}}", "", result, flags=re.IGNORECASE)

    # Remove "{type}:" or "{type} " prefix when type is empty
    if not values.get(FIELD_TYPE, "").strip():
        result = re.sub(rf"\{{{FIELD_TYPE}\}}:?\s*", "", result, flags=re.IGNORECASE)

    # Now format remaining placeholders with their values
    # Use case-insensitive replacement for all placeholders
    for key, value in values.items():
        # Replace both {key} and case variations
        pattern = re.compile(r"\{" + re.escape(key) + r"\}", re.IGNORECASE)
        result = pattern.sub(str(value), result)

    # Clean up extra whitespace
    result = re.sub(r"\s+", " ", result)  # Multiple spaces to single space
    result = result.strip()

    return result
