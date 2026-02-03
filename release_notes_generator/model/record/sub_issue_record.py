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
A module for the SubIssueRecord class, which represents a sub-issue record in the release notes.
"""

import logging
from typing import Optional

from github.Issue import SubIssue, Issue

from release_notes_generator.model.record.issue_record import IssueRecord

logger = logging.getLogger(__name__)


class SubIssueRecord(IssueRecord):
    """
    Represents a sub-issue record in the release notes.
    Inherits from IssueRecord and specializes behavior for sub-issues.
    """

    def __init__(self, sub_issue: SubIssue | Issue, issue_labels: Optional[list[str]] = None, skip: bool = False):
        super().__init__(sub_issue, issue_labels, skip)

    # properties - override IssueRecord properties

    # properties - specific to IssueRecord
