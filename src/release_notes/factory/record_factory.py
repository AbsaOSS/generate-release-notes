import logging

from github_integration.model.commit import Commit
from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.model.record import Record


class RecordFactory:

    @staticmethod
    def generate(issues: list[Issue], pulls: list[PullRequest], commits: list[Commit]) -> dict[int, Record]:
        """
        Generates a dictionary of ReleaseNotesRecord instances.
        The key is the issue or pr number.

        @param issues: The list of Issue instances.
        @param pulls: The list of PullRequest instances.

        @return: The dictionary of ReleaseNotesRecord instances.
        """
        records = {}
        pull_numbers = [pull.number for pull in pulls]

        for issue in issues:
            if issue.number not in pull_numbers:
                records[issue.number] = Record(issue)
                logging.debug(f"Created record for issue {issue.number}: {issue.title}")

        for pull in pulls:
            parent_issues_numbers = pull.extract_issue_numbers_from_body()

            for parent_issues_number in parent_issues_numbers:
                if parent_issues_number not in records.keys():
                    logging.error(f"Detected PR {pull.number} linked to issue {parent_issues_number} which is not in the list of issues.")

                records[parent_issues_number].register_pull_request(pull)
                logging.debug(f"Registering PR {pull.number}: {pull.title} to Issue {parent_issues_number}: ")

            if len(parent_issues_numbers) == 0:
                records[pull.number] = Record()
                records[pull.number].register_pull_request(pull)
                logging.debug(f"Created record for PR {pull.number}: {pull.title}")

        for commit in commits:
            for pull in pulls:
                if commit.sha in pull.merge_commit_sha:
                    logging.debug("Commit SHA found in Pull merge commit SHA for PR {pull.number}.")

        logging.info(f"Generated {len(records)} records from {len(issues)} issues and {len(pulls)} PRs.")
        return records
