from github_integration.model.pull_request import PullRequest
from release_notes.model.record import Record


class RecordFormatter:

    # Default entry row
    # - #37 _Example Issue without PR_ implemented by "Missing Assignee or Contributor"
    #   - Example Issue to show usage of feature label and closed Issue without linked PR.
    #   - Test release note without leading bullet
    #
    # - #52 _Add Tag into Release Draft_ implemented by @user in [#53](https://github.com/absa-group/living-doc-example-project/pull/53)

    DEFAULT_ISSUE_PATTERN: str = "- #{number} _{title}_ implemented by {developers} in {pull_requests}\n{release_note_rows}"
    DEFAULT_PULL_REQUESTS_PATTERN: str = "[#{number}]({url})"

    def __init__(self, issue_pattern: str = DEFAULT_ISSUE_PATTERN,
                 pull_requests_pattern: str = DEFAULT_PULL_REQUESTS_PATTERN):
        self.issue_pattern = issue_pattern
        self.pull_requests_pattern = pull_requests_pattern

    def format(self, record: Record) -> str:
        # create a dict of supported keys and values - from record
        params = {
            "title": record.gh_issue.title if record.gh_issue is not None else record.pulls[0].title,
            "number": record.gh_issue.number if record.gh_issue is not None else record.pulls[0].number,
            "labels": record.labels,
            "is_closed": record.is_closed,
            "is_pr": record.is_pr,
            "is_issue": record.is_issue,
            "developers": self._format_developers(record),
            "release_note_rows": self._format_release_note_rows(record),
            "pull_requests": self._format_pulls(record.pulls)
        }

        # print("DEBUG - Formatter params: ", params)

        # apply to pattern
        return self.issue_pattern.format(**params)

    def _format_pulls(self, pulls: list['PullRequest']) -> str:
        return ", ".join([self.pull_requests_pattern.format(number=pr.number, url=pr.url) for pr in pulls])

    def _format_developers(self, record: 'Record') -> str:
        developers = []
        # if record.gh_issue and record.gh_issue.assignees:
        #     developers.extend(record.gh_issue.assignees)
        # for pr in record.pulls:
        #     if pr.assignees:
        #         developers.extend(pr.assignees)
        return ', '.join(developers) if developers else "developers"

    def _format_release_note_rows(self, record: 'Record') -> str:
        return "  - release notes 1\n  - release notes 2"
        # return "\n  - ".join(record.release_note_rows()) if record.release_note_rows() else "  - No release notes"
