from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import requests

from release_notes_generator.utils.record_utils import parse_issue_id, format_issue_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectorConfig:
    """
    Configuration options for BulkSubIssueCollector.
    Override defaults when instantiating if you need custom behavior.
    """

    api_url: str = "https://api.github.com/graphql"
    timeout: float = 12.0
    verify_tls: bool = True

    # Retry/backoff
    max_retries: int = 3
    base_backoff: float = 1.0

    # Pagination and batching
    per_page: int = 100              # Max allowed by GitHub for subIssues
    max_parents_per_repo: int = 100   # Max issue aliases per repository(...) block
    max_repos_per_request: int = 1   # Max repository blocks per query

    # Pacing
    gentle_pacing_seconds: float = 0.05


class BulkSubIssueCollector:
    """
    Collect sub-issues for received parent issues in bulk via GitHub GraphQL API.
    Prepare list of new parents build from found sub-issues.
    """

    def __init__(
            self,
            token: str,
            cfg: Optional[CollectorConfig] = None,
            session: Optional[requests.Session] = None,
    ):
        self._cfg = cfg or CollectorConfig()
        self._session = session or requests.Session()
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Parent -> list of its direct sub-issues ("org/repo#n")
        self.parents_sub_issues: dict[str, list[str]] = {}

    def scan_sub_issues_for_parents(self, parents_to_check: list[str]) -> list[str]:
        """
        Input:  ["org/repo#123", "org2/repo2#77", ...]
        Output: list of *new parent* IDs in the same format (unique, sorted).
        Side-effect: self.parents_sub_issues[parent_id] = [child_ids...]
        """
        if not parents_to_check:
            return []

        new_parents_to_check: Set[str] = set()
        self.parents_sub_issues = {}

        by_repo: dict[tuple[str, str], list[int]] = {}
        originals: set[str] = set()

        for raw in parents_to_check:
            org, repo, num = parse_issue_id(raw)
            by_repo.setdefault((org, repo), []).append(num)
            originals.add(raw)

        # Outer chunk by repositories to keep queries within safe length.
        repo_items = list(by_repo.items())
        for i in range(0, len(repo_items), self._cfg.max_repos_per_request):
            repo_chunk = repo_items[i : i + self._cfg.max_repos_per_request]

            # Maintain cursors per (org, repo, issue).
            cursors: Dict[Tuple[str, str, int], Optional[str]] = {}
            remaining_by_repo: Dict[Tuple[str, str], Set[int]] = {
                k: set(v) for k, v in repo_chunk
            }
            for (org, repo), nums in remaining_by_repo.items():
                for n in nums:
                    cursors[(org, repo, n)] = None

            # Continue until all parents in this chunk are fully paginated.
            while any(remaining_by_repo.values()):
                # Build one GraphQL query with up to max_repos_per_request repos,
                # each with up to max_parents_per_repo parent issues that still have pages.
                repo_blocks: List[str] = []
                alias_maps: Dict[str, Tuple[str, str, int]] = {}  # alias -> (org, repo, parent_num)

                for r_idx, ((org, repo), parents_rem) in enumerate(remaining_by_repo.items()):
                    if not parents_rem:
                        continue
                    current_parents = list(parents_rem)[: self._cfg.max_parents_per_repo]
                    issue_blocks: List[str] = []
                    for p_idx, parent_num in enumerate(current_parents):
                        alias = f"i{r_idx}_{p_idx}"
                        alias_maps[alias] = (org, repo, parent_num)
                        after = cursors[(org, repo, parent_num)]
                        after_part = f', after: "{after}"' if after else ""
                        issue_blocks.append(
                            f"""{alias}: issue(number: {parent_num}) {{
                                  number
                                  subIssues(first: {self._cfg.per_page}{after_part}) {{
                                    nodes {{
                                      number
                                      repository {{ owner {{ login }} name }}
                                      # only count to decide if child is also a parent
                                      subIssues(first: 0) {{ totalCount }}
                                    }}
                                    pageInfo {{ hasNextPage endCursor }}
                                  }}
                                }}"""
                        )
                    if issue_blocks:
                        repo_alias = f"r{r_idx}"
                        repo_blocks.append(
                            f"""{repo_alias}: repository(owner: "{org}", name: "{repo}") {{
                                   {' '.join(issue_blocks)}
                                 }}"""
                        )

                if not repo_blocks:
                    break

                query = f"query Bulk {{ {' '.join(repo_blocks)} }}"
                data = self._post_graphql({"query": query})

                # Parse results: top-level 'data' contains our repo aliases
                d_repo = data.get("data", {})

                for alias, (org, repo, parent_num) in alias_maps.items():
                    issue_node = self._find_alias_node(d_repo, alias)
                    parent_id = format_issue_id(org, repo, parent_num)

                    if issue_node is None:
                        # Parent not found / no access — mark as complete
                        remaining_by_repo[(org, repo)].discard(parent_num)
                        # Ensure map key exists (empty list)
                        self.parents_sub_issues.setdefault(parent_id, [])
                        logger.info("No sub-issues found for parent %s.", parent_id)
                        continue

                    conn = issue_node["subIssues"]
                    child_ids: list[str] = self.parents_sub_issues.setdefault(parent_id, [])

                    for child in conn.get("nodes", []):
                        child_num = child["number"]
                        child_org = child["repository"]["owner"]["login"]
                        child_repo = child["repository"]["name"]
                        child_id = format_issue_id(child_org, child_repo, child_num)
                        # Save every direct child in the mapping (no duplicates)
                        if child_id not in child_ids:
                            child_ids.append(child_id)

                        # If the child has children, it's a "new parent"
                        if child_id not in originals:
                            if child["subIssues"]["totalCount"] > 0:
                                new_parents_to_check.add(child_id)
                            else:
                                # save no sub-issues for non-parents
                                self.parents_sub_issues.setdefault(child_id, [])

                    logger.debug("Sub-issues found for parent %s: %s", parent_id, child_ids)

                    page = conn["pageInfo"]
                    if page["hasNextPage"]:
                        cursors[(org, repo, parent_num)] = page["endCursor"]
                    else:
                        remaining_by_repo[(org, repo)].discard(parent_num)

                # Gentle pacing to avoid secondary limits
                time.sleep(0.05)

        # Deterministic order
        return sorted(new_parents_to_check, key=lambda s: (lambda o, r, n: (o, r, n))(*parse_issue_id(s)))

    # ---------- internals ----------

    def _post_graphql(self, payload: dict) -> dict:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self._cfg.max_retries + 1):
            try:
                logger.debug("Posting graphql query")
                resp = self._session.post(
                    self._cfg.api_url,
                    headers=self._headers,
                    data=json.dumps(payload),
                    verify=self._cfg.verify_tls,
                    timeout=self._cfg.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                if "errors" in data and data["errors"]:
                    logger.error("GraphQL errors: %s", data["errors"])
                    raise RuntimeError(f"GitHub GraphQL errors: {data['errors']}")
                logger.debug("Posted graphql query")
                return data
            except Exception as e:
                logger.exception("GraphQL query failed")
                last_exc = e
                if attempt == self._cfg.max_retries:
                    raise
                time.sleep(self._cfg.base_backoff * attempt)
        if last_exc:
            raise last_exc
        raise RuntimeError("GraphQL POST failed without exception.")

    def _find_alias_node(self, repo_block: dict, alias: str) -> Optional[dict]:
        """
        Given top-level 'data' (mapping of repo aliases -> repo object),
        return the 'issue' object under whichever repo alias contains our issue alias.
        """
        for _, repo_obj in repo_block.items():
            if isinstance(repo_obj, dict) and alias in repo_obj:
                return repo_obj[alias]
        return None
