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
DefaultRecordFactory builds both flat and hierarchical issue records (Epics/Features/Tasks) and associates PRs/commits.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import cast, Optional

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.model.record import Record
from release_notes_generator.model.sub_issue_record import SubIssueRecord
from release_notes_generator.record.factory.record_factory import RecordFactory
from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter

from release_notes_generator.utils.pull_request_utils import get_issues_for_pr, extract_issue_numbers_from_body
from release_notes_generator.utils.record_utils import get_id, parse_issue_id

logger = logging.getLogger(__name__)


class DefaultRecordFactory(RecordFactory):
    """
    A class used to generate records for release notes.
    """

    def __init__(self, github: Github, home_repository: Repository) -> None:
        self._github = github
        rate_limiter = GithubRateLimiter(github)
        self._safe_call = safe_call_decorator(rate_limiter)
        self._home_repository = home_repository

        self._records: dict[str, Record] = {}

        self.__registered_issues: set[str] = set()
        self.__registered_commits: set[str] = set()

    def generate(self, data: MinedData) -> dict[str, Record]:
        """
        Generate records for release notes.

        Parameters:
            data (MinedData): The MinedData instance containing repository, issues, pull requests, and commits.

        Returns:
            dict[str, Record]: A dictionary of records indexed by their IDs.
        """
        logger.info("Creation of records started...")

        built = build_issue_records_parallel(self, data, max_workers=8)
        self._records.update(built)
        self.__registered_issues.update(built.keys())

        # dev note: Each issue is now in records dict by its issue number - all on same level - no hierarchy
        #   --> This is useful for population by PRs and commits

        logger.info("Registering Commits to Pull Requests and Pull Requests to Issues...")
        for pull, repo in data.pull_requests.items():
            self._register_pull_and_its_commits_to_issue(pull, get_id(pull, repo), data, target_repository=repo)

        if data.pull_requests_of_fetched_cross_issues:
            logger.info("Register cross-repo Pull Requests to its issues")
            for iid, prs in data.pull_requests_of_fetched_cross_issues.items():
                self._register_cross_repo_prs_to_issue(iid, prs)

        logger.info("Registering direct commits to records...")
        for commit, repo in data.commits.items():
            if commit.sha not in self.__registered_commits:
                self._records[get_id(commit, repo)] = CommitRecord(commit)

        # dev note: now we have all PRs and commits registered to issues or as stand-alone records
        logger.info("Building issues hierarchy...")

        sub_i_ids = list({iid for sublist in data.parents_sub_issues.values() for iid in sublist})
        sub_i_prts = {sub_issue: parent for parent, sublist in data.parents_sub_issues.items() for sub_issue in sublist}
        self._re_register_hierarchy_issues(sub_issues_ids=sub_i_ids, sub_issue_parents=sub_i_prts)
        self.order_hierarchy_levels()

        logger.info(
            "Generated %d records from %d issues and %d PRs, with %d commits detected.",
            len(self._records),
            len(data.issues),
            len(data.pull_requests),
            len(data.commits),
        )
        return self._records

    def _create_record_for_issue(self, issue: Issue, iid: str, issue_labels: Optional[list[str]] = None) -> None:
        if issue_labels is None:
            issue_labels = self._get_issue_labels_mix_with_type(issue)

        # super()._create_record_for_issue(issue, iid, issue_labels)
        skip_record = any(item in issue_labels for item in ActionInputs.get_skip_release_notes_labels())
        self._records[iid] = IssueRecord(issue=issue, skip=skip_record, issue_labels=issue_labels)
        self.__registered_issues.add(iid)

    # pylint: disable=too-many-statements
    def _register_pull_and_its_commits_to_issue(
        self, pull: PullRequest, pid: str, data: MinedData, target_repository: Optional[Repository] = None
    ) -> None:
        pull_labels = [label.name for label in pull.get_labels()]
        skip_record: bool = any(item in pull_labels for item in ActionInputs.get_skip_release_notes_labels())
        related_commits = [c for c in data.commits if c.sha == pull.merge_commit_sha]
        self.__registered_commits.update(c.sha for c in related_commits)

        pr_repo = target_repository if target_repository is not None else data.home_repository

        linked_from_api: set[str] = self._safe_call(get_issues_for_pr)(pull_number=pull.number) or set()
        linked_from_body: set[str] = extract_issue_numbers_from_body(pull, pr_repo)
        merged_linked_issues: set[str] = linked_from_api.union(linked_from_body)
        pull_issues: list[str] = list(merged_linked_issues)
        attached_any = False
        if len(pull_issues) > 0:
            for issue_id in pull_issues:
                if issue_id not in self._records:
                    logger.warning(
                        "Detected PR %d linked to issue %s which is not in the list of received issues. "
                        "Fetching ...",
                        pull.number,
                        issue_id,
                    )
                    # dev note: here we expect that PR links to an issue in the same repository !!!
                    org, repo, num = parse_issue_id(issue_id)
                    r = data.get_repository(f"{org}/{repo}")
                    parent_issue = self._safe_call(r.get_issue)(num) if r is not None else None
                    if parent_issue is not None:
                        self._create_record_for_issue(parent_issue, get_id(parent_issue, r))  # type: ignore[arg-type]

                if issue_id in self._records and isinstance(
                    self._records[issue_id], (SubIssueRecord, HierarchyIssueRecord, IssueRecord)
                ):
                    rec = cast(IssueRecord, self._records[issue_id])
                    rec.register_pull_request(pull)
                    logger.debug("Registering pull number: %s, title : %s", pull.number, pull.title)

                    for c in related_commits:  # register commits to the PR record
                        rec.register_commit(pull, c)
                        logger.debug("Registering commit %s to PR %d", c.sha, pull.number)

                    attached_any = True

        if not attached_any:
            pr_rec = PullRequestRecord(pull, pull_labels, skip_record)
            for c in related_commits:  # register commits to the PR record
                pr_rec.register_commit(c)
            self._records[pid] = pr_rec
            logger.debug("Created record for PR %s: %s", pid, pull.title)

    def _register_cross_repo_prs_to_issue(self, iid: str, prs: list[PullRequest]) -> None:
        if iid not in self.__registered_issues:
            logger.error("Issue '%s' not found among collected records.", iid)
            return

        for pr in prs:
            cast(IssueRecord, self._records[iid]).register_pull_request(pr)

    def _get_issue_labels_mix_with_type(self, issue: Issue) -> list[str]:
        labels: list[str] = [label.name for label in issue.get_labels()]

        if issue.type is not None:
            issue_type = issue.type.name.lower()
            if issue_type not in labels:
                labels.append(issue_type)

        return labels

    def _re_register_hierarchy_issues(self, sub_issues_ids: list[str], sub_issue_parents: dict[str, str]):
        logger.debug("Re-registering hierarchy issues ...")
        reduced_sub_issue_ids: list[str] = sub_issues_ids[:]

        made_progress = False
        for sub_issue_id in sub_issues_ids:
            # remove issue(sub_issue_id) from current records and add it to parent
            #   as sub-issue or sub-hierarchy-issue
            # but do it only for issue where parent issue number is not in _sub_issue_parents keys
            #   Why? We building hierarchy from bottom. Access in records is very easy.
            if sub_issue_id in sub_issue_parents.values():
                continue

            parent_issue_id: str = sub_issue_parents[sub_issue_id]
            parent_rec = cast(HierarchyIssueRecord, self._records[parent_issue_id])
            sub_rec = self._records[sub_issue_id]

            if isinstance(sub_rec, SubIssueRecord):
                parent_rec.sub_issues[sub_issue_id] = sub_rec  # add to parent as SubIssueRecord
                self._records.pop(sub_issue_id)  # remove from main records as it is sub-one
                reduced_sub_issue_ids.remove(sub_issue_id)  # remove from sub-parents as it is now sub-one
                sub_issue_parents.pop(sub_issue_id)
                made_progress = True
                logger.debug("Added sub-issue %s to parent %s", sub_issue_id, parent_issue_id)
            elif isinstance(sub_rec, HierarchyIssueRecord):
                parent_rec.sub_hierarchy_issues[sub_issue_id] = sub_rec  # add to parent as 'Sub' HierarchyIssueRecord
                self._records.pop(sub_issue_id)  # remove from main records as it is sub-one
                reduced_sub_issue_ids.remove(sub_issue_id)  # remove from sub-parents as it is now sub-one
                sub_issue_parents.pop(sub_issue_id)
                made_progress = True
                logger.debug("Added sub-hierarchy-issue %s to parent %s", sub_issue_id, parent_issue_id)
            else:
                logger.error(
                    "Detected IssueRecord in position of SubIssueRecord - leaving as standalone and dropping mapping"
                )
                # Avoid infinite recursion by removing the unresolved mapping
                reduced_sub_issue_ids.remove(sub_issue_id)
                sub_issue_parents.pop(sub_issue_id)

        if reduced_sub_issue_ids and made_progress:
            self._re_register_hierarchy_issues(reduced_sub_issue_ids, sub_issue_parents)

    def order_hierarchy_levels(self, level: int = 0) -> None:
        """
        Order hierarchy levels for proper rendering.

        Parameters:
            level (int): The current level in the hierarchy. Default is 0.
        """
        # we have now all hierarchy issues in records - but levels are not set
        #   we need to set levels for proper rendering
        #   This have to be done from up to down
        top_hierarchy_records = [rec for rec in self._records.values() if isinstance(rec, HierarchyIssueRecord)]
        for rec in top_hierarchy_records:
            rec.order_hierarchy_levels(level=level)

    def build_record_for_hierarchy_issue(self, issue: Issue, issue_labels: Optional[list[str]] = None) -> Record:
        """
        Build a hierarchy issue record.

        Parameters:
            issue (Issue): The issue to build.
            issue_labels (list[str]): The labels to use for this issue.
        Returns:
            Record: The built record.
        """
        if issue_labels is None:
            issue_labels = self._get_issue_labels_mix_with_type(issue)
        skip_record = any(lbl in ActionInputs.get_skip_release_notes_labels() for lbl in issue_labels)
        return HierarchyIssueRecord(issue=issue, skip=skip_record, issue_labels=issue_labels)

    def build_record_for_sub_issue(self, issue: Issue, iid: str, issue_labels: Optional[list[str]] = None) -> Record:
        """
        Build a sub issue record.

        Parameters:
            issue (Issue): The issue to build.
            iid (str): The id to use for this issue.
            issue_labels (list[str]): The labels to use for this issue.
        Returns:
            Record: The built record.
        """
        if issue_labels is None:
            issue_labels = self._get_issue_labels_mix_with_type(issue)
        skip_record = any(lbl in ActionInputs.get_skip_release_notes_labels() for lbl in issue_labels)
        rec = SubIssueRecord(issue, issue_labels, skip_record)
        # preserve cross-repo flag behavior
        if iid.split("#")[0] != self._home_repository.full_name:
            rec.is_cross_repo = True
        return rec

    def build_record_for_issue(self, issue: Issue, issue_labels: Optional[list[str]] = None) -> Record:
        """
        Build an issue record.

        Parameters:
            issue (Issue): The issue to build.
            issue_labels (list[str]): The labels to use for this issue.
        Returns:
            Record: The built record.
        """
        if issue_labels is None:
            issue_labels = self._get_issue_labels_mix_with_type(issue)
        skip_record = any(lbl in ActionInputs.get_skip_release_notes_labels() for lbl in issue_labels)
        return IssueRecord(issue=issue, skip=skip_record, issue_labels=issue_labels)


def build_issue_records_parallel(gen, data, max_workers: int = 8) -> dict[str, "Record"]:
    """
    Build issue records in parallel with no side effects on `gen`.
    Returns: {iid: Record}
    """
    parents_sub_issues = data.parents_sub_issues  # read-only snapshot for this phase
    all_sub_issue_ids = {iid for subs in parents_sub_issues.values() for iid in subs}
    issues_items = list(data.issues.items())  # snapshot

    def _classify_and_build(issue, repo) -> tuple[str, "Record"]:
        iid = get_id(issue, repo)

        # classification
        if len(parents_sub_issues.get(iid, [])) > 0:
            # hierarchy node (has sub-issues)
            rec = gen.build_record_for_hierarchy_issue(issue)
        elif iid in all_sub_issue_ids:
            # leaf sub-issue
            rec = gen.build_record_for_sub_issue(issue, iid)
        else:
            # plain issue
            rec = gen.build_record_for_issue(issue)
        return iid, rec

    results: dict[str, "Record"] = {}
    if not issues_items:
        return results

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="build-issue-rec") as ex:
        for iid, rec in ex.map(lambda ir: _classify_and_build(*ir), issues_items):
            results[iid] = rec

    return results
