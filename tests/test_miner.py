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

from datetime import datetime
from typing import Optional

from github import Github
from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.miner import DataMiner
from release_notes_generator.model.MinedData import MinedData

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
        super().__init__()
        self.repository = mock_repo
        self.release = rls_mock if rls_mock is not None else mocker.Mock(spec=GitRelease)
        self.issues = [
            mocker.Mock(spec=Issue, title="Mock Issue 1", number=1),
            mocker.Mock(spec=Issue, title="Mock Issue 2", number=2),
        ]
        self.pull_requests = [
            mocker.Mock(spec=PullRequest, title="Mock PR 1", number=1),
            mocker.Mock(spec=PullRequest, title="Mock PR 2", number=2),
        ]
        self.commits = [
            mocker.Mock(spec=Commit, sha="abc123", commit={"message": "Mock Commit 1"}),
            mocker.Mock(spec=Commit, sha="def456", commit={"message": "Mock Commit 2"}),
        ]
        self.since = datetime.now()

def test_get_latest_release_from_tag_name_not_defined_2_releases_type_error(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.miner.logger.info")
    mock_log_error = mocker.patch("release_notes_generator.miner.logger.error")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases
    data = MinedDataMock(mocker, mock_git_releases, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock
    mocker.patch("semver.Version.parse", side_effect=TypeError)

    latest_release = release_notes_miner.get_latest_release(data.repository)

    assert latest_release is None
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for %s. 1st release for repository!', 'org/repo') == mock_log_info.call_args_list[1][0]
    assert ('Skipping invalid type of version tag: %s | Error: %s', 'v1.0.0', '') == mock_log_error.call_args_list[0][0]
    assert ('Skipping invalid type of version tag: %s | Error: %s', 'v2.0.0', '') == mock_log_error.call_args_list[2][0]

def test_get_latest_release_from_tag_name_not_defined_2_releases_value_error(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.miner.logger.info")
    mock_log_error = mocker.patch("release_notes_generator.miner.logger.error")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases
    data = MinedDataMock(mocker, mock_git_releases, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock
    mocker.patch("semver.Version.parse", side_effect=ValueError)

    data.repository.get_releases = mocker.MagicMock(return_value=mock_git_releases)

    latest_release = release_notes_miner.get_latest_release(data.repository)

    assert latest_release is None
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for %s. 1st release for repository!', 'org/repo') == mock_log_info.call_args_list[1][0]
    assert ('Skipping invalid value of version tag: %s', 'v1.0.0') == mock_log_error.call_args_list[0][0]
    assert ('Skipping invalid value of version tag: %s', 'v2.0.0') == mock_log_error.call_args_list[1][0]

def test_get_latest_release_from_tag_name_not_defined_2_releases(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.miner.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases
    data = MinedDataMock(mocker, mock_git_releases, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock

    latest_release = release_notes_miner.get_latest_release(data.repository)

    assert latest_release is not None
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]

def test_get_latest_release_from_tag_name_not_defined_no_release(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.miner.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = []
    data = MinedDataMock(mocker, None, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock

    latest_release = release_notes_miner.get_latest_release(data.repository)

    assert latest_release is None
    assert 2 == len(mock_log_info.call_args_list)
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for %s. 1st release for repository!', 'org/repo') == mock_log_info.call_args_list[1][0]

def test_get_latest_release_from_tag_name_defined_release_exists(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_info = mocker.patch("release_notes_generator.miner.logger.info")

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

    latest_release = release_notes_miner.get_latest_release(data.repository)

    assert rls_mock == latest_release
    mock_exit.assert_not_called()
    assert 1 == len(mock_log_info.call_args_list)
    assert ('Getting latest release by from-tag name %s', "") == mock_log_info.call_args_list[0][0]

# get_latest_release tests
def test_get_latest_release_from_tag_name_defined_no_release(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_info = mocker.patch("release_notes_generator.miner.logger.error")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_release.return_value = None
    data = MinedDataMock(mocker, None, mock_repo)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_miner = DataMiner(github_mock, mock_rate_limit)
    release_notes_miner._safe_call = decorator_mock

    latest_release = release_notes_miner.get_latest_release(data.repository)

    assert latest_release is None
    mock_exit.assert_called_once_with(1)
    assert 2 == len(mock_log_info.call_args_list)
    assert ('Getting latest release by from-tag name %s', "") == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for received from-tag %s. Ending!', '') == mock_log_info.call_args_list[1][0]
