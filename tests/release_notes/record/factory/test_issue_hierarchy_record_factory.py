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
from mypy.semanal_classprop import calculate_class_abstract_status

from release_notes_generator.model.commit_record import CommitRecord
from release_notes_generator.model.hierarchy_issue_record import HierarchyIssueRecord
from release_notes_generator.model.issue_record import IssueRecord
from release_notes_generator.model.mined_data import MinedData
from release_notes_generator.model.pull_request_record import PullRequestRecord
from release_notes_generator.record.factory.issue_hierarchy_record_factory import IssueHierarchyRecordFactory

def mock_safe_call_decorator(_rate_limiter):
    def wrapper(fn):
        if fn.__name__ == "get_issues_for_pr":
            return mock_get_issues_for_pr
        return fn
    return wrapper

def mock_get_issues_for_pr(pull_number: int) -> set[int]:
    # if pull_number == 150:
    #     return [451]
    return set()


# generate

def test_generate_no_input_data(mocker):
    mock_github_client = mocker.Mock(spec=Github)
    factory = IssueHierarchyRecordFactory(github=mock_github_client)
    data = MinedData()

    result = factory.generate(data)

    assert 0 == len(result.values())


def test_generate_isolated_record_types_no_labels_no_type_defined(mocker, mined_data_isolated_record_types_no_labels_no_type_defined):
    mocker.patch("release_notes_generator.record.factory.default_record_factory.safe_call_decorator", side_effect=mock_safe_call_decorator)
    mock_github_client = mocker.Mock(spec=Github)

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.rate.remaining = 10
    mock_rate_limit.rate.reset.timestamp.return_value = time.time() + 3600
    mock_github_client.get_rate_limit.return_value = mock_rate_limit

    factory = IssueHierarchyRecordFactory(github=mock_github_client)

    result = factory.generate(mined_data_isolated_record_types_no_labels_no_type_defined)

    assert 7 == len(result)
    assert {121, 301, 302, 303, 123, 124, "merge_commit_sha_direct"}.issubset(result.keys())

    assert isinstance(result[121], IssueRecord)
    assert isinstance(result[301], HierarchyIssueRecord)
    assert isinstance(result[302], HierarchyIssueRecord)
    assert isinstance(result[303], HierarchyIssueRecord)
    assert isinstance(result[123], PullRequestRecord)
    assert isinstance(result[124], PullRequestRecord)
    assert isinstance(result["merge_commit_sha_direct"], CommitRecord)

    rec_i = cast(IssueRecord, result[121])
    assert 0 == rec_i.pull_requests_count()

    rec_hi_1 = cast(HierarchyIssueRecord, result[301])
    assert 0 == rec_hi_1.pull_requests_count()
    assert 0 == len(rec_hi_1.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_1.sub_issues.values())
    assert 0 == rec_hi_1.sub_issues[450].pull_requests_count()

    rec_hi_2 = cast(HierarchyIssueRecord, result[302])
    assert 1 == rec_hi_2.pull_requests_count()
    assert 0 == len(rec_hi_2.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_2.sub_issues.values())
    assert 1 == rec_hi_2.sub_issues[451].pull_requests_count()

    rec_hi_3 = cast(HierarchyIssueRecord, result[303])
    assert 1 == rec_hi_3.pull_requests_count()
    assert 0 == len(rec_hi_3.sub_hierarchy_issues.values())
    assert 2 == len(rec_hi_3.sub_issues.values())
    assert 1 == rec_hi_3.sub_issues[452].pull_requests_count()
    assert "Fixed bug in PR 151" == rec_hi_3.sub_issues[452].get_commit(151, "merge_commit_sha_151").message


# def test_generate_isolated_record_types_with_labels_no_type_defined()
#   - single issue record
#   - single hierarchy issue record - no sub-issues
#   - single hierarchy issue record - two sub-issues without PRs
#   - single hierarchy issue record - two sub-issues with PRs - no commits
#   - single hierarchy issue record - two sub-issues with PRs - with commits
#   - single pull request record
#   - single direct commit record


# def test_generate_isolated_record_types_no_labels_with_type_defined()
#   - single issue record
#   - single hierarchy issue record - no sub-issues
#   - single hierarchy issue record - two sub-issues without PRs
#   - single hierarchy issue record - two sub-issues with PRs - no commits
#   - single hierarchy issue record - two sub-issues with PRs - with commits
#   - single pull request record
#   - single direct commit record


# def test_generate_isolated_record_types_with_labels_with_type_defined()
#   - single issue record
#   - single hierarchy issue record - no sub-issues
#   - single hierarchy issue record - two sub-issues without PRs
#   - single hierarchy issue record - two sub-issues with PRs - no commits
#   - single hierarchy issue record - two sub-issues with PRs - with commits
#   - single pull request record
#   - single direct commit record


# def test_generate_records_with_deep_hierarchy_nesting()
