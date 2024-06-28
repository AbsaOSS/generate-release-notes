import json
import logging
import traceback

from typing import Optional
from github import Github, Auth

from github_integration.gh_action import get_action_input, set_action_output, set_action_failed
from github_integration.github_manager import GithubManager

from release_notes.formatter.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder
from release_notes.factory.record_factory import RecordFactory


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ActionInputs:
    GITHUB_REPOSITORY = 'GITHUB_REPOSITORY'
    GITHUB_TOKEN = 'github-token'
    TAG_NAME = 'tag-name'
    CHAPTERS = 'chapters'
    WARNINGS = 'warnings'
    PUBLISHED_AT = 'published-at'
    SKIP_RELEASE_NOTES_LABEL = 'skip-release-notes-label'
    PRINT_EMPTY_CHAPTERS = 'print-empty-chapters'
    CHAPTERS_TO_PR_WITHOUT_ISSUE = 'chapters-to-pr-without-issue'
    VERBOSE = 'verbose'

    @staticmethod
    def get_github_repository() -> str:
        return get_action_input(ActionInputs.GITHUB_REPOSITORY)

    @staticmethod
    def get_github_token() -> str:
        return get_action_input(ActionInputs.GITHUB_TOKEN)

    @staticmethod
    def get_tag_name() -> str:
        return get_action_input(ActionInputs.TAG_NAME)

    @staticmethod
    def get_chapters_json() -> str:
        return get_action_input(ActionInputs.CHAPTERS)

    @staticmethod
    def get_warnings() -> bool:
        return get_action_input(ActionInputs.WARNINGS).lower() == 'true'

    @staticmethod
    def get_published_at() -> bool:
        return get_action_input(ActionInputs.PUBLISHED_AT).lower() == 'true'

    @staticmethod
    def get_skip_release_notes_label() -> str:
        return get_action_input(ActionInputs.SKIP_RELEASE_NOTES_LABEL) or 'skip-release-notes'

    @staticmethod
    def get_print_empty_chapters() -> bool:
        return get_action_input(ActionInputs.PRINT_EMPTY_CHAPTERS).lower() == 'true'

    @staticmethod
    def get_chapters_to_pr_without_issue() -> bool:
        return get_action_input(ActionInputs.CHAPTERS_TO_PR_WITHOUT_ISSUE).lower() == 'true'

    @staticmethod
    def get_verbose() -> bool:
        return get_action_input(ActionInputs.VERBOSE).lower() == 'true'


def validate_inputs():
    """
    Validates the inputs provided for the release notes generator.

    :raises ValueError: If any of the inputs are invalid.
    """
    repository_id = ActionInputs.get_github_repository()
    if '/' in repository_id:
        owner, repo_name = ActionInputs.get_github_repository().split('/')
    else:
        owner = repo_name = ""

    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("Owner must be a non-empty string.")

    if not isinstance(repo_name, str) or not repo_name.strip():
        raise ValueError("Repo name must be a non-empty string.")

    tag_name = ActionInputs.get_tag_name()
    if not isinstance(tag_name, str) or not tag_name.strip():
        raise ValueError("Tag name must be a non-empty string.")

    try:
        chapters_json = ActionInputs.get_chapters_json()
        json.loads(chapters_json)
    except json.JSONDecodeError:
        raise ValueError("Chapters JSON must be a valid JSON string.")

    warnings = ActionInputs.get_warnings()
    if not isinstance(warnings, bool):
        raise ValueError("Warnings must be a boolean.")

    published_at = ActionInputs.get_published_at()
    if not isinstance(published_at, bool):
        raise ValueError("Published at must be a boolean.")

    skip_release_notes_label = ActionInputs.get_skip_release_notes_label()
    if not isinstance(skip_release_notes_label, str) or not skip_release_notes_label.strip():
        raise ValueError("Skip release notes label must be a non-empty string.")

    print_empty_chapters = ActionInputs.get_print_empty_chapters()
    if not isinstance(print_empty_chapters, bool):
        raise ValueError("Print empty chapters must be a boolean.")

    chapters_to_pr_without_issue = ActionInputs.get_chapters_to_pr_without_issue()
    if not isinstance(chapters_to_pr_without_issue, bool):
        raise ValueError("Chapters to PR without issue must be a boolean.")

    verbose = ActionInputs.get_verbose()
    if not isinstance(verbose, bool):
        raise ValueError("Verbose logging must be a boolean.")

    logging.debug(f'Repository: {owner}/{repo_name}')
    logging.debug(f'Tag name: {tag_name}')
    logging.debug(f'Chapters JSON: {chapters_json}')
    logging.debug(f'Warnings: {warnings}')
    logging.debug(f'Published at: {published_at}')
    logging.debug(f'Skip release notes label: {skip_release_notes_label}')
    logging.debug(f'Print empty chapters: {print_empty_chapters}')
    logging.debug(f'Chapters to PR without issue: {chapters_to_pr_without_issue}')
    logging.debug(f'Verbose logging: {verbose}')


def release_notes_generator(custom_chapters: CustomChapters) -> Optional[str]:
    """
    Generates the release notes for a given repository.

    :return: The generated release notes as a string, or None if the repository could not be found.
    """
    # get GitHub repository object (1 API call)
    if GithubManager().fetch_repository(ActionInputs.get_github_repository()) is None:
        return None

    # get latest release (1 API call)
    GithubManager().fetch_latest_release()
    GithubManager().show_rate_limit()

    # get closed issues since last release (N API calls - pagination)
    issues = GithubManager().fetch_issues()
    GithubManager().show_rate_limit()

    # get finished PRs since last release
    pulls = GithubManager().fetch_pull_requests()
    GithubManager().show_rate_limit()

    # get commits since last release
    commits = GithubManager().fetch_commits()

    # generate change url
    changelog_url = GithubManager().get_change_url(ActionInputs.get_tag_name())

    # merge data to Release Notes records form
    rls_notes_records: dict[int, Record] = RecordFactory.generate(
        issues=issues,
        pulls=pulls,
        commits=commits
    )

    formatter = RecordFormatter()

    # build rls notes
    return ReleaseNotesBuilder(
        records=rls_notes_records,
        custom_chapters=custom_chapters,
        formatter=formatter,
        warnings=ActionInputs.get_warnings(),
        print_empty_chapters=ActionInputs.get_print_empty_chapters(),
        changelog_url=changelog_url
    ).build()


def run():
    """
    Runs the 'Release Notes Generator' GitHub Action.
    """
    logging.info("Starting 'Release Notes Generator' GitHub Action")

    try:
        if ActionInputs.get_verbose():
            logging.info("Verbose logging enabled")
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.info("Verbose logging disabled")

        # Init GitHub instance
        auth = Auth.Token(token=ActionInputs.get_github_token())
        g = Github(auth=auth, per_page=100)
        GithubManager().github = g    # creat singleton instance and init with g (Github)
        GithubManager().show_rate_limit()

        validate_inputs()

        custom_chapters = CustomChapters(print_empty_chapters=ActionInputs.get_print_empty_chapters())
        custom_chapters.from_json(ActionInputs.get_chapters_json())

        rls_notes = release_notes_generator(custom_chapters)
        logging.debug(f"Release notes: \n{rls_notes}")

        set_action_output('release-notes', rls_notes)
        logging.info("GitHub Action 'Release Notes Generator' completed successfully")
        GithubManager().show_rate_limit()

    except Exception as error:
        stack_trace = traceback.format_exc()
        set_action_failed(f'Action failed with error: {error}\nStack trace: {stack_trace}')


if __name__ == '__main__':
    run()
