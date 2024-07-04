import logging
import traceback

from typing import Optional
from github import Github, Auth

from action.action_inputs import ActionInputs
from github_integration.gh_action import set_action_output, set_action_failed
from github_integration.github_manager import GithubManager

from release_notes.record_formatter import RecordFormatter
from release_notes.model.custom_chapters import CustomChapters
from release_notes.model.record import Record
from release_notes.release_notes_builder import ReleaseNotesBuilder
from release_notes.record_factory import RecordFactory


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def init_github_manager() -> None:
    auth = Auth.Token(token=ActionInputs.get_github_token())
    g = Github(auth=auth, per_page=100)
    GithubManager().github = g


def generate_release_notes(custom_chapters: CustomChapters) -> Optional[str]:
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

        init_github_manager()
        GithubManager().show_rate_limit()

        ActionInputs.validate_inputs()

        custom_chapters = (CustomChapters(print_empty_chapters=ActionInputs.get_print_empty_chapters())
                           .from_json(ActionInputs.get_chapters_json()))

        rls_notes = generate_release_notes(custom_chapters)
        logging.debug(f"Release notes: \n{rls_notes}")

        set_action_output('release-notes', rls_notes)
        logging.info("GitHub Action 'Release Notes Generator' completed successfully")
        GithubManager().show_rate_limit()

    except Exception as error:
        stack_trace = traceback.format_exc()
        logging.error(f'Action failed with error: {error}\nStack trace: {stack_trace}')
        set_action_failed(f'Action failed with error: {error}\nStack trace: {stack_trace}')


if __name__ == '__main__':
    run()
