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


from unittest.mock import MagicMock
from datetime import datetime, timedelta

from github.Repository import Repository

from release_notes_generator.data.filter import FilterByRelease
from release_notes_generator.model.mined_data import MinedData


def test_filter_no_release(mocker):
    mock_log_info = mocker.patch("release_notes_generator.data.filter.logger.info")
    mock_log_debug = mocker.patch("release_notes_generator.data.filter.logger.debug")

    # Mock MinedData
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.since = datetime(2023, 1, 1)
    data.release = None
    data.compare_commit_shas = set()
    data.issues = [MagicMock(closed_at=None), MagicMock(closed_at=None)]
    data.pull_requests = [MagicMock(merged_at=None), MagicMock(merged_at=None)]
    data.commits = [MagicMock(commit=MagicMock(author=MagicMock(date=None)))]

    # Apply filter
    filter_instance = FilterByRelease()
    filter_instance.filter(data)

    # Assert no filtering occurred
    assert len(data.issues) == 2
    assert len(data.pull_requests) == 2
    assert len(data.commits) == 1
    assert 0 == len(mock_log_info.call_args_list)
    assert 0 == len(mock_log_debug.call_args_list)


def test_filter_with_release(mocker):
    mock_log_info = mocker.patch("release_notes_generator.data.filter.logger.info")
    mock_log_debug = mocker.patch("release_notes_generator.data.filter.logger.debug")

    # Mock MinedData
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.release = MagicMock()
    data.since = datetime(2023, 1, 1)
    data.compare_commit_shas = set()

    # Mock issues, pull requests, and commits
    data.issues = {
        MagicMock(closed_at=datetime(2023, 1, 2)): data.home_repository,
        MagicMock(closed_at=datetime(2022, 12, 31)): data.home_repository,
    }
    data.pull_requests = {
        MagicMock(merged_at=datetime(2023, 2, 3), closed_at=datetime(2022, 12, 31)): data.home_repository,
        MagicMock(merged_at=datetime(2022, 12, 30), closed_at=datetime(2022, 12, 31)): data.home_repository,
    }
    data.commits = {
        MagicMock(commit=MagicMock(author=MagicMock(date=datetime(2024, 1, 4)))): data.home_repository,
        MagicMock(commit=MagicMock(author=MagicMock(date=datetime(2022, 12, 29)))): data.home_repository,
    }

    # Apply filter
    filter_instance = FilterByRelease()
    filtered_data = filter_instance.filter(data)

    # Assert filtering occurred
    assert len(filtered_data.issues) == 1
    assert len(filtered_data.pull_requests) == 1
    assert len(filtered_data.commits) == 1
    assert next(iter(filtered_data.issues.keys())).closed_at == datetime(2023, 1, 2)
    assert next(iter(filtered_data.pull_requests.keys())).merged_at == datetime(2023, 2, 3)
    assert next(iter(filtered_data.commits.keys())).commit.author.date == datetime(2024, 1, 4)
    assert (
        "Starting issue, prs and commit reduction by the latest release since time.",
    ) == mock_log_info.call_args_list[0][0]
    assert ("Count of issues reduced from %d to %d", 2, 1) == mock_log_debug.call_args_list[1][0]
    assert ("Count of pulls reduced from %d to %d", 2, 1) == mock_log_debug.call_args_list[2][0]
    assert ("Count of commits reduced from %d to %d", 2, 1) == mock_log_debug.call_args_list[3][0]


# --- FilterByRelease compare mode guard ---


def test_filter_compare_mode_passes_prs_through():
    """PRs retained regardless of merged_at when compare_commit_shas is non-empty."""
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.release = MagicMock()
    data.since = datetime(2026, 5, 14)
    data.compare_commit_shas = {"sha_abc"}
    data.issues = {}
    data.commits = {}
    old_pr = MagicMock()
    old_pr.number = 1
    old_pr.merged_at = datetime(2026, 5, 14) - timedelta(days=30)
    old_pr.closed_at = old_pr.merged_at
    data.pull_requests = {old_pr: data.home_repository}

    filtered = FilterByRelease().filter(data)

    assert old_pr in filtered.pull_requests


def test_filter_compare_mode_passes_commits_through():
    """Commits retained regardless of author date when compare_commit_shas is non-empty."""
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.release = MagicMock()
    data.since = datetime(2026, 5, 14)
    data.compare_commit_shas = {"sha_abc"}
    data.issues = {}
    data.pull_requests = {}
    old_commit = MagicMock()
    old_commit.commit.author.date = datetime(2026, 5, 14) - timedelta(days=30)
    data.commits = {old_commit: data.home_repository}

    filtered = FilterByRelease().filter(data)

    assert old_commit in filtered.commits


def test_filter_compare_mode_passes_multiple_prs_and_commits():
    """All PRs and commits pass through unfiltered in compare mode."""
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.release = MagicMock()
    data.since = datetime(2026, 5, 14)
    data.compare_commit_shas = {"sha1", "sha2"}
    data.issues = {}
    old_date = datetime(2026, 5, 14) - timedelta(days=30)
    data.pull_requests = {
        MagicMock(number=i, merged_at=old_date, closed_at=old_date): data.home_repository
        for i in range(3)
    }
    data.commits = {
        MagicMock(commit=MagicMock(author=MagicMock(date=old_date))): data.home_repository
        for _ in range(2)
    }

    filtered = FilterByRelease().filter(data)

    assert len(filtered.pull_requests) == 3
    assert len(filtered.commits) == 2


def test_filter_timestamp_mode_filters_old_prs():
    """PR before since excluded in timestamp mode (compare_commit_shas empty)."""
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.release = MagicMock()
    data.since = datetime(2026, 5, 14)
    data.compare_commit_shas = set()
    data.issues = {}
    data.commits = {}
    old_pr = MagicMock()
    old_pr.number = 1
    old_pr.merged_at = datetime(2026, 5, 14) - timedelta(days=30)
    old_pr.closed_at = old_pr.merged_at
    data.pull_requests = {old_pr: data.home_repository}

    filtered = FilterByRelease().filter(data)

    assert old_pr not in filtered.pull_requests


def test_filter_timestamp_mode_keeps_recent_prs():
    """PR after since retained in timestamp mode (regression guard)."""
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.release = MagicMock()
    data.since = datetime(2026, 5, 14)
    data.compare_commit_shas = set()
    data.issues = {}
    data.commits = {}
    new_pr = MagicMock()
    new_pr.number = 2
    new_pr.merged_at = datetime(2026, 5, 15)
    new_pr.closed_at = datetime(2026, 5, 15)
    data.pull_requests = {new_pr: data.home_repository}

    filtered = FilterByRelease().filter(data)

    assert new_pr in filtered.pull_requests
