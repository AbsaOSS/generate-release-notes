import logging

from github_integration.model.issue import Issue
from github_integration.model.pull_request import PullRequest
from release_notes.model.record import Record


class RecordFactory:

    @staticmethod
    def generate(issues: list[Issue], pulls: list[PullRequest]) -> dict[int, Record]:
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

        for pull in pulls:
            for parent_issues_number in pull.extract_issue_numbers_from_body():
                if parent_issues_number not in records.keys():
                    logging.warning(f"Detected PR {pull.number} linked to issue {parent_issues_number} "
                                    f"which is not in the list of issues.")
                    # TODO - How to handle this case? - new extra service chapter?

                records[parent_issues_number].register_pull_request(pull)

        return records
