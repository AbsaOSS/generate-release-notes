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

    # TODO - 'Release notest:' as detection pattern default - can be defined by user
    # TODO - '-' as leading line mark for each release note to be used
    @property
    def get_rls_notes(self, detection_pattern="Release notes:", line_mark="-") -> str:
        release_notes = ""

        # Iterate over all PRs
        for pull in self.pulls:
            body_lines = pull.body.split('\n')
            inside_release_notes = False

            for line in body_lines:
                if detection_pattern in line:
                    inside_release_notes = True
                    continue

                if inside_release_notes:
                    if line.startswith(line_mark):
                        release_notes += f"  {line.strip()}\n"
                    else:
                        break

        # Return the concatenated release notes
        return release_notes.rstrip()

    def register_pull_request(self, pull):
        self.pulls.append(pull)

    # TODO add user defined row format feature
    def to_chapter_row(self, row_format=""):
        # Example of default format
        # - #37 _Example Issue without PR_ implemented by "Missing Assignee or Contributor"
        #   - Example Issue to show usage of feature label and closed Issue without linked PR.
        #   - Test release note without leading bullet
        # - #38 _Example Issue without Release notes comment_ implemented by "Missing Assignee or Contributor"

        if self.gh_issue is None:
            return f"{self.pulls[0].title}"
        else:
            return f"#{self.gh_issue.number} _{self.gh_issue.title}_ implemented by TODO\n{self.get_rls_notes}"
