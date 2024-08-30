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

import logging

from typing import Optional
from github import Github

from release_notes_generator.record.record_formatter import RecordFormatter
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.model.record import Record
from release_notes_generator.builder import ReleaseNotesBuilder
from release_notes_generator.record.record_factory import RecordFactory
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import ISSUE_STATE_ALL

from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.utils import get_change_url
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# pylint: disable=too-few-public-methods
class ReleaseNotesGenerator:
    def __init__(self, github_instance: Github, custom_chapters: CustomChapters):
        self.github_instance = github_instance
        self.custom_chapters = custom_chapters
        self.rate_limiter = GithubRateLimiter(self.github_instance)
        self.safe_call = safe_call_decorator(self.rate_limiter)

    def generate(self) -> Optional[str]:
        """
        Generates the release notes for a given repository.

        @return: The generated release notes as a string, or None if the repository could not be found.
        """
        repo = self.safe_call(self.github_instance.get_repo)(ActionInputs.get_github_repository())
        if repo is None:
            return None

        rls = self.safe_call(repo.get_latest_release)()
        if rls is None:
            logging.info("Latest release not found for %s. 1st release for repository!", repo.full_name)

        # default is repository creation date if no releases OR created_at of latest release
        since = rls.created_at if rls else repo.created_at
        if rls and ActionInputs.get_published_at():
            since = rls.published_at

        issues = self.safe_call(repo.get_issues)(state=ISSUE_STATE_ALL, since=since)
        pulls = pulls_all = self.safe_call(repo.get_pulls)(state='closed')
        commits = commits_all = list(self.safe_call(repo.get_commits)())

        if rls is not None:
            logging.info("Count of issues: %d", len(list(issues)))

            # filter out merged PRs and commits before the since date
            pulls = list(filter(lambda pull: pull.merged_at is not None and pull.merged_at > since, list(pulls_all)))
            logging.debug("Count of pulls reduced from %d to %d", len(list(pulls_all)), len(pulls))

            commits = list(filter(lambda commit: commit.commit.author.date > since, list(commits_all)))
            logging.debug("Count of commits reduced from %d to %d", len(list(commits_all)), len(commits))

        changelog_url = get_change_url(tag_name=ActionInputs.get_tag_name(), repository=repo, git_release=rls)

        rls_notes_records: dict[int, Record] = RecordFactory.generate(
            github=self.github_instance,
            repo=repo,
            issues=list(issues),        # PaginatedList --> list
            pulls=list(pulls),          # PaginatedList --> list
            commits=list(commits)       # PaginatedList --> list
        )

        release_notes_builder = ReleaseNotesBuilder(
            records=rls_notes_records,
            custom_chapters=self.custom_chapters,
            formatter=RecordFormatter(),
            changelog_url=changelog_url
        )

        return release_notes_builder.build()
