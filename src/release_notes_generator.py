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
github_manager = GithubManager()


def validate_inputs(owner: str, repo_name: str, tag_name: str, chapters_json: str, warnings: bool,
                    published_at: bool, skip_release_notes_label: str, print_empty_chapters: bool,
                    chapters_to_pr_without_issue: bool, verbose: bool):
    """
    Validates the inputs provided for the release notes generator.

    :param owner: The owner of the repository.
    :param repo_name: The name of the repository.
    :param tag_name: The name of the tag.
    :param chapters_json: The JSON string containing the chapters.
    :param warnings: A boolean indicating whether to show warnings.
    :param published_at: A boolean indicating whether to show the published date.
    :param skip_release_notes_label: The label to skip release notes.
    :param print_empty_chapters: A boolean indicating whether to print empty chapters.
    :param chapters_to_pr_without_issue: A boolean indicating whether to add chapters to PR without issue.
    :param verbose: A boolean indicating whether to enable verbose logging.
    :raises ValueError: If any of the inputs are invalid.
    """
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("Owner must be a non-empty string.")

    if not isinstance(repo_name, str) or not repo_name.strip():
        raise ValueError("Repo name must be a non-empty string.")

    if not isinstance(tag_name, str) or not tag_name.strip():
        raise ValueError("Tag name must be a non-empty string.")

    try:
        chapters_data = json.loads(chapters_json)
    except json.JSONDecodeError:
        raise ValueError("Chapters JSON must be a valid JSON string.")

    if not isinstance(warnings, bool):
        raise ValueError("Warnings must be a boolean.")

    if not isinstance(published_at, bool):
        raise ValueError("Published at must be a boolean.")

    if not isinstance(skip_release_notes_label, str) or not skip_release_notes_label.strip():
        raise ValueError("Skip release notes label must be a non-empty string.")

    if not isinstance(print_empty_chapters, bool):
        raise ValueError("Print empty chapters must be a boolean.")

    if not isinstance(chapters_to_pr_without_issue, bool):
        raise ValueError("Chapters to PR without issue must be a boolean.")

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


def release_notes_generator(repository_id: str, tag_name: str, custom_chapters: CustomChapters, warnings: bool,
                            published_at: bool, skip_release_notes_label: str, print_empty_chapters: bool,
                            chapters_to_pr_without_issue: bool) -> Optional[str]:
    """
    Generates the release notes for a given repository.

    :param g: The Github instance.
    :param repository_id: The ID of the repository.
    :param tag_name: The name of the tag.
    :param custom_chapters: The custom chapters for the release notes.
    :param warnings: A boolean indicating whether to show warnings.
    :param published_at: A boolean indicating whether to show the published date.
    :param skip_release_notes_label: The label to skip release notes.
    :param print_empty_chapters: A boolean indicating whether to print empty chapters.
    :param chapters_to_pr_without_issue: A boolean indicating whether to add chapters to PR without issue.
    :return: The generated release notes as a string, or None if the repository could not be found.
    """
    # get GitHub repository object (1 API call)
    if (repository := GithubManager().fetch_repository(repository_id)) is None: return None

    # get latest release (1 API call)
    release = GithubManager().fetch_latest_release()
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
    changelog_url = GithubManager().get_change_url(tag_name)

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
        warnings=warnings,
        print_empty_chapters=print_empty_chapters,
        changelog_url=changelog_url
    ).build()


def run():
    """
    Runs the 'Release Notes Generator' GitHub Action.
    """
    logging.info("Starting 'Release Notes Generator' GitHub Action")

    try:
        local_repository_id = get_action_input('GITHUB_REPOSITORY')
        owner, repo_name = local_repository_id.split('/')

        github_token: str = get_action_input('github-token')

        tag_name = get_action_input('tag-name')
        chapters_json = get_action_input('chapters')
        warnings = get_action_input('warnings') == 'true'
        published_at = get_action_input('published-at') == 'true'
        skip_release_notes_label_raw = get_action_input('skip-release-notes-label')
        skip_release_notes_label = skip_release_notes_label_raw if skip_release_notes_label_raw else 'skip-release-notes'
        print_empty_chapters = get_action_input('print-empty-chapters') == 'true'
        chapters_to_pr_without_issue = get_action_input('chapters-to-pr-without-issue') == 'true'
        verbose = get_action_input('verbose').lower() == 'true'
        if verbose:
            logging.info("Verbose logging enabled")
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.info("Verbose logging disabled")

        # Init GitHub instance
        auth = Auth.Token(token=github_token)
        g = Github(auth=auth, per_page=100)
        GithubManager().github = g    # creat singleton instance and init with g (Github)
        GithubManager().show_rate_limit()

        validate_inputs(owner, repo_name, tag_name, chapters_json, warnings, published_at,
                        skip_release_notes_label, print_empty_chapters, chapters_to_pr_without_issue, verbose)

        custom_chapters = CustomChapters(print_empty_chapters=print_empty_chapters)
        custom_chapters.from_json(chapters_json)

        rls_notes = release_notes_generator(local_repository_id, tag_name, custom_chapters, warnings, published_at,
                                           skip_release_notes_label, print_empty_chapters, chapters_to_pr_without_issue)
        logging.debug(f"Release notes: \n{rls_notes}")

        set_action_output('release-notes', rls_notes)
        logging.info("GitHub Action 'Release Notes Generator' completed successfully")
        GithubManager().show_rate_limit()

    except Exception as error:
        stack_trace = traceback.format_exc()
        set_action_failed(f'Action failed with error: {error}\nStack trace: {stack_trace}')


if __name__ == '__main__':
    run()
