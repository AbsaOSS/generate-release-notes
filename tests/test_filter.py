
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
from datetime import datetime

from github.Repository import Repository

from release_notes_generator.filter import FilterByRelease
from release_notes_generator.model.mined_data import MinedData


def test_filter_no_release(mocker):
    mock_log_info = mocker.patch("release_notes_generator.filter.logger.info")
    mock_log_debug = mocker.patch("release_notes_generator.filter.logger.debug")

    # Mock MinedData
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.since = datetime(2023, 1, 1)
    data.release = None
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
    mock_log_info = mocker.patch("release_notes_generator.filter.logger.info")
    mock_log_debug = mocker.patch("release_notes_generator.filter.logger.debug")

    # Mock MinedData
    data = MagicMock(spec=MinedData)
    data.home_repository = MagicMock(spec=Repository)
    data.release = MagicMock()
    data.since = datetime(2023, 1, 1)

    # Mock issues, pull requests, and commits
    data.issues = [
        MagicMock(closed_at=datetime(2023, 1, 2)),
        MagicMock(closed_at=datetime(2022, 12, 31)),
    ]
    data.pull_requests = [
        MagicMock(merged_at=datetime(2023, 2, 3), closed_at=datetime(2022, 12, 31)),
        MagicMock(merged_at=datetime(2022, 12, 30), closed_at=datetime(2022, 12, 31)),
    ]
    data.commits = [
        MagicMock(commit=MagicMock(author=MagicMock(date=datetime(2024, 1, 4)))),
        MagicMock(commit=MagicMock(author=MagicMock(date=datetime(2022, 12, 29)))),
    ]

    # Apply filter
    filter_instance = FilterByRelease()
    filtered_data = filter_instance.filter(data)

    # Assert filtering occurred
    assert len(filtered_data.issues) == 1
    assert len(filtered_data.pull_requests) == 1
    assert len(filtered_data.commits) == 1
    assert filtered_data.issues[0].closed_at == datetime(2023, 1, 2)
    assert filtered_data.pull_requests[0].merged_at == datetime(2023, 2, 3)
    assert filtered_data.commits[0].commit.author.date == datetime(2024, 1, 4)
    assert ('Starting issue, prs and commit reduction by the latest release since time.',) == mock_log_info.call_args_list[0][0]
    assert ('Count of issues reduced from %d to %d', 2, 1) == mock_log_debug.call_args_list[1][0]
    assert ('Count of pulls reduced from %d to %d', 2, 1) == mock_log_debug.call_args_list[2][0]
    assert ('Count of commits reduced from %d to %d', 2, 1) == mock_log_debug.call_args_list[3][0]
