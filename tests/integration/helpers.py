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
"""Non-fixture helper functions for offline integration tests.

Keeping these in a dedicated module (rather than conftest.py) avoids
importing helpers from the pytest plugin file and prevents double-import /
module-state issues.
"""

import os
import tempfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.model.mined_data import MinedData


def reset_action_inputs_caches() -> None:
    """Reset all class-level caches on ActionInputs to their initial state.

    Call this from an autouse fixture so every test starts from a clean slate.
    Centralised here so that knowledge of ActionInputs internals is confined
    to one place in the test tree rather than spread across fixtures.
    """
    # pylint: disable=protected-access
    ActionInputs._row_format_hierarchy_issue = None  # type: ignore[attr-defined]
    ActionInputs._row_format_issue = None  # type: ignore[attr-defined]
    ActionInputs._row_format_pr = None  # type: ignore[attr-defined]
    ActionInputs._row_format_link_pr = None  # type: ignore[attr-defined]
    ActionInputs._owner = ""  # type: ignore[attr-defined]
    ActionInputs._repo_name = ""  # type: ignore[attr-defined]
    ActionInputs._super_chapters_raw = None  # type: ignore[attr-defined]
    ActionInputs._super_chapters_cache = None  # type: ignore[attr-defined]


def capture_run(patch_env: Callable, overrides: dict[str, str] | None = None) -> str:
    """Apply env overrides, run main.run() and return the captured release notes string.

    Parameters:
        patch_env: The patch_env fixture callable from the calling test.
        overrides: Optional mapping of INPUT_* env var names to values that
            extend or override the base environment defined in conftest._BASE_ENV.

    Returns:
        The release-notes output value extracted from the GitHub Actions
        output file (``GITHUB_OUTPUT``).
    """
    import main  # pylint: disable=import-outside-toplevel

    patch_env(overrides)
    with tempfile.NamedTemporaryFile(mode="r", suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    previous_github_output = os.environ.get("GITHUB_OUTPUT")
    try:
        os.environ["GITHUB_OUTPUT"] = tmp_path
        main.run()
        with open(tmp_path, encoding="utf-8") as f:
            raw = f.read()
    finally:
        if previous_github_output is None:
            os.environ.pop("GITHUB_OUTPUT", None)
        else:
            os.environ["GITHUB_OUTPUT"] = previous_github_output
        Path(tmp_path).unlink(missing_ok=True)

    # Parse the GitHub Actions output format: "name<<EOF\nvalue\nEOF\n"
    lines = raw.splitlines()
    notes_lines: list[str] = []
    inside = False
    for line in lines:
        if line == "release-notes<<EOF":
            inside = True
            continue
        if line == "EOF" and inside:
            break
        if inside:
            notes_lines.append(line)
    return "\n".join(notes_lines)


def build_mined_data(
    repo: Repository,
    issues: list[tuple[Issue, Repository]],
    pull_requests: list[tuple[PullRequest, Repository]],
    commits: list[tuple[Commit, Repository]],
    release: GitRelease | None,
    since: datetime | None,
) -> MinedData:
    """Construct a MinedData instance from explicit lists of mocked objects."""
    data = MinedData(repo)
    data.release = release
    data.since = since
    data.issues = {issue: r for issue, r in issues}
    data.pull_requests = {pr: r for pr, r in pull_requests}
    data.commits = {commit: r for commit, r in commits}
    return data
