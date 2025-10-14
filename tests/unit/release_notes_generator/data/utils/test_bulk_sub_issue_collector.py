import json
import pytest

from release_notes_generator.data.utils.bulk_sub_issue_collector import (
    BulkSubIssueCollector,
    CollectorConfig,
)

class DummyResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._data


class DummySession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []  # capture posted payloads

    def post(self, url, headers=None, data=None, verify=None, timeout=None):
        self.requests.append(
            {
                "url": url,
                "headers": headers,
                "data": data,
                "verify": verify,
                "timeout": timeout,
            }
        )
        if not self._responses:
            raise AssertionError("No more fake responses queued")
        nxt = self._responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)


def make_collector(responses, **cfg_overrides):
    # Merge defaults with overrides to avoid duplicate keyword errors
    defaults = {
        "gentle_pacing_seconds": 0.0,
        "max_retries": 3,
        "base_backoff": 0.0,
    }
    defaults.update(cfg_overrides)
    cfg = CollectorConfig(**defaults)
    session = DummySession(responses)
    col = BulkSubIssueCollector(token="t", cfg=cfg, session=session)
    return col, session


def gql_parent_block(parent_num, nodes, has_next=False, end="CUR"):
    return {
        "number": parent_num,
        "subIssues": {
            "nodes": nodes,
            "pageInfo": {"hasNextPage": has_next, "endCursor": end if has_next else None},
        },
    }


def gql_child(number, org="org", repo="repo", total_children=0):
    return {
        "number": number,
        "repository": {"owner": {"login": org}, "name": repo},
        "subIssues": {"totalCount": total_children},
    }


def wrap_issue(alias_block_map):
    return {"data": alias_block_map}


def test_empty_input_returns_empty_list():
    col, _ = make_collector([])
    assert col.scan_sub_issues_for_parents([]) == []
    assert col.parents_sub_issues == {}


def test_parent_with_no_sub_issues():
    resp = wrap_issue(
        {
            "r0": {
                "i0_0": gql_parent_block(
                    1,
                    nodes=[],
                    has_next=False,
                )
            }
        }
    )
    col, _ = make_collector([DummyResponse(resp)])
    result = col.scan_sub_issues_for_parents(["org/repo#1"])
    assert result == []
    assert col.parents_sub_issues == {"org/repo#1": []}


def test_parent_with_children_and_new_parent_detection():
    resp = wrap_issue(
        {
            "r0": {
                "i0_0": gql_parent_block(
                    1,
                    nodes=[
                        gql_child(2, total_children=5),
                        gql_child(3, total_children=0),
                    ],
                    has_next=False,
                )
            }
        }
    )
    col, _ = make_collector([DummyResponse(resp)])
    result = col.scan_sub_issues_for_parents(["org/repo#1"])
    assert result == ["org/repo#2"]
    assert col.parents_sub_issues["org/repo#1"] == ["org/repo#2", "org/repo#3"]
    assert col.parents_sub_issues["org/repo#3"] == []
    assert "org/repo#2" not in col.parents_sub_issues or col.parents_sub_issues["org/repo#2"] in ([], [])


def test_pagination_accumulates_children_and_uses_cursor():
    resp1 = wrap_issue(
        {
            "r0": {
                "i0_0": gql_parent_block(
                    10,
                    nodes=[gql_child(2, total_children=1)],
                    has_next=True,
                    end="CUR1",
                )
            }
        }
    )
    resp2 = wrap_issue(
        {
            "r0": {
                "i0_0": gql_parent_block(
                    10,
                    nodes=[gql_child(3, total_children=0)],
                    has_next=False,
                )
            }
        }
    )
    col, session = make_collector([DummyResponse(resp1), DummyResponse(resp2)])
    new_parents = col.scan_sub_issues_for_parents(["org/repo#10"])
    assert new_parents == ["org/repo#2"]
    assert col.parents_sub_issues["org/repo#10"] == ["org/repo#2", "org/repo#3"]
    posted_bodies = [json.loads(r["data"])["query"] for r in session.requests]
    assert 'after: "CUR1"' in posted_bodies[1]


def test_multiple_new_parents_sorted():
    resp = wrap_issue(
        {
            "r0": {
                "i0_0": gql_parent_block(
                    1,
                    nodes=[
                        gql_child(30, org="b_org", repo="r", total_children=1),
                        gql_child(5, org="a_org", repo="r", total_children=1),
                        gql_child(2, org="a_org", repo="r", total_children=0),
                    ],
                    has_next=False,
                )
            }
        }
    )
    col, _ = make_collector([DummyResponse(resp)])
    new_parents = col.scan_sub_issues_for_parents(["org/repo#1"])
    assert new_parents == ["a_org/r#5", "b_org/r#30"]


def test_retry_on_exception_then_success(monkeypatch):
    resp_ok = wrap_issue(
        {
            "r0": {
                "i0_0": gql_parent_block(
                    7,
                    nodes=[],
                    has_next=False,
                )
            }
        }
    )
    col, session = make_collector(
        [RuntimeError("temp"), DummyResponse(resp_ok)],
        base_backoff=0.0,
        max_retries=2,
    )
    new_parents = col.scan_sub_issues_for_parents(["org/repo#7"])
    assert new_parents == []
    assert len(session.requests) == 2


def test_graphql_errors_raise_runtime_error():
    error_resp = {"data": {}, "errors": [{"message": "Something"}]}
    # Avoid retries so only one queued response is needed
    col, _ = make_collector([DummyResponse(error_resp)], max_retries=0)
    with pytest.raises(RuntimeError):
        col.scan_sub_issues_for_parents(["org/repo#1"])

def test_issue_node_missing_marks_parent_complete():
    # Response has repo alias but NO issue alias 'i0_0'
    resp = {
        "data": {
            "r0": {
                # different key ensures _find_alias_node returns None
                "unrelated": {}
            }
        }
    }
    col, _ = make_collector([DummyResponse(resp)])
    result = col.scan_sub_issues_for_parents(["org/repo#11"])
    assert result == []  # no new parents
    assert col.parents_sub_issues == {"org/repo#11": []}  # empty list recorded


def test_retry_exhaustion_raises():
    err = RuntimeError("temp-fail")
    # Provide enough exceptions to exhaust retries: max_retries = 2 -> attempts 0,1,2
    col, _ = make_collector([err, err, err], max_retries=2)
    with pytest.raises(RuntimeError) as ei:
        col.scan_sub_issues_for_parents(["org/repo#14"])
    assert "temp-fail" in str(ei.value)


def test_graphql_errors_line_coverage(caplog):
    # Minimal single-response error to cover:
    # if data.get("errors"): logger.error(...); raise RuntimeError(...)
    error_resp = {"data": {}, "errors": [{"message": "Direct failure"}]}
    col, _ = make_collector([DummyResponse(error_resp)], max_retries=1)
    with caplog.at_level("ERROR"):
        with pytest.raises(RuntimeError) as ei:
            col.scan_sub_issues_for_parents(["org/repo#123"])
    assert "GraphQL errors" in str(ei.value)
    assert any("GraphQL errors" in r.message for r in caplog.records)
