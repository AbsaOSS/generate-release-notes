import logging

from typing import Optional
from github import Github, Auth

from release_notes_generator.record.record_formatter import RecordFormatter
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.model.record import Record
from release_notes_generator.builder import ReleaseNotesBuilder
from release_notes_generator.record.record_factory import RecordFactory
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.constants import Constants

from release_notes_generator.utils.decorators import safe_call_decorator
from release_notes_generator.utils.utils import get_change_url
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ReleaseNotesGenerator:
    def __init__(self, github_instance: Github, custom_chapters: CustomChapters):
        self.github_instance = github_instance
        self.custom_chapters = custom_chapters
        self.rate_limiter = GithubRateLimiter(self.github_instance)
        self.safe_call = safe_call_decorator(self.rate_limiter)

    def generate_release_notes(self) -> Optional[str]:
        """
        Generates the release notes for a given repository.

        :return: The generated release notes as a string, or None if the repository could not be found.
        """
        repo = self.safe_call(self.github_instance.get_repo)(ActionInputs.get_github_repository())
        if repo is None:
            return None

        rls = self.safe_call(repo.get_latest_release)()
        if rls is None:
            logging.info(f"Latest release not found for {repo.full_name}. 1st release for repository!")

        since = rls.published_at if rls else repo.created_at
        issues = self.safe_call(repo.get_issues)(state=Constants.ISSUE_STATE_ALL, since=since)
        pulls = self.safe_call(repo.get_pulls)(state='closed')
        commits = self.safe_call(repo.get_commits)()

        changelog_url = get_change_url(tag_name=ActionInputs.get_tag_name(), repository=repo, git_release=rls)

        rls_notes_records: dict[int, Record] = RecordFactory.generate(
            github=self.github_instance,
            repo=repo,
            issues=list(issues),        # PaginatedList --> list
            pulls=list(pulls),          # PaginatedList --> list
            commits=list(commits)       # PaginatedList --> list
        )

        return ReleaseNotesBuilder(
            records=rls_notes_records,
            custom_chapters=self.custom_chapters,
            formatter=RecordFormatter(),
            warnings=ActionInputs.get_warnings(),
            print_empty_chapters=ActionInputs.get_print_empty_chapters(),
            changelog_url=changelog_url
        ).build()
