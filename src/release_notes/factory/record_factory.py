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

        for issue in issues:
            records[issue.number] = Record(issue)

        for pull in pulls:
            # TODO - check pr description for release notes mentions
            parent_issue = 0
            if False:
                records[parent_issue].register_pull_request(pull)

        return records
