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
from copy import deepcopy
from types import SimpleNamespace

import pytest
from datetime import datetime
from typing import Optional

from github import Github
from github import GithubException
from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.data.miner import DataMiner
from release_notes_generator.data.utils.bulk_sub_issue_collector import BulkSubIssueCollector
from release_notes_generator.model.mined_data import MinedData
from tests.unit.conftest import FakeRepo


class ChildBulkSubIssueCollector(BulkSubIssueCollector):
    """
    Inherit from the real class so isinstance checks still pass.
    We AVOID calling super().__init__ to skip any network work.
    """

    def __init__(self, patch_parent_sub_issues: Optional[dict[str, list[str]]] = None):
        super().__init__("FAKE")
        self.patch_parent_sub_issues: Optional[dict[str, list[str]]] = patch_parent_sub_issues

    def scan_sub_issues_for_parents(self, parent_ids: list[str]) -> list[str]:
        if self.patch_parent_sub_issues is None:
            for parent_id in parent_ids:
                self.parents_sub_issues.setdefault(parent_id, [])
        else:
            self.parents_sub_issues = self.patch_parent_sub_issues

        return []


def _identity(fn):
    return fn


def fake_fetch_repository(full_name: str):
    # you can branch based on input
    if full_name == "org_1/another_repo":
        return FakeRepo("org_1/another_repo")
    elif full_name == "org_2/another_repo":
        return FakeRepo("org_2/another_repo")
    elif full_name == "org_3/another_repo":
        return FakeRepo("org_3/another_repo")
    else:
        return None  # simulate “not found”


def decorator_mock(func):
    """
    Mock for the decorator to return the function itself.
    """
    return func


class MinedDataMock(MinedData):
    """
    Mock class for MinedData to simulate the behavior of the real MinedData class.
    """

    def __init__(self, mocker, rls_mock: Optional[GitRelease], mock_repo: Repository):
        super().__init__(mock_repo)
        self.release = rls_mock if rls_mock is not None else mocker.Mock(spec=GitRelease)
        self.issues = {
            mocker.Mock(spec=Issue, title="Mock Issue 1", number=1): mock_repo,
            mocker.Mock(spec=Issue, title="Mock Issue 2", number=2): mock_repo,
        }
        self.pull_requests = {
            mocker.Mock(spec=PullRequest, title="Mock PR 1", number=1): mock_repo,
            mocker.Mock(spec=PullRequest, title="Mock PR 2", number=2): mock_repo,
        }
        self.commits = {
            mocker.Mock(spec=Commit, sha="abc123", commit={"message": "Mock Commit 1"}): mock_repo,
            mocker.Mock(spec=Commit, sha="def456", commit={"message": "Mock Commit 2"}): mock_repo,
        }
        self.since = datetime.now()


