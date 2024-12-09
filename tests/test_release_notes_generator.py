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

import time
from datetime import datetime, timedelta

from github import Github
from github.GitRelease import GitRelease

from release_notes_generator.generator import ReleaseNotesGenerator
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.utils.constants import ROW_FORMAT_ISSUE


# generate_release_notes tests


def test_generate_release_notes_repository_not_found(mocker):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = None

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 10
    mock_rate_limit.core.reset.timestamp.return_value = time.time() + 3600
    github_mock.get_rate_limit.return_value = mock_rate_limit

    custom_chapters = CustomChapters(print_empty_chapters=True)

    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()

    assert release_notes is None


def test_generate_release_notes_latest_release_not_found(
    mocker,
    mock_repo,
    mock_issue_closed,
    mock_issue_closed_i1_bug,
    mock_pull_closed_with_rls_notes_101,
    mock_pull_closed_with_rls_notes_102,
    mock_commit,
):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo
    mock_repo.created_at = datetime.now() - timedelta(days=10)
    mock_repo.get_issues.return_value = [mock_issue_closed, mock_issue_closed_i1_bug]
    mock_repo.get_pulls.return_value = [mock_pull_closed_with_rls_notes_101, mock_pull_closed_with_rls_notes_102]
    mock_repo.get_commits.return_value = [mock_commit]

    mock_issue_closed.created_at = mock_repo.created_at + timedelta(days=2)
    mock_issue_closed_i1_bug.created_at = mock_repo.created_at + timedelta(days=7)
    mock_issue_closed_i1_bug.closed_at = mock_repo.created_at + timedelta(days=6)
    mock_pull_closed_with_rls_notes_101.merged_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_102.merged_at = mock_repo.created_at + timedelta(days=7)

    mocker.patch("release_notes_generator.generator.ReleaseNotesGenerator.get_latest_release", return_value=None)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    custom_chapters = CustomChapters(print_empty_chapters=True)

    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()

    assert release_notes is not None
    assert "- #121 _Fix the bug_" in release_notes
    assert "- #122 _I1+bug_" in release_notes
    assert "- PR: #101 _Fixed bug_" in release_notes
    assert "- PR: #102 _Fixed bug_" in release_notes


def test_generate_release_notes_latest_release_found_by_created_at(
    mocker,
    mock_repo,
    mock_git_release,
    mock_issue_closed_i1_bug,
    mock_pull_closed_with_rls_notes_101,
    mock_pull_closed_with_rls_notes_102,
    mock_commit,
):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo
    mock_repo.created_at = datetime.now() - timedelta(days=10)
    mock_repo.published_at = datetime.now() - timedelta(days=9)

    mock_repo.get_issues.return_value = [mock_issue_closed_i1_bug]
    mock_repo.get_pulls.return_value = [mock_pull_closed_with_rls_notes_101, mock_pull_closed_with_rls_notes_102]
    mock_repo.get_commits.return_value = [mock_commit]
    mock_commit.commit.author.date = mock_repo.created_at + timedelta(days=1)

    mock_issue_closed_i1_bug.created_at = mock_repo.created_at + timedelta(days=7)
    mock_issue_closed_i1_bug.closed_at = mock_repo.created_at + timedelta(days=6)
    mock_pull_closed_with_rls_notes_101.merged_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_102.merged_at = mock_repo.created_at + timedelta(days=7)

    mock_git_release.created_at = mock_repo.created_at + timedelta(days=5)
    mock_git_release.published_at = mock_repo.created_at + timedelta(days=5)
    mocker.patch("release_notes_generator.generator.ReleaseNotesGenerator.get_latest_release", return_value=mock_git_release)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    mock_get_action_input = mocker.patch("release_notes_generator.utils.gh_action.get_action_input")
    mock_get_action_input.side_effect = lambda first_arg, **kwargs: (
        "{number} _{title}_ in {pull-requests} {unknown} {another-unknown}" if first_arg == ROW_FORMAT_ISSUE else None
    )

    custom_chapters = CustomChapters(print_empty_chapters=True)

    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()

    assert release_notes is not None
    assert "- #122 _I1+bug_" in release_notes
    assert "- PR: #101 _Fixed bug_" not in release_notes
    assert "- PR: #102 _Fixed bug_" in release_notes


