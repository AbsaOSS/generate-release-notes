import json
import logging
import traceback

from typing import Optional
from github import Github, Auth

from github_integration.gh_action import get_input, set_output, set_failed
from github_integration.gh_api_caller import (get_gh_repository, fetch_latest_release, fetch_closed_issues,
                                              fetch_finished_pull_requests, generate_change_url, show_rate_limit)
from release_notes.release_notes_builder import ReleaseNotesBuilder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def validate_inputs(owner: str, repo_name: str, tag_name: str, chapters_json: str, warnings: bool,
                    published_at: bool, skip_release_notes_label: str, print_empty_chapters: bool,
                    chapters_to_pr_without_issue: bool):
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

    logging.debug(f'Repository: {owner}/{repo_name}')
    logging.debug(f'Tag name: {tag_name}')
    logging.debug(f'Chapters JSON: {chapters_json}')
    logging.debug(f'Warnings: {warnings}')
    logging.debug(f'Published at: {published_at}')
    logging.debug(f'Skip release notes label: {skip_release_notes_label}')
    logging.debug(f'Print empty chapters: {print_empty_chapters}')
    logging.debug(f'Chapters to PR without issue: {chapters_to_pr_without_issue}')


def release_notes_generator(g: Github, repository_id: str, tag_name: str, chapters_json: str, warnings: bool,
                           published_at: bool, skip_release_notes_label: str, print_empty_chapters: bool,
                           chapters_to_pr_without_issue: bool) -> Optional[str]:
    # get GitHub repository object (1 API call)
    if (repository := get_gh_repository(g, repository_id)) is None: return None

    # get latest release (1 API call)
    release = fetch_latest_release(repository)
    show_rate_limit(g)

    # get closed issues since last release (N API calls - pagination)
    issues = fetch_closed_issues(repository, release)
    show_rate_limit(g)

    # get finished PRs since last release
    pulls = fetch_finished_pull_requests(repository)
    show_rate_limit(g)

    # generate change url
    changelog_url = generate_change_url(repository, release, tag_name)

    # build rls notes
    return ReleaseNotesBuilder(issues, pulls, changelog_url, chapters_json, warnings, print_empty_chapters).build()


def run():
    logging.info("Starting 'Release Notes Generator' GitHub Action")

    try:
        local_repository_id = get_input('GITHUB_REPOSITORY')
        owner, repo_name = local_repository_id.split('/')

        github_token: str = get_input('github-token')

        tag_name = get_input('tag-name')
        chapters_json = get_input('chapters')
        warnings = get_input('warnings') == 'true'
        published_at = get_input('published-at') == 'true'
        skip_release_notes_label_raw = get_input('skip-release-notes-label')
        skip_release_notes_label = skip_release_notes_label_raw if skip_release_notes_label_raw else 'skip-release-notes'
        print_empty_chapters = get_input('print-empty-chapters') == 'true'
        chapters_to_pr_without_issue = get_input('chapters-to-pr-without-issue') == 'true'
        verbose = get_input('verbose').lower() == 'true'
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Init GitHub instance
        auth = Auth.Token(token=github_token)
        g = Github(auth=auth, per_page=100)
        show_rate_limit(g)

        validate_inputs(owner, repo_name, tag_name, chapters_json, warnings, published_at,
                        skip_release_notes_label, print_empty_chapters, chapters_to_pr_without_issue)

        rls_notes = release_notes_generator(g, local_repository_id, tag_name, chapters_json, warnings, published_at,
                                           skip_release_notes_label, print_empty_chapters, chapters_to_pr_without_issue)
        logging.debug(f"Release notes: \n{rls_notes}")

        set_output('release-notes', rls_notes)
        logging.info("GitHub Action 'Release Notes Generator' completed successfully")
        show_rate_limit(g)

    except Exception as error:
        stack_trace = traceback.format_exc()
        set_failed(f'Action failed with error: {error}\nStack trace: {stack_trace}')


if __name__ == '__main__':
    run()
