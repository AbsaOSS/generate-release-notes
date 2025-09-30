"""
This script demonstrates how to use the BulkSubIssueCollector to find sub-issues
"""

import os
import urllib3

from release_notes_generator.data.utils.bulk_sub_issue_collector import CollectorConfig, BulkSubIssueCollector

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

token = os.getenv("GITHUB_TOKEN")
if token is None:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

# If you need to disable TLS verification (to mirror your example):
cfg = CollectorConfig(verify_tls=False)

collector = BulkSubIssueCollector(token, cfg=cfg)

new_parents = [
    "absa-group/AUL#2960",
]

while new_parents:
    new_parents = collector.scan_sub_issues_for_parents(new_parents)
    print("New parents found:", new_parents)
    print("Collected sub-issues so far:", collector.parents_sub_issues)
