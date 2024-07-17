import logging
import traceback

from github import Github, Auth

from release_notes_generator.generator import ReleaseNotesGenerator
from release_notes_generator.model.custom_chapters import CustomChapters
from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.utils.gh_action import set_action_output, set_action_failed


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

        rls_notes = ReleaseNotesGenerator(py_github, custom_chapters).generate_release_notes()
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
