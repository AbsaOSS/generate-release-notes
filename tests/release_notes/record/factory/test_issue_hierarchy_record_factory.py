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
from typing import cast

from github import Github

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.record.factory.issue_hierarchy_record_factory import IssueHierarchyRecordFactory
from tests.conftest import mock_safe_call_decorator


# generate

def test_generate_no_input_data(mocker, mock_repo):
    mock_github_client = mocker.Mock(spec=Github)
    factory = IssueHierarchyRecordFactory(github=mock_github_client)
    data = MinedData(mock_repo)

    result = factory.generate(data)

    assert 0 == len(result.values())

#   - single issue record (closed)
#   - single hierarchy issue record - two sub-issues without PRs
#   - single hierarchy issue record - two sub-issues with PRs - no commits
#   - single hierarchy issue record - two sub-issues with PRs - with commits
#   - single hierarchy issue record - one sub hierarchy issues - two sub-issues with PRs - with commits
#   - single pull request record (closed, merged)
#   - single direct commit record
def test_generate_isolated_record_types_no_labels_no_type_defined(mocker, mined_data_isolated_record_types_no_labels_no_type_defined):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator)
    mock_github_client = mocker.Mock(spec=Github)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit

    factory = IssueHierarchyRecordFactory(github=mock_github_client)

    result = factory.generate(mined_data_isolated_record_types_no_labels_no_type_defined)

    assert 8 == len(result)
    assert {'org/repo#121', 'org/repo#301', 'org/repo#302', 'org/repo#303', 'org/repo#304', '123', '124', "merge_commit_sha_direct"}.issubset(result.keys())

    assert isinstance(result['org/repo#121'], IssueRecord)
    assert isinstance(result['org/repo#301'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#302'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#303'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#304'], HierarchyIssueRecord)
    assert isinstance(result['123'], PullRequestRecord)
    assert isinstance(result['124'], PullRequestRecord)
    assert isinstance(result["merge_commit_sha_direct"], CommitRecord)

    rec_i = cast(IssueRecord, result['org/repo#121'])
    assert 0 == rec_i.pull_requests_count()

    rec_hi_1 = cast(HierarchyIssueRecord, result['org/repo#301'])
    assert 0 == rec_hi_1.pull_requests_count()
    assert 0 == len(rec_hi_1.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_1.sub_issues.values())
    assert 0 == rec_hi_1.sub_issues['org/repo#450'].pull_requests_count()
    assert 0 == rec_hi_1.level

    rec_hi_2 = cast(HierarchyIssueRecord, result['org/repo#302'])
    assert 1 == rec_hi_2.pull_requests_count()
    assert 0 == len(rec_hi_2.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_2.sub_issues.values())
    assert 1 == rec_hi_2.sub_issues['org/repo#451'].pull_requests_count()
    assert 0 == rec_hi_2.level

    rec_hi_3 = cast(HierarchyIssueRecord, result['org/repo#303'])
    assert 1 == rec_hi_3.pull_requests_count()
    assert 0 == len(rec_hi_3.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_3.sub_issues.values())
    assert 1 == rec_hi_3.sub_issues['org/repo#452'].pull_requests_count()
    assert "Fixed bug in PR 151" == rec_hi_3.sub_issues['org/repo#452'].get_commit(151, "merge_commit_sha_151").commit.message
    assert 0 == rec_hi_3.level

    rec_hi_4 = cast(HierarchyIssueRecord, result['org/repo#304'])
    assert 1 == rec_hi_4.pull_requests_count()
    assert 1 == len(rec_hi_4.sub_hierarchy_issues.values())
    assert 0 == len(rec_hi_4.sub_issues.values())
    assert 1 == rec_hi_4.pull_requests_count()
    assert "Fixed bug in PR 152" == rec_hi_4.sub_hierarchy_issues['org/repo#350'].sub_issues['org/repo#453'].get_commit(152, "merge_commit_sha_152").commit.message
    assert 0 == rec_hi_4.level

    rec_hi_5 = cast(HierarchyIssueRecord, result['org/repo#304'])
    assert 1 == rec_hi_5.sub_hierarchy_issues['org/repo#350'].level


#   - single issue record (closed)
#   - single hierarchy issue record - two sub-issues without PRs
#   - single hierarchy issue record - two sub-issues with PRs - no commits
#   - single hierarchy issue record - two sub-issues with PRs - with commits
#   - single hierarchy issue record - one sub hierarchy issues - two sub-issues with PRs - with commits
#   - single pull request record (closed, merged)
#   - single direct commit record
def test_generate_isolated_record_types_with_labels_no_type_defined(mocker, mined_data_isolated_record_types_with_labels_no_type_defined):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator)
    mock_github_client = mocker.Mock(spec=Github)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit

    factory = IssueHierarchyRecordFactory(github=mock_github_client)

    result = factory.generate(mined_data_isolated_record_types_with_labels_no_type_defined)

    assert 8 == len(result)
    assert {'org/repo#121', 'org/repo#301', 'org/repo#302', 'org/repo#303', 'org/repo#304', '123', '124', "merge_commit_sha_direct"}.issubset(result.keys())

    assert isinstance(result['org/repo#121'], IssueRecord)
    assert isinstance(result['org/repo#301'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#302'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#303'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#304'], HierarchyIssueRecord)
    assert isinstance(result['123'], PullRequestRecord)
    assert isinstance(result['124'], PullRequestRecord)
    assert isinstance(result["merge_commit_sha_direct"], CommitRecord)

    rec_i = cast(IssueRecord, result['org/repo#121'])
    assert 0 == rec_i.pull_requests_count()

    rec_hi_1 = cast(HierarchyIssueRecord, result['org/repo#301'])
    assert 0 == rec_hi_1.pull_requests_count()
    assert 0 == len(rec_hi_1.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_1.sub_issues.values())
    assert 0 == rec_hi_1.sub_issues['org/repo#450'].pull_requests_count()

    rec_hi_2 = cast(HierarchyIssueRecord, result['org/repo#302'])
    assert 1 == rec_hi_2.pull_requests_count()
    assert 0 == len(rec_hi_2.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_2.sub_issues.values())
    assert 1 == rec_hi_2.sub_issues['org/repo#451'].pull_requests_count()

    rec_hi_3 = cast(HierarchyIssueRecord, result['org/repo#303'])
    assert 1 == rec_hi_3.pull_requests_count()
    assert 0 == len(rec_hi_3.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_3.sub_issues.values())
    assert 1 == rec_hi_3.sub_issues['org/repo#452'].pull_requests_count()
    assert "Fixed bug in PR 151" == rec_hi_3.sub_issues['org/repo#452'].get_commit(151, "merge_commit_sha_151").commit.message

    rec_hi_4 = cast(HierarchyIssueRecord, result['org/repo#304'])
    assert 1 == rec_hi_4.pull_requests_count()
    assert 1 == len(rec_hi_4.sub_hierarchy_issues.values())
    assert 0 == len(rec_hi_4.sub_issues.values())
    assert 1 == rec_hi_4.pull_requests_count()
    assert "Fixed bug in PR 152" == rec_hi_4.sub_hierarchy_issues['org/repo#350'].sub_issues['org/repo#453'].get_commit(152, "merge_commit_sha_152").commit.message


#   - single issue record (closed)
#   - single hierarchy issue record - two sub-issues without PRs
#   - single hierarchy issue record - two sub-issues with PRs - no commits
#   - single hierarchy issue record - two sub-issues with PRs - with commits
#   - single hierarchy issue record - one sub hierarchy issues - two sub-issues with PRs - with commits
#   - single pull request record (closed, merged)
#   - single direct commit record
def test_generate_isolated_record_types_no_labels_with_type_defined(mocker, mined_data_isolated_record_types_no_labels_with_type_defined):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator)
    mock_github_client = mocker.Mock(spec=Github)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit

    factory = IssueHierarchyRecordFactory(github=mock_github_client)

    result = factory.generate(mined_data_isolated_record_types_no_labels_with_type_defined)

    assert 8 == len(result)
    assert {'org/repo#121', 'org/repo#301', 'org/repo#302', 'org/repo#303', 'org/repo#304', '123', '124', "merge_commit_sha_direct"}.issubset(result.keys())

    assert isinstance(result['org/repo#121'], IssueRecord)
    assert isinstance(result['org/repo#301'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#302'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#303'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#304'], HierarchyIssueRecord)
    assert isinstance(result['123'], PullRequestRecord)
    assert isinstance(result['124'], PullRequestRecord)
    assert isinstance(result["merge_commit_sha_direct"], CommitRecord)

    rec_i = cast(IssueRecord, result['org/repo#121'])
    assert 0 == rec_i.pull_requests_count()

    rec_hi_1 = cast(HierarchyIssueRecord, result['org/repo#301'])
    assert 0 == rec_hi_1.pull_requests_count()
    assert 0 == len(rec_hi_1.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_1.sub_issues.values())
    assert 0 == rec_hi_1.sub_issues['org/repo#450'].pull_requests_count()

    rec_hi_2 = cast(HierarchyIssueRecord, result['org/repo#302'])
    assert 1 == rec_hi_2.pull_requests_count()
    assert 0 == len(rec_hi_2.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_2.sub_issues.values())
    assert 1 == rec_hi_2.sub_issues['org/repo#451'].pull_requests_count()

    rec_hi_3 = cast(HierarchyIssueRecord, result['org/repo#303'])
    assert 1 == rec_hi_3.pull_requests_count()
    assert 0 == len(rec_hi_3.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_3.sub_issues.values())
    assert 1 == rec_hi_3.sub_issues['org/repo#452'].pull_requests_count()
    assert "Fixed bug in PR 151" == rec_hi_3.sub_issues['org/repo#452'].get_commit(151, "merge_commit_sha_151").commit.message

    rec_hi_4 = cast(HierarchyIssueRecord, result['org/repo#304'])
    assert 1 == rec_hi_4.pull_requests_count()
    assert 1 == len(rec_hi_4.sub_hierarchy_issues.values())
    assert 0 == len(rec_hi_4.sub_issues.values())
    assert 1 == rec_hi_4.pull_requests_count()
    assert "Fixed bug in PR 152" == rec_hi_4.sub_hierarchy_issues['org/repo#350'].sub_issues['org/repo#453'].get_commit(152, "merge_commit_sha_152").commit.message


#   - single issue record (closed)
#   - single hierarchy issue record - two sub-issues without PRs
#   - single hierarchy issue record - two sub-issues with PRs - no commits
#   - single hierarchy issue record - two sub-issues with PRs - with commits
#   - single hierarchy issue record - one sub hierarchy issues - two sub-issues with PRs - with commits
#   - single pull request record (closed, merged)
#   - single direct commit record
def test_generate_isolated_record_types_with_labels_with_type_defined(mocker, mined_data_isolated_record_types_with_labels_with_type_defined):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator)
    mock_github_client = mocker.Mock(spec=Github)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit

    factory = IssueHierarchyRecordFactory(github=mock_github_client)

    result = factory.generate(mined_data_isolated_record_types_with_labels_with_type_defined)

    assert 8 == len(result)
    assert {'org/repo#121', 'org/repo#301', 'org/repo#302', 'org/repo#303', 'org/repo#304', '123', '124', "merge_commit_sha_direct"}.issubset(result.keys())

    assert isinstance(result['org/repo#121'], IssueRecord)
    assert isinstance(result['org/repo#301'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#302'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#303'], HierarchyIssueRecord)
    assert isinstance(result['org/repo#304'], HierarchyIssueRecord)
    assert isinstance(result['123'], PullRequestRecord)
    assert isinstance(result['124'], PullRequestRecord)
    assert isinstance(result["merge_commit_sha_direct"], CommitRecord)

    rec_i = cast(IssueRecord, result['org/repo#121'])
    assert 0 == rec_i.pull_requests_count()

    rec_hi_1 = cast(HierarchyIssueRecord, result['org/repo#301'])
    assert 0 == rec_hi_1.pull_requests_count()
    assert 0 == len(rec_hi_1.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_1.sub_issues.values())
    assert 0 == rec_hi_1.sub_issues['org/repo#450'].pull_requests_count()

    rec_hi_2 = cast(HierarchyIssueRecord, result['org/repo#302'])
    assert 1 == rec_hi_2.pull_requests_count()
    assert 0 == len(rec_hi_2.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_2.sub_issues.values())
    assert 1 == rec_hi_2.sub_issues['org/repo#451'].pull_requests_count()

    rec_hi_3 = cast(HierarchyIssueRecord, result['org/repo#303'])
    assert 1 == rec_hi_3.pull_requests_count()
    assert 0 == len(rec_hi_3.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_3.sub_issues.values())
    assert 1 == rec_hi_3.sub_issues['org/repo#452'].pull_requests_count()
    assert "Fixed bug in PR 151" == rec_hi_3.sub_issues['org/repo#452'].get_commit(151, "merge_commit_sha_151").commit.message

    rec_hi_4 = cast(HierarchyIssueRecord, result['org/repo#304'])
    assert 1 == rec_hi_4.pull_requests_count()
    assert 1 == len(rec_hi_4.sub_hierarchy_issues.values())
    assert 0 == len(rec_hi_4.sub_issues.values())
    assert 1 == rec_hi_4.pull_requests_count()
    assert "Fixed bug in PR 152" == rec_hi_4.sub_hierarchy_issues['org/repo#350'].sub_issues['org/repo#453'].get_commit(152, "merge_commit_sha_152").commit.message
