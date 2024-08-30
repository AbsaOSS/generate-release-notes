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


# Action inputs environment variables
GITHUB_REPOSITORY = 'GITHUB_REPOSITORY'
GITHUB_TOKEN = 'github-token'
TAG_NAME = 'tag-name'
CHAPTERS = 'chapters'
PUBLISHED_AT = 'published-at'
SKIP_RELEASE_NOTES_LABEL = 'skip-release-notes-label'
VERBOSE = 'verbose'
RUNNER_DEBUG = 'RUNNER_DEBUG'

# Features
WARNINGS = 'warnings'
PRINT_EMPTY_CHAPTERS = 'print-empty-chapters'
CHAPTERS_TO_PR_WITHOUT_ISSUE = 'chapters-to-pr-without-issue'

# Pull Request states
PR_STATE_CLOSED = "closed"
PR_STATE_OPEN = "open"

# Issue states
ISSUE_STATE_CLOSED = "closed"
ISSUE_STATE_OPEN = "open"
ISSUE_STATE_ALL = "all"

# Release notes comment constants
RELEASE_NOTE_DETECTION_PATTERN = "Release notes:"
RELEASE_NOTE_LINE_MARK = "-"

# Service chapters titles
CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: str = "Closed Issues without Pull Request ⚠️"
CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: str = "Closed Issues without User Defined Labels ⚠️"

MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Merged PRs without Issue and User Defined Labels ⚠️"
CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Closed PRs without Issue and User Defined Labels ⚠️"

MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES: str = "Merged PRs Linked to 'Not Closed' Issue ⚠️"

OTHERS_NO_TOPIC: str = "Others - No Topic ⚠️"

# Record formatter patterns
DEFAULT_ISSUE_PATTERN: str = ("- #{number} _{title}_ implemented by {developers} in {pull_requests}\n"
                              "{release_note_rows}")
DEFAULT_PULL_REQUESTS_PATTERN: str = "[#{number}]({url})"
