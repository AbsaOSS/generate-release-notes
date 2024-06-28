import logging

from github_integration.model.commit import Commit
from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.model.record import Record


class RecordFactory:
    """
    A class used to generate records for release notes.
    """

    @staticmethod
    def generate(issues: list[Issue], pulls: list[PullRequest], commits: list[Commit]) -> dict[int, Record]:
        """
        Generates a dictionary of ReleaseNotesRecord instances.
        The key is the issue or pr number.

        :param issues: The list of Issue instances.
        :param pulls: The list of PullRequest instances.
        :param commits: The list of Commit instances.
        :return: The dictionary of ReleaseNotesRecord instances.
        """
        records = {}
        pull_numbers = [pull.number for pull in pulls]

        for issue in issues:
            if issue.number not in pull_numbers:
                records[issue.number] = Record(issue)
                logging.debug(f"Created record for issue {issue.number}: {issue.title}")

        for pull in pulls:
            parent_issues_numbers = pull.mentioned_issues

            for parent_issues_number in parent_issues_numbers:
                if parent_issues_number not in records.keys():
                    logging.error(f"Detected PR {pull.number} linked to issue {parent_issues_number} which is not in the list of issues.")

                records[parent_issues_number].register_pull_request(pull)
                logging.debug(f"Registering PR {pull.number}: {pull.title} to Issue {parent_issues_number}: ")

            if len(parent_issues_numbers) == 0:
                records[pull.number] = Record()
                records[pull.number].register_pull_request(pull)
                logging.debug(f"Created record for PR {pull.number}: {pull.title}")

        # logging.debug(f"XXX Received {len(issues)} issues, {len(pulls)} PRs and {len(commits)} commits.")

        detected_PRs = 0
        for commit in commits:
            for key, record in records.items():
                if record.is_commit_sha_present(commit.sha):
                    record.register_commit(commit)
                    detected_PRs += 1
                    # logging.debug(f"XXX Commit SHA found in Pull merge commit SHA for record {key}, message: {commit.message}")

        # logging.debug(f"XXX Detected PRs from commits: {detected_PRs}")

        logging.info(f"Generated {len(records)} records from {len(issues)} issues and {len(pulls)} PRs.")
        return records
