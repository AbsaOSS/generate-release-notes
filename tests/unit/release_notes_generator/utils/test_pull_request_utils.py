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
import pytest
import requests
from github.PullRequest import PullRequest

from release_notes_generator.utils import pull_request_utils as pru
from release_notes_generator.utils.pull_request_utils import (
    extract_issue_numbers_from_body,
)


# Auto-clear the lru_cache between tests
@pytest.fixture(autouse=True)
def clear_cache():
    pru.get_issues_for_pr.cache_clear()
    yield
    pru.get_issues_for_pr.cache_clear()


def _patch_action_inputs(monkeypatch, owner="OWN", repo="REPO", token="TOK"):
    monkeypatch.setattr(pru.ActionInputs, "get_github_owner", lambda: owner)
    monkeypatch.setattr(pru.ActionInputs, "get_github_repo_name", lambda: repo)
    monkeypatch.setattr(pru.ActionInputs, "get_github_token", lambda: token)

def _patch_issues_template(monkeypatch, template="Q {number} {owner} {name} {first}"):
    monkeypatch.setattr(pru, "ISSUES_FOR_PRS", template)
    monkeypatch.setattr(pru, "LINKED_ISSUES_MAX", 10)

# extract_issue_numbers_from_body


def test_extract_issue_numbers_from_body_no_issues(mocker, mock_repo):
    mock_pr = mocker.Mock(spec=PullRequest)
    mock_pr.body = "This PR does not fix any issues."
    issue_ids = extract_issue_numbers_from_body(mock_pr, mock_repo)
    assert issue_ids == set()


def test_extract_issue_numbers_from_body_single_issue(mocker, mock_repo):
    mock_pr = mocker.Mock(spec=PullRequest)
    mock_pr.body = "This PR closes #123."
    issue_ids = extract_issue_numbers_from_body(mock_pr, mock_repo)
    assert issue_ids == {'org/repo#123'}


def test_extract_issue_numbers_from_body_multiple_issues(mocker, mock_repo):
    mock_pr = mocker.Mock(spec=PullRequest)
    mock_pr.body = "This PR fixes #123 and resolves #456."
    issue_ids = extract_issue_numbers_from_body(mock_pr, mock_repo)
    assert issue_ids == {'org/repo#123', 'org/repo#456'}


def test_extract_issue_numbers_from_body_mixed_case_keywords(mocker, mock_repo):
    mock_pr = mocker.Mock(spec=PullRequest)
    mock_pr.body = "This PR Fixes #123 and Resolves #456."
    issue_ids = extract_issue_numbers_from_body(mock_pr, mock_repo)
    assert issue_ids == {'org/repo#123', 'org/repo#456'}


def test_extract_issue_numbers_from_body_no_body(mocker, mock_repo):
    mock_pr = mocker.Mock(spec=PullRequest)
    mock_pr.body = None
    issue_ids = extract_issue_numbers_from_body(mock_pr, mock_repo)
    assert issue_ids == set()


def test_extract_issue_numbers_from_body_complex_text_with_wrong_syntax(mocker, mock_repo):
    mock_pr = mocker.Mock(spec=PullRequest)
    mock_pr.body = """
    This PR does a lot:
    - closes #123
    - fixes issue #456
    - resolves the bug in #789
    """
    issue_ids = extract_issue_numbers_from_body(mock_pr, mock_repo)
    assert issue_ids == {'org/repo#123'}


# get_issues_for_pr


def test_get_issues_for_pr_success(monkeypatch):
    _patch_action_inputs(monkeypatch)
    _patch_issues_template(monkeypatch)

    captured = {}
    class Resp:
        def raise_for_status(self): pass
        def json(self):
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {
                                "nodes": [{"number": 11}, {"number": 22}]
                            }
                        }
                    }
                }
            }

    def fake_graphql_query(url, json=None, headers=None, verify=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["verify"] = verify
        captured["timeout"] = timeout
        return Resp()

    monkeypatch.setattr(pru.Requester, "graphql_query", fake_graphql_query)

    result = pru.get_issues_for_pr(123)
    assert result == {'OWN/REPO#11', 'OWN/REPO#22'}
    assert captured["url"] == "https://api.github.com/graphql"
    # Query string correctly formatted
    assert captured["json"]["query"] == "Q 123 OWN REPO 10"
    # Headers include token
    assert captured["headers"]["Authorization"] == "Bearer TOK"
    assert captured["verify"] is False
    assert captured["timeout"] == 10

def test_get_issues_for_pr_empty_nodes(monkeypatch):
    _patch_action_inputs(monkeypatch)
    _patch_issues_template(monkeypatch)

    class Resp:
        def raise_for_status(self): pass
        def json(self):
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {"nodes": []}
                        }
                    }
                }
            }

    monkeypatch.setattr(pru.requests, "post", lambda *a, **k: Resp())
    assert pru.get_issues_for_pr(5) == set()

def test_get_issues_for_pr_http_error(monkeypatch):
    _patch_action_inputs(monkeypatch)
    _patch_issues_template(monkeypatch)

    class Resp:
        def raise_for_status(self):
            raise requests.HTTPError("Boom")
        def json(self):
            return {}

    monkeypatch.setattr(pru.requests, "post", lambda *a, **k: Resp())

    with pytest.raises(requests.HTTPError):
        pru.get_issues_for_pr(77)

def test_get_issues_for_pr_malformed_response(monkeypatch):
    _patch_action_inputs(monkeypatch)
    _patch_issues_template(monkeypatch)

    class Resp:
        def raise_for_status(self): pass
        def json(self):
            # Missing the expected nested keys -> triggers KeyError
            return {"data": {}}

    monkeypatch.setattr(pru.requests, "post", lambda *a, **k: Resp())

    with pytest.raises(KeyError):
        pru.get_issues_for_pr(42)

def test_get_issues_for_pr_caching(monkeypatch):
    _patch_action_inputs(monkeypatch)
    _patch_issues_template(monkeypatch)

    calls = {"count": 0}
    class Resp:
        def raise_for_status(self): pass
        def json(self):
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {"nodes": [{"number": 9}]}
                        }
                    }
                }
            }

    def fake_post(*a, **k):
        calls["count"] += 1
        return Resp()

    monkeypatch.setattr(pru.requests, "post", fake_post)

    first = pru.get_issues_for_pr(900)
    second = pru.get_issues_for_pr(900)  # should use cache
    assert first == {'OWN/REPO#9'} and second == {'OWN/REPO#9'}
    assert calls["count"] == 1  # only one network call

def test_get_issues_for_pr_different_numbers_not_cached(monkeypatch):
    _patch_action_inputs(monkeypatch)
    _patch_issues_template(monkeypatch)

    calls = {"nums": []}
    class Resp:
        def __init__(self, n): self.n = n
        def raise_for_status(self): pass
        def json(self):
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {"nodes": [{"number": self.n}]}
                        }
                    }
                }
            }

    def fake_post(url, json=None, **k):
        # Extract pull number back from formatted query tail
        pull_num = int(json["query"].split()[1])
        calls["nums"].append(pull_num)
        return Resp(pull_num)

    monkeypatch.setattr(pru.requests, "post", fake_post)

    r1 = pru.get_issues_for_pr(1)
    r2 = pru.get_issues_for_pr(2)
    assert r1 == {'OWN/REPO#1'}
    assert r2 == {'OWN/REPO#2'}
    assert calls["nums"] == [1, 2]
