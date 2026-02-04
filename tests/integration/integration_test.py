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

# Integration test relocated per Constitution test directory structure.
# Performs a smoke scan of sub-issues when GITHUB_TOKEN is provided; otherwise skipped.
import os
import pytest
import urllib3

from release_notes_generator.data.utils.bulk_sub_issue_collector import CollectorConfig, BulkSubIssueCollector

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

pytestmark = pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set for integration test"
)


def test_bulk_sub_issue_collector_smoke():
    token = os.getenv("GITHUB_TOKEN")
    assert token is not None  # guarded by skip above
    cfg = CollectorConfig(verify_tls=False)
    collector = BulkSubIssueCollector(token, cfg=cfg)
    new_parents = ["absa-group/AUL#2960"]
    iterations = 0
    while new_parents and iterations < 2:  # limit iterations for test speed
        new_parents = collector.scan_sub_issues_for_parents(new_parents)
        iterations += 1
    # Collector internal state should be dict-like even if empty
    assert hasattr(collector, "parents_sub_issues")

