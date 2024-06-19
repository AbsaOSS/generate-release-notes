from typing import Optional

from github_integration.model.issue import Issue


class Record:
    def __init__(self, issue: Optional[Issue] = None):
        self.gh_issue = issue
        self.pulls = []

    @property
    def is_pr(self):
        return self.gh_issue is None

    @property
    def is_issue(self):
        return self.gh_issue is not None

    @property
    def is_closed(self):
        if self.gh_issue is None:
            # no issue ==> stand-alone PR
            return self.pulls[0].is_merged
            # TODO - check if this is the final state of the PR - cancel
        else:
            return self.gh_issue.is_closed

    @property
    def labels(self) -> list[str]:
        if self.gh_issue is None:
            return self.pulls[0].labels
        else:
            return self.gh_issue.labels

    def register_pull_request(self, pull):
        self.pulls.append(pull)

    def to_rls_row(self):
        return "TODO"
        # if self.gh_issue is None:
        #     return self.pulls[0].
        # else:
        #     return self.gh_issue.releas_note_row
