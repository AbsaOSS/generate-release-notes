import logging
import re
from functools import singledispatchmethod, lru_cache
from typing import cast

from github.Commit import Commit
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

logger = logging.getLogger(__name__)

ISSUE_ID_RE = re.compile(r"^(?P<org>[^/\s]+)/(?P<repo>[^#\s]+)#(?P<num>\d+)$")

class IssueIdParseError(ValueError):
    pass

def get_id(obj, repository: Repository) -> str:
    if isinstance(obj, Issue):
        issue = cast(Issue, obj)
        return _issue_id(repository.full_name, issue.number)
    elif isinstance(obj, PullRequest):
        pr = cast(PullRequest, obj)
        return _pr_id(repository.full_name, pr.number)
    elif isinstance(obj, Commit):
        commit = cast(Commit, obj)
        return f"{commit.sha}"

    return str(obj)

@lru_cache(maxsize=2048)
def _issue_id(repo_full_name: str, number: int) -> str:
    return f"{repo_full_name}#{number}"

@lru_cache(maxsize=2048)
def _pr_id(repo_full_name: str, number: int) -> str:
    return f"{repo_full_name}#{number}"

def parse_issue_id(issue_id: str) -> tuple[str, str, int]:
    """
    Parse 'org/repo#123' -> (org, repo, 123).
    Raises IssueIdParseError on malformed input.
    """
    m = ISSUE_ID_RE.match(issue_id.strip())
    if not m:
        raise IssueIdParseError(
            f"Invalid issue id '{issue_id}', expected 'org/repo#number'"
        )
    return m.group("org"), m.group("repo"), int(m.group("num"))

def format_issue_id(org: str, repo: str, number: int) -> str:
    return f"{org}/{repo}#{number}"