def test_get_latest_release_from_tag_name_not_defined_2_releases_type_error(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.data.miner.logger.info")
    mock_log_error = mocker.patch("release_notes_generator.data.miner.logger.error")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases
    data = MinedDataMock(mocker, mock_git_releases, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock
    mocker.patch("semver.Version.parse", side_effect=TypeError)

    latest_release = release_notes_miner.get_latest_release(data.home_repository)

    assert latest_release is None
    assert (
        "Getting latest release by semantic ordering (could not be the last one by time).",
    ) == mock_log_info.call_args_list[0][0]
    assert ("Latest release not found for %s. 1st release for repository!", "org/repo") == mock_log_info.call_args_list[
        1
    ][0]
    assert ("Skipping invalid type of version tag: %s | Error: %s", "v1.0.0", "") == mock_log_error.call_args_list[0][0]
    assert ("Skipping invalid type of version tag: %s | Error: %s", "v2.0.0", "") == mock_log_error.call_args_list[2][0]


def test_get_latest_release_from_tag_name_not_defined_2_releases_value_error(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.data.miner.logger.info")
    mock_log_error = mocker.patch("release_notes_generator.data.miner.logger.error")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases
    data = MinedDataMock(mocker, mock_git_releases, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock
    mocker.patch("semver.Version.parse", side_effect=ValueError)

    data.home_repository.get_releases = mocker.MagicMock(return_value=mock_git_releases)

    latest_release = release_notes_miner.get_latest_release(data.home_repository)

    assert latest_release is None
    assert (
        "Getting latest release by semantic ordering (could not be the last one by time).",
    ) == mock_log_info.call_args_list[0][0]
    assert ("Latest release not found for %s. 1st release for repository!", "org/repo") == mock_log_info.call_args_list[
        1
    ][0]
    assert ("Skipping invalid value of version tag: %s", "v1.0.0") == mock_log_error.call_args_list[0][0]
    assert ("Skipping invalid value of version tag: %s", "v2.0.0") == mock_log_error.call_args_list[1][0]


def test_get_latest_release_from_tag_name_not_defined_2_releases(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.data.miner.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases
    data = MinedDataMock(mocker, mock_git_releases, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock

    latest_release = release_notes_miner.get_latest_release(data.home_repository)

    assert latest_release is not None
    assert (
        "Getting latest release by semantic ordering (could not be the last one by time).",
    ) == mock_log_info.call_args_list[0][0]


def test_get_latest_release_from_tag_name_not_defined_no_release(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.data.miner.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = []
    data = MinedDataMock(mocker, None, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock

    latest_release = release_notes_miner.get_latest_release(data.home_repository)

    assert latest_release is None
    assert 2 == len(mock_log_info.call_args_list)
    assert (
        "Getting latest release by semantic ordering (could not be the last one by time).",
    ) == mock_log_info.call_args_list[0][0]
    assert ("Latest release not found for %s. 1st release for repository!", "org/repo") == mock_log_info.call_args_list[
        1
    ][0]


def test_get_latest_release_from_tag_name_defined_release_exists(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_info = mocker.patch("release_notes_generator.data.miner.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    rls_mock = mocker.Mock(spec=GitRelease)
    mock_repo.get_release.return_value = rls_mock
    data = MinedDataMock(mocker, None, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock

    latest_release = release_notes_miner.get_latest_release(data.home_repository)

    assert rls_mock == latest_release
    mock_exit.assert_not_called()
    assert 1 == len(mock_log_info.call_args_list)
    assert ("Getting latest release by from-tag name %s", "") == mock_log_info.call_args_list[0][0]


# get_latest_release tests
def test_get_latest_release_from_tag_name_defined_no_release(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_error = mocker.patch("release_notes_generator.data.miner.logger.error")
    mock_log_info = mocker.patch("release_notes_generator.data.miner.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_release.return_value = None
    data = MinedDataMock(mocker, None, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock

    latest_release = release_notes_miner.get_latest_release(data.home_repository)

    assert latest_release is None
    mock_exit.assert_called_once_with(1)
    assert 1 == len(mock_log_info.call_args_list)
    assert 1 == len(mock_log_error.call_args_list)
    assert ("Getting latest release by from-tag name %s", "") == mock_log_info.call_args_list[0][0]
    assert ("Latest release not found for received from-tag %s. Ending!", "") == mock_log_error.call_args_list[0][0]


def test_mine_data_repo_none_raises(mocker):
    github_mock = mocker.Mock(spec=Github)
    # Ensure github.get_repo returns None -> DataMiner.get_repository returns None
    github_mock.get_repo.return_value = None

    rate_limiter_mock = mocker.Mock()
    miner = DataMiner(github_mock, rate_limiter_mock)
    # Bypass safe_call wrapper so the raw ValueError surfaces
    miner._safe_call = _identity

    # ActionInputs.get_github_repository is consulted inside mine_data
    mocker.patch("release_notes_generator.data.miner.ActionInputs.get_github_repository", return_value="owner/repo")

    with pytest.raises(ValueError, match="Repository not found"):
        miner.mine_data()


def test_mine_data_commits_without_since(mocker, mock_repo):
    # GitHub instance mock
    gh = mocker.Mock()
    gh.get_repo.return_value = mock_repo
    mock_repo.get_issues.return_value = []
    mock_repo.get_pulls.return_value = []
    mock_repo.get_commits.return_value = []

    # Miner instance
    miner = DataMiner(gh, mocker.Mock())

    # Bypass safe_call wrapper
    miner._safe_call = lambda f: f

    # Inputs / release behavior
    mocker.patch(
        "release_notes_generator.action_inputs.ActionInputs.get_github_repository",
        return_value="owner/repo",
    )
    mocker.patch.object(miner, "get_latest_release", return_value=None)

    # Execute
    data = miner.mine_data()

    # Assert commits retrieved without since arg
    mock_repo.get_commits.assert_called_once()
    assert mock_repo.get_commits.call_args.kwargs == {}
    assert data.since is None


# mine_missing_sub_issues


def test_scan_sub_issues_for_parents(mocker, mock_repo, mined_data_simple):
    gh = mocker.Mock()
    gh.get_repo.return_value = mock_repo

    # miner setup
    miner = DataMiner(gh, mocker.Mock())
    miner._safe_call = lambda f: f
    mocker.patch.object(miner, "_make_bulk_sub_issue_collector", return_value=ChildBulkSubIssueCollector())

    mocker.patch.object(miner, "_fetch_all_repositories_in_cache", return_value=None)
    mocker.patch.object(miner, "_fetch_missing_issues", return_value={})
    mocker.patch.object(miner, "_fetch_prs_for_fetched_cross_issues", return_value={})

    fetched_issues, prs_of_fetched_cross_repo_issues = miner.mine_missing_sub_issues(mined_data_simple)

    assert 1 == len(mined_data_simple.parents_sub_issues.keys())
    assert mined_data_simple.parents_sub_issues["org/repo#121"] == []

    # No additional calls to get_issues
    assert {} == fetched_issues
    assert {} == prs_of_fetched_cross_repo_issues


def test_fetch_all_repositories_in_cache(mocker, mock_repo, mined_data_simple):
    gh = mocker.Mock()
    gh.get_repo.return_value = mock_repo

    # miner setup
    miner = DataMiner(gh, mocker.Mock())
    miner._safe_call = lambda f: f

    patch_parents_sub_issues: dict[str, list[str]] = {}
    patch_parents_sub_issues["org_1/another_repo#122"] = ["org_2/another_repo#122", "org_3/another_repo#122", "o/r#1"]

    mocker.patch.object(
        miner, "_make_bulk_sub_issue_collector", return_value=ChildBulkSubIssueCollector(patch_parents_sub_issues)
    )
    mocker.patch.object(miner, "_fetch_missing_issues", return_value={})
    mocker.patch.object(miner, "_fetch_prs_for_fetched_cross_issues", return_value={})

    mocker.patch.object(miner, "_fetch_repository", side_effect=fake_fetch_repository)

    fetched_issues, prs_of_fetched_cross_repo_issues = miner.mine_missing_sub_issues(mined_data_simple)

    assert 4 == len(mined_data_simple._repositories.keys())
    assert "org/repo" in mined_data_simple._repositories
    assert "org_1/another_repo" in mined_data_simple._repositories
    assert "org_2/another_repo" in mined_data_simple._repositories
    assert "org_3/another_repo" in mined_data_simple._repositories

    # No additional calls to get_issues
    assert {} == fetched_issues
    assert {} == prs_of_fetched_cross_repo_issues


def test_fetch_missing_issues(mocker, mock_repo, mined_data_simple, mock_issue_closed_i1_bug):
    def fake_get_issue(num):
        if num == 1:
            return mock_issue_closed_i1_bug
        if num == 2:
            i = deepcopy(mock_issue_closed_i1_bug)
            i.closed_at = None
            return i
        if num == 3:
            i = deepcopy(mock_issue_closed_i1_bug)
            i.closed_at = datetime(2019, 12, 31)
            return i
        if num == 7:
            raise RuntimeError("Issue 7 not found")
        else:
            return None

    gh = mocker.Mock()
    gh.get_repo.return_value = mock_repo
    mock_repo.get_issue.side_effect = fake_get_issue

    # miner setup
    miner = DataMiner(gh, mocker.Mock())
    miner._safe_call = lambda f: f

    patch_parents_sub_issues: dict[str, list[str]] = {}
    patch_parents_sub_issues["org/repo#1"] = [
        "org/repo#2",
        "org/repo#3",
        "org*repo#4",
        "org/repoX#5",
        "org/repo#6",
        "org/repo#7",
        "org/repo#8",
        "org/repo#9",
    ]
    for i in range(2, 10):
        if i == 4:
            patch_parents_sub_issues[f"org*repo#{i}"] = []
        if i == 5:
            patch_parents_sub_issues[f"org/repoX#{i}"] = []
        else:
            patch_parents_sub_issues[f"org/repo#{i}"] = []

    mocker.patch.object(
        miner, "_make_bulk_sub_issue_collector", return_value=ChildBulkSubIssueCollector(patch_parents_sub_issues)
    )
    mocker.patch.object(miner, "_fetch_all_repositories_in_cache", return_value={})
    mocker.patch.object(miner, "_fetch_prs_for_fetched_cross_issues", return_value={})

    mined_data_simple.since = datetime(2020, 1, 1)

    fetched_issues, prs_of_fetched_cross_repo_issues = miner.mine_missing_sub_issues(mined_data_simple)

    assert 1 == len(mined_data_simple.parents_sub_issues.keys())
    assert [] == mined_data_simple.parents_sub_issues["org/repo#1"]

    # No additional calls to get_issues
    assert 1 == len(fetched_issues.keys())
    assert mock_issue_closed_i1_bug == next(iter(fetched_issues.keys()))
    assert {} == prs_of_fetched_cross_repo_issues


def test_fetch_missing_issues_no_fetch(mocker, mock_repo, mined_data_simple, mock_issue_closed_i1_bug):
    def fake_get_issue(num):
        return None

    gh = mocker.Mock()
    gh.get_repo.return_value = mock_repo
    mock_repo.get_issue.side_effect = fake_get_issue

    # miner setup
    miner = DataMiner(gh, mocker.Mock())
    miner._safe_call = lambda f: f

    patch_parents_sub_issues: dict[str, list[str]] = {}

    mocker.patch.object(
        miner, "_make_bulk_sub_issue_collector", return_value=ChildBulkSubIssueCollector(patch_parents_sub_issues)
    )
    mocker.patch.object(miner, "_fetch_all_repositories_in_cache", return_value={})
    mocker.patch.object(miner, "_fetch_prs_for_fetched_cross_issues", return_value={})

    mined_data_simple.since = datetime(2020, 1, 1)

    fetched_issues, prs_of_fetched_cross_repo_issues = miner.mine_missing_sub_issues(mined_data_simple)

    assert 0 == len(mined_data_simple.parents_sub_issues.keys())
    assert 0 == len(fetched_issues.keys())
    assert {} == prs_of_fetched_cross_repo_issues


def test_fetch_prs_for_fetched_cross_issues(mocker, mock_repo):
    # Miner with safe_call bypassed
    gh = mocker.Mock()
    miner = DataMiner(gh, mocker.Mock())
    miner._safe_call = lambda f: f  # no decorator wrapping

    # PR object returned by as_pull_request()
    pr_obj = mocker.Mock(spec=PullRequest)

    # Event that should add PR
    src_issue_with_pr = mocker.Mock()
    src_issue_with_pr.pull_request = object()
    src_issue_with_pr.as_pull_request.return_value = pr_obj
    ev_add = SimpleNamespace(event="cross-referenced", source=SimpleNamespace(issue=src_issue_with_pr))

    # Event with cross-reference but no pull_request attribute (skip)
    src_issue_plain = mocker.Mock()
    if hasattr(src_issue_plain, "pull_request"):
        delattr(src_issue_plain, "pull_request")
    ev_skip = SimpleNamespace(event="cross-referenced", source=SimpleNamespace(issue=src_issue_plain))

    # Irrelevant event (skip)
    ev_other = SimpleNamespace(event="assigned", source=None)

    # Issue 1: normal timeline
    issue_ok = mocker.Mock(spec=Issue)
    issue_ok.number = 10
    issue_ok.get_timeline.return_value = [ev_add, ev_skip, ev_other]

    # Issue 2: raises on timeline
    issue_err = mocker.Mock(spec=Issue)
    issue_err.number = 11
    issue_err.get_timeline.side_effect = RuntimeError("boom")

    # Logger warning spy
    warn_mock = mocker.patch("release_notes_generator.data.miner.logger.warning")

    issues_map = {issue_ok: mock_repo, issue_err: mock_repo}

    result = miner._fetch_prs_for_fetched_cross_issues(issues_map)

    key_ok = f"{mock_repo.full_name}#{issue_ok.number}"
    key_err = f"{mock_repo.full_name}#{issue_err.number}"

    assert key_ok in result and result[key_ok] == [pr_obj]
    assert key_err in result and result[key_err] == []
    warn_mock.assert_called_once()


# --- _extract_pr_numbers_from_commits ---


def test_extract_pr_numbers_squash_format(mocker):
    commit = mocker.Mock()
    commit.commit.message = "Fix service access role (#1363)"
    assert DataMiner._extract_pr_numbers_from_commits([commit]) == {1363}


def test_extract_pr_numbers_merge_format(mocker):
    commit = mocker.Mock()
    commit.commit.message = "Merge pull request #1358 from org/branch"
    assert DataMiner._extract_pr_numbers_from_commits([commit]) == {1358}


def test_extract_pr_numbers_multiple_commits(mocker):
    c1, c2, c3 = mocker.Mock(), mocker.Mock(), mocker.Mock()
    c1.commit.message = "Feature A (#10)"
    c2.commit.message = "Merge pull request #20 from org/feat-b"
    c3.commit.message = "Hotfix C (#30)"
    assert DataMiner._extract_pr_numbers_from_commits([c1, c2, c3]) == {10, 20, 30}


def test_extract_pr_numbers_deduplicates(mocker):
    c1, c2 = mocker.Mock(), mocker.Mock()
    c1.commit.message = "Fix A (#42)"
    c2.commit.message = "Follow-up for #42 (#42)"
    assert DataMiner._extract_pr_numbers_from_commits([c1, c2]) == {42}


def test_extract_pr_numbers_no_references(mocker):
    c1, c2 = mocker.Mock(), mocker.Mock()
    c1.commit.message = "Initial commit"
    c2.commit.message = "Fix typo in README"
    assert DataMiner._extract_pr_numbers_from_commits([c1, c2]) == set()


def test_extract_pr_numbers_empty_input():
    assert DataMiner._extract_pr_numbers_from_commits([]) == set()


def test_extract_pr_numbers_multiline_message(mocker):
    commit = mocker.Mock()
    commit.commit.message = "Subject line\n\nFixes behaviour (#77)"
    assert DataMiner._extract_pr_numbers_from_commits([commit]) == set()


# --- mine_data compare mode ---


def _make_compare_miner(mocker, mock_repo, *, from_tag="v2.6.3", to_tag="v2.6.4",
                        created_at=datetime(2026, 5, 7), published_at=None, prefer_published=False,
                        compare_commits=None, get_pull_side_effect=None, total_commits=None):
    """Wire a DataMiner for compare-mode mine_data calls."""
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_from_tag_name", return_value=from_tag)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_tag_name", return_value=to_tag)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_github_repository", return_value="org/repo")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_published_at", return_value=prefer_published)

    release_mock = mocker.Mock(spec=GitRelease)
    release_mock.created_at = created_at
    release_mock.published_at = published_at
    release_mock.tag_name = from_tag
    mock_repo.get_release.return_value = release_mock
    mock_repo.get_issues.return_value = []

    comparison_mock = mocker.Mock()
    comparison_mock.commits = compare_commits if compare_commits is not None else []
    if total_commits is not None:
        comparison_mock.total_commits = total_commits
    mock_repo.compare.return_value = comparison_mock

    if get_pull_side_effect is not None:
        mock_repo.get_pull.side_effect = get_pull_side_effect
    else:
        mock_repo.get_pull.return_value = mocker.Mock(spec=PullRequest)

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    miner = DataMiner(github_mock, mocker.Mock())
    miner._safe_call = decorator_mock
    return miner


def test_mine_data_compare_mode_uses_compare_api(mocker, mock_repo):
    commit_mock = mocker.Mock()
    commit_mock.sha = "abc123"
    commit_mock.commit.message = "Fix service access role (#1363)"

    miner = _make_compare_miner(mocker, mock_repo, compare_commits=[commit_mock])
    data = miner.mine_data()

    mock_repo.compare.assert_called_once_with("v2.6.3", "v2.6.4")
    mock_repo.get_commits.assert_not_called()
    assert data.compare_commit_shas == {"abc123"}


def test_mine_data_compare_mode_fetches_prs_by_number(mocker, mock_repo):
    commit_mock = mocker.Mock()
    commit_mock.sha = "abc123"
    commit_mock.commit.message = "Fix service access role (#42)"
    pr_mock = mocker.Mock(spec=PullRequest)
    pr_mock.number = 42

    miner = _make_compare_miner(mocker, mock_repo, compare_commits=[commit_mock],
                                get_pull_side_effect=lambda n: pr_mock if n == 42 else None)
    data = miner.mine_data()

    mock_repo.get_pull.assert_called_once_with(42)
    assert pr_mock in data.pull_requests
    assert data.pull_requests[pr_mock] == mock_repo


def test_mine_data_compare_mode_multiple_prs(mocker, mock_repo):
    c1, c2 = mocker.Mock(), mocker.Mock()
    c1.sha, c2.sha = "sha1", "sha2"
    c1.commit.message = "Feature A (#10)"
    c2.commit.message = "Fix B (#20)"
    pr10 = mocker.Mock(spec=PullRequest)
    pr10.number = 10
    pr20 = mocker.Mock(spec=PullRequest)
    pr20.number = 20

    miner = _make_compare_miner(mocker, mock_repo, compare_commits=[c1, c2],
                                get_pull_side_effect=lambda n: pr10 if n == 10 else pr20)
    data = miner.mine_data()

    assert len(data.pull_requests) == 2


def test_mine_data_compare_mode_leaves_issues_empty(mocker, mock_repo):
    miner = _make_compare_miner(mocker, mock_repo, compare_commits=[])
    data = miner.mine_data()
    assert data.issues == {}


def test_mine_data_compare_mode_sets_data_since(mocker, mock_repo):
    miner = _make_compare_miner(mocker, mock_repo, created_at=datetime(2026, 5, 7), prefer_published=False)
    data = miner.mine_data()
    assert data.since == datetime(2026, 5, 7)


def test_mine_data_compare_mode_sets_data_since_published_at(mocker, mock_repo):
    miner = _make_compare_miner(mocker, mock_repo,
                                created_at=datetime(2026, 5, 7),
                                published_at=datetime(2026, 5, 8),
                                prefer_published=True)
    data = miner.mine_data()
    assert data.since == datetime(2026, 5, 8)


def test_mine_data_compare_mode_skips_none_prs(mocker, mock_repo):
    commit_mock = mocker.Mock()
    commit_mock.sha = "dead99"
    commit_mock.commit.message = "Fix something (#99)"

    miner = _make_compare_miner(mocker, mock_repo, compare_commits=[commit_mock],
                                get_pull_side_effect=lambda _: None)
    data = miner.mine_data()

    assert data.pull_requests == {}


def test_mine_data_compare_mode_no_pr_numbers_in_message(mocker, mock_repo):
    commit_mock = mocker.Mock()
    commit_mock.sha = "bumpsha"
    commit_mock.commit.message = "Bump version to 2.6.4"

    miner = _make_compare_miner(mocker, mock_repo, compare_commits=[commit_mock])
    data = miner.mine_data()

    assert data.pull_requests == {}
    assert "bumpsha" in data.compare_commit_shas


def test_mine_data_compare_mode_warns_on_total_commits_overflow(mocker, mock_repo):
    """Test that a warning is logged when the compare API returns more commits than it can retrieve (over 10,000)."""
    commit_mock = mocker.Mock()
    commit_mock.sha = "abc123"
    commit_mock.commit.message = "Fix service access role (#1363)"
    warning_mock = mocker.patch("release_notes_generator.data.miner.logger.warning")

    miner = _make_compare_miner(
        mocker,
        mock_repo,
        compare_commits=[commit_mock],
        total_commits=10_001,
    )
    miner.mine_data()

    warning_mock.assert_called_once_with(
        "Compare mode: retrieved %d commit(s) but comparison reports %d total; results may be truncated.",
        1,
        10_001,
    )


def test_mine_data_compare_mode_warns_on_retrieval_cap_without_total(mocker, mock_repo):
    """Test that a warning is logged when the compare API reaches the retrieval cap without a total commit count."""
    commits = []
    for i in range(10_000):
        commit_mock = mocker.Mock()
        commit_mock.sha = f"sha{i}"
        commit_mock.commit.message = "Commit without PR ref"
        commits.append(commit_mock)

    warning_mock = mocker.patch("release_notes_generator.data.miner.logger.warning")

    miner = _make_compare_miner(
        mocker,
        mock_repo,
        compare_commits=commits,
    )
    miner.mine_data()

    warning_mock.assert_called_once_with(
        "Compare mode: retrieved %d commit(s); comparison ranges over %d commits may be truncated.",
        10_000,
        10_000,
    )


def test_mine_data_compare_mode_fallback_to_target_sha_on_404(mocker, mock_repo):
    """Test that when compare API raises 404, fallback to target tag's latest commit SHA."""
    target_commit = mocker.Mock()
    target_commit.sha = "targetsha123"
    target_commit.commit.message = "Latest commit on target tag (no PR ref)"

    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_from_tag_name", return_value="v2.6.3")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_tag_name", return_value="v2.6.4")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_github_repository", return_value="org/repo")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_published_at", return_value=False)

    release_mock = mocker.Mock(spec=GitRelease)
    release_mock.created_at = datetime(2026, 5, 7)
    release_mock.published_at = None
    release_mock.tag_name = "v2.6.3"
    mock_repo.get_release.return_value = release_mock

    # Compare API raises 404 exception
    mock_repo.compare.side_effect = GithubException(404, {"message": "Comparison failed"})
    # Fall back to fetching the target commit
    mock_repo.get_commit.return_value = target_commit
    mock_repo.get_issues.return_value = []

    warning_mock = mocker.patch("release_notes_generator.data.miner.logger.warning")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    decorator_mock = lambda f: f
    miner = DataMiner(github_mock, mocker.Mock())
    miner._safe_call = decorator_mock
    data = miner.mine_data()

    # Verify warning was logged with expected message
    warning_mock.assert_called_once()
    call_args = warning_mock.call_args[0]
    assert "Compare API returned 404" in call_args[0]
    assert "Attempting to resolve target ref" in call_args[0]

    # Verify the fallback actually queried the target ref via get_commit()
    mock_repo.get_commit.assert_called_once_with("v2.6.4")

    # Verify the fallback commit was used
    assert "targetsha123" in data.compare_commit_shas, "Target commit SHA must be in compare_commit_shas"
    # Commit is included since message has no PR reference, so no filtering
    assert len(data.commits) == 1, "Fallback commit should be included in data.commits"


def test_mine_data_compare_mode_exits_when_fallback_fails(mocker, mock_repo):
    """Test that action exits when both compare API and fallback commit fetch fail."""
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_from_tag_name", return_value="v2.6.3")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_tag_name", return_value="v2.6.4")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_github_repository", return_value="org/repo")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_published_at", return_value=False)

    release_mock = mocker.Mock(spec=GitRelease)
    release_mock.created_at = datetime(2026, 5, 7)
    release_mock.published_at = None
    release_mock.tag_name = "v2.6.3"
    mock_repo.get_release.return_value = release_mock

    # Both compare and get_commit fail
    mock_repo.compare.side_effect = GithubException(404, {"message": "Not Found"})
    mock_repo.get_commit.return_value = None
    mock_repo.get_issues.return_value = []

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    decorator_mock = lambda f: f
    miner = DataMiner(github_mock, mocker.Mock())
    miner._safe_call = decorator_mock

    with pytest.raises(SystemExit):
        miner.mine_data()


def test_mine_data_compare_mode_exits_on_non_404_github_exception(mocker, mock_repo):
    """Non-404 GithubException from compare API must exit immediately without falling back."""
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_from_tag_name", return_value="v2.6.3")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_tag_name", return_value="v2.6.4")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_github_repository", return_value="org/repo")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_published_at", return_value=False)

    release_mock = mocker.Mock(spec=GitRelease)
    release_mock.created_at = datetime(2026, 5, 7)
    release_mock.published_at = None
    release_mock.tag_name = "v2.6.3"
    mock_repo.get_release.return_value = release_mock

    mock_repo.compare.side_effect = GithubException(500, {"message": "Internal Server Error"})
    mock_repo.get_issues.return_value = []

    error_mock = mocker.patch("release_notes_generator.data.miner.logger.error")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    miner = DataMiner(github_mock, mocker.Mock())
    miner._safe_call = lambda f: f

    with pytest.raises(SystemExit):
        miner.mine_data()

    # Fallback (get_commit) must NOT have been attempted
    mock_repo.get_commit.assert_not_called()
    # Error must have been logged with the non-404 status
    assert any("500" in str(call) for call in error_mock.call_args_list)


# --- mine_data timestamp mode (regression) ---


def test_mine_data_timestamp_mode_uses_get_commits(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_github_repository", return_value="org/repo")
    mock_repo.get_issues.return_value = []
    mock_repo.get_pulls.return_value = []
    mock_repo.get_commits.return_value = []

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    miner = DataMiner(github_mock, mocker.Mock())
    miner._safe_call = decorator_mock
    mocker.patch.object(miner, "get_latest_release", return_value=None)

    miner.mine_data()

    mock_repo.get_commits.assert_called_once()
    mock_repo.compare.assert_not_called()


def test_mine_data_timestamp_mode_compare_shas_empty(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_github_repository", return_value="org/repo")
    mock_repo.get_issues.return_value = []
    mock_repo.get_pulls.return_value = []
    mock_repo.get_commits.return_value = []

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    miner = DataMiner(github_mock, mocker.Mock())
    miner._safe_call = decorator_mock
    mocker.patch.object(miner, "get_latest_release", return_value=None)

    data = miner.mine_data()

    assert data.compare_commit_shas == set()