def test_generate_release_notes_latest_release_found_by_published_at(
    mocker,
    mock_repo,
    mock_git_release,
    mock_issue_closed_i1_bug,
    mock_pull_closed_with_rls_notes_101,
    mock_pull_closed_with_rls_notes_102,
    mock_commit,
):
    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo
    mock_repo.created_at = datetime.now() - timedelta(days=10)

    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_published_at", return_value="true")

    mock_repo.get_issues.return_value = [mock_issue_closed_i1_bug]
    mock_repo.get_pulls.return_value = [mock_pull_closed_with_rls_notes_101, mock_pull_closed_with_rls_notes_102]
    mock_repo.get_commits.return_value = [mock_commit]
    mock_commit.commit.author.date = mock_repo.created_at + timedelta(days=1)

    mock_issue_closed_i1_bug.created_at = mock_repo.created_at + timedelta(days=7)
    mock_issue_closed_i1_bug.closed_at = mock_repo.created_at + timedelta(days=8)
    mock_pull_closed_with_rls_notes_101.merged_at = mock_repo.created_at + timedelta(days=2)
    mock_pull_closed_with_rls_notes_102.merged_at = mock_repo.created_at + timedelta(days=7)

    github_mock.get_repo().get_latest_release.return_value = mock_git_release
    mock_git_release.created_at = mock_repo.created_at + timedelta(days=5)
    mock_git_release.published_at = mock_repo.created_at + timedelta(days=5)
    mocker.patch("release_notes_generator.generator.ReleaseNotesGenerator.get_latest_release", return_value=mock_git_release)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    custom_chapters = CustomChapters(print_empty_chapters=True)

    release_notes = ReleaseNotesGenerator(github_mock, custom_chapters).generate()

    assert release_notes is not None
    assert "- #122 _I1+bug_" in release_notes
    assert "- PR: #101 _Fixed bug_" not in release_notes
    assert "- PR: #102 _Fixed bug_" in release_notes


# get_latest_release tests

def test_get_latest_release_from_tag_name_defined_no_release(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_release.return_value = None

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert latest_release is None
    mock_exit.assert_called_once_with(1)
    assert mock_log_info.called_with(2)
    assert ('Getting latest release by from-tag name %s', None) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for received tag %s. Ending!', '') == mock_log_info.call_args_list[1][0]


def test_get_latest_release_from_tag_name_defined_release_exists(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    rls_mock = mocker.Mock(spec=GitRelease)
    mock_repo.get_release.return_value = rls_mock

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert rls_mock == latest_release
    mock_exit.assert_not_called()
    assert mock_log_info.called_with(1)
    assert ('Getting latest release by from-tag name %s', None) == mock_log_info.call_args_list[0][0]


# get_latest_release tests

def test_get_latest_release_from_tag_name_defined_no_release(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_release.return_value = None

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert latest_release is None
    mock_exit.assert_called_once_with(1)
    assert mock_log_info.called_with(2)
    assert ('Getting latest release by from-tag name %s', None) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for received tag %s. Ending!', '') == mock_log_info.call_args_list[1][0]


def test_get_latest_release_from_tag_name_not_defined_no_release(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = []

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert latest_release is None
    assert mock_log_info.called_with(2)
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for %s. 1st release for repository!', 'org/repo') == mock_log_info.call_args_list[1][0]


def test_get_latest_release_from_tag_name_not_defined_2_releases(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert latest_release is not None
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]


def test_get_latest_release_from_tag_name_not_defined_2_releases_value_error(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")
    mock_log_debug = mocker.patch("release_notes_generator.generator.logger.debug")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))
    mocker.patch("semver.Version.parse", side_effect=ValueError)

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert latest_release is None
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for %s. 1st release for repository!', 'org/repo') == mock_log_info.call_args_list[1][0]
    assert ('Skipping invalid value of version tag: %s', 'v1.0.0') == mock_log_debug.call_args_list[0][0]
    assert ('Skipping invalid value of version tag: %s', 'v2.0.0') == mock_log_debug.call_args_list[1][0]


def test_get_latest_release_from_tag_name_not_defined_2_releases_type_error(mocker, mock_repo, mock_git_releases):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=False)
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")
    mock_log_debug = mocker.patch("release_notes_generator.generator.logger.debug")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    mock_repo.get_releases.return_value = mock_git_releases

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))
    mocker.patch("semver.Version.parse", side_effect=TypeError)

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert latest_release is None
    assert ('Getting latest release by semantic ordering (could not be the last one by time).',) == mock_log_info.call_args_list[0][0]
    assert ('Latest release not found for %s. 1st release for repository!', 'org/repo') == mock_log_info.call_args_list[1][0]
    assert ('Skipping invalid type of version tag: %s', 'v1.0.0') == mock_log_debug.call_args_list[0][0]
    assert ('Skipping invalid type of version tag: %s', 'v2.0.0') == mock_log_debug.call_args_list[1][0]


def test_get_latest_release_from_tag_name_defined_release_exists(mocker, mock_repo):
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_from_tag_name_defined", return_value=True)
    mock_exit = mocker.patch("sys.exit")
    mock_log_info = mocker.patch("release_notes_generator.generator.logger.info")

    github_mock = mocker.Mock(spec=Github)
    github_mock.get_repo.return_value = mock_repo

    rls_mock = mocker.Mock(spec=GitRelease)
    mock_repo.get_release.return_value = rls_mock

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.core.remaining = 1000
    github_mock.get_rate_limit.return_value = mock_rate_limit

    release_notes_generator = ReleaseNotesGenerator(github_mock, CustomChapters(print_empty_chapters=True))

    latest_release = release_notes_generator.get_latest_release(mock_repo)

    assert rls_mock == latest_release
    mock_exit.assert_not_called()
    assert mock_log_info.called_with(1)
    assert ('Getting latest release by from-tag name %s', None) == mock_log_info.call_args_list[0][0]
