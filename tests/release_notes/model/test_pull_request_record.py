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

import re
import pytest
from github.PullRequest import PullRequest

from release_notes_generator.model.pull_request_record import PullRequestRecord

# get_rls_notes

def test_get_rls_notes_coderabbit_ignores_groups(mocker):
    pr = mocker.Mock(spec=PullRequest)
    pr.state = PullRequestRecord.PR_STATE_CLOSED
    pr.number = 42
    pr.title = "PR with CR summary"
    pr.get_labels.return_value = []
    pr.body = (
        "Summary by CodeRabbit\n"
        "- **Improvements**\n"
        "  - Speed up\n"
        "- **Fixes**\n"
        "  - Crash fix\n"
        "  + Minor patch\n"
        "Other text"
    )

    rec = PullRequestRecord(pr)

    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_release_notes_title", return_value=r"^Release Notes:$")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.is_coderabbit_support_active", return_value=True)
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_coderabbit_release_notes_title", return_value="Summary by CodeRabbit")
    mocker.patch("release_notes_generator.action_inputs.ActionInputs.get_coderabbit_summary_ignore_groups", return_value=["Improvements"])

    notes = rec.get_rls_notes()
    assert notes == "  - Crash fix\n  + Minor patch"

# get_commit

def test_get_commit_found_and_missing(pull_request_record_merged):
    found = pull_request_record_merged.get_commit("merge_commit_sha")
    missing = pull_request_record_merged.get_commit("nonexistent")
    assert found is not None and getattr(found, "sha", None) == "merge_commit_sha"
    assert missing is None
