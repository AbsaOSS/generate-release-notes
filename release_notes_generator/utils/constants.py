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

"""
This module contains the constants used in the release notes generator.
"""

# Action inputs environment variables
GITHUB_REPOSITORY = "GITHUB_REPOSITORY"
GITHUB_TOKEN = "github-token"
TAG_NAME = "tag-name"
FROM_TAG_NAME = "from-tag-name"
CHAPTERS = "chapters"
DUPLICITY_SCOPE = "duplicity-scope"
DUPLICITY_ICON = "duplicity-icon"
PUBLISHED_AT = "published-at"
SKIP_RELEASE_NOTES_LABELS = "skip-release-notes-labels"
VERBOSE = "verbose"
RELEASE_NOTES_TITLE = "release-notes-title"
RUNNER_DEBUG = "RUNNER_DEBUG"
ROW_FORMAT_ISSUE = "row-format-issue"
ROW_FORMAT_PR = "row-format-pr"
ROW_FORMAT_LINK_PR = "row-format-link-pr"
SUPPORTED_ROW_FORMAT_KEYS = ["number", "title", "pull-requests"]

# Features
WARNINGS = "warnings"
PRINT_EMPTY_CHAPTERS = "print-empty-chapters"

# Pull Request states
PR_STATE_CLOSED = "closed"
PR_STATE_OPEN = "open"

# Issue states
ISSUE_STATE_CLOSED = "closed"
ISSUE_STATE_OPEN = "open"
ISSUE_STATE_ALL = "all"

# Release notes comment constants
RELEASE_NOTE_TITLE_DEFAULT = "[Rr]elease [Nn]otes:"
RELEASE_NOTE_LINE_MARKS = ["-", "*", "+"]

# Service chapters titles
CLOSED_ISSUES_WITHOUT_PULL_REQUESTS: str = "Closed Issues without Pull Request ⚠️"
CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS: str = "Closed Issues without User Defined Labels ⚠️"

MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Merged PRs without Issue and User Defined Labels ⚠️"
CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS: str = "Closed PRs without Issue and User Defined Labels ⚠️"

MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES: str = "Merged PRs Linked to 'Not Closed' Issue ⚠️"

OTHERS_NO_TOPIC: str = "Others - No Topic ⚠️"
