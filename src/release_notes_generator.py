import logging
import traceback

from typing import Optional, Callable
from github import Github, Auth

from release_notes.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder
from release_notes.record_factory import RecordFactory
from action_inputs import ActionInputs
from utils.constants import Constants

from utils.decorators import safe_call_decorator
from utils.utils import get_change_url
from utils.github_rate_limiter import GithubRateLimiter
from utils.gh_action import set_action_output, set_action_failed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_release_notes(g: Github, custom_chapters: CustomChapters) -> Optional[str]:
    """
    Generates the release notes for a given repository.

    :param g: Github instance.
    :param custom_chapters: Custom chapters to include in the release notes.
    :return: The generated release notes as a string, or None if the repository could not be found.
    """
    rate_limiter = GithubRateLimiter(g)
    safe_call = safe_call_decorator(rate_limiter)

    # get GitHub repository object (1 API call)
    if repo := safe_call(g.get_repo, ActionInputs.get_github_repository()) is None:
        return None

    # get latest release (1 API call)
    rls = safe_call(repo.get_latest_release)

    # get all issues since last release (N API calls - pagination)
    since = rls.published_at if rls else None
    issues = safe_call(repo.get_issues, state=Constants.ISSUE_STATE_ALL, since=since)

    # get finished PRs since last release (N API calls - pagination)
    pulls = safe_call(repo.get_pulls, state='closed')

    # get commits since last release (N API calls - pagination)
    # experimental: not possible to pair all returned commits by sha to PRs
    commits = safe_call(repo.get_commits)

    # generate change url
    changelog_url = get_change_url(tag_name=ActionInputs.get_tag_name(), repository=repo, git_release=rls)

    # merge data to Release Notes records form
    rls_notes_records: dict[int, Record] = RecordFactory.generate(
        github=g,
        repo=repo,
        issues=issues,
        pulls=pulls,
        commits=commits
    )

    # build rls notes
    return ReleaseNotesBuilder(
        records=rls_notes_records,
        custom_chapters=custom_chapters,
        formatter=RecordFormatter(),
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
        # Enable verbose logging if specified
        if ActionInputs.get_verbose():
            logging.info("Verbose logging enabled")
            logging.getLogger().setLevel(logging.DEBUG)

        # Authenticate with GitHub
        py_github = Github(auth=Auth.Token(token=ActionInputs.get_github_token()), per_page=100)

        ActionInputs.validate_inputs()

        # Load custom chapters configuration
        custom_chapters = (CustomChapters(print_empty_chapters=ActionInputs.get_print_empty_chapters())
                           .from_json(ActionInputs.get_chapters_json()))

        rls_notes = generate_release_notes(py_github, custom_chapters)
        logging.debug(f"Release notes: \n{rls_notes}")

        # Set the output for the GitHub Action
        set_action_output('release-notes', rls_notes)
        logging.info("GitHub Action 'Release Notes Generator' completed successfully")

    except Exception as error:
        stack_trace = traceback.format_exc()
        logging.error(f'Action failed with error: {error}\nStack trace: {stack_trace}')
        set_action_failed(f'Action failed with error: {error}\nStack trace: {stack_trace}')


if __name__ == '__main__':
    run()
