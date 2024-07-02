import logging

from github_integration.github_manager import GithubManager
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

        def create_record_for_issue(issue: Issue):
            records[issue.number] = Record(issue)
            logging.debug(f"Created record for issue {issue.number}: {issue.title}")

        def register_pull_request(pull: PullRequest):
            for parent_issue_number in pull.mentioned_issues:
                if parent_issue_number not in records:
                    logging.warning(
                        f"Detected PR {pull.number} linked to issue {parent_issue_number} which is not in the list of received issues. Fetching ..."
                    )
                    issue = GithubManager().fetch_issue(parent_issue_number)
                    create_record_for_issue(issue)
                records[parent_issue_number].register_pull_request(pull)
                logging.debug(
                    f"Registering PR {pull.number}: {pull.title} to Issue {parent_issue_number}"
                )

        def register_commit_to_record(commit: Commit):
            for record in records.values():
                if record.is_commit_sha_present(commit.sha):
                    record.register_commit(commit)
                    return True
            return False

        for issue in issues:
            if issue.number not in pull_numbers:
                create_record_for_issue(issue)

        for pull in pulls:
            if not pull.mentioned_issues:
                records[pull.number] = Record()
                records[pull.number].register_pull_request(pull)
                logging.debug(f"Created record for PR {pull.number}: {pull.title}")
            else:
                register_pull_request(pull)

        detected_prs = sum(register_commit_to_record(commit) for commit in commits)

        logging.info(f"Generated {len(records)} records from {len(issues)} issues and {len(pulls)} PRs, with {detected_prs} commits detected.")
        return records
