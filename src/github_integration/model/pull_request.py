import re
from datetime import datetime
from typing import Optional

from github.PullRequest import PullRequest as GitPullRequest

from github_integration.model.commit import Commit


class PullRequest:
    """
    A class used to represent a pull request in GitHub.
    """

    PR_STATE_CLOSED = "closed"

    def __init__(self, pull: GitPullRequest):
        """
        Constructs all the necessary attributes for the PullRequest object.

        :param pull: The GitPullRequest object.
        """
        self.__source_pull = pull

        # for local storage of data required additional API call
        self.__labels = None

        self.__body_contains_issue_mention = False
        self.__mentioned_issues: list[int] = self.__extract_issue_numbers_from_body()
        self.__merge_commits: Optional[list[Commit]] = None

    @property
    def id(self) -> int:
        """
        Gets the ID of the pull request.

        :return: The ID of the pull request as an integer.
        """
        return self.__source_pull.id

    @property
    def number(self) -> int:
        """
        Gets the number of the pull request.

        :return: The number of the pull request as an integer.
        """
        return self.__source_pull.number

    @property
    def title(self) -> str:
        """
        Gets the title of the pull request.

        :return: The title of the pull request as a string.
        """
        return self.__source_pull.title

    @property
    def body(self) -> str:
        """
        Gets the body of the pull request.

        :return: The body of the pull request as a string, or an empty string if there is no body.
        """
        return self.__source_pull.body if self.__source_pull.body else ""

    @property
    def state(self) -> str:
        """
        Gets the state of the pull request.

        :return: The state of the pull request as a string.
        """
        return self.__source_pull.state

    @property
    def created_at(self) -> datetime:
        """
        Gets the creation date of the pull request.

        :return: The creation date of the pull request as a datetime object.
        """
        return self.__source_pull.created_at

    @property
    def updated_at(self) -> datetime:
        """
        Gets the updated date of the pull request.

        :return: The updated date of the pull request as a datetime object.
        """
        return self.__source_pull.updated_at

    @property
    def closed_at(self) -> Optional[datetime]:
        """
        Gets the closed date of the pull request.

        :return: The closed date of the pull request as a datetime object, or None if the pull request is not closed.
        """
        return self.__source_pull.closed_at if self.__source_pull.closed_at else None

    @property
    def merged_at(self) -> Optional[datetime]:
        """
        Gets the merged date of the pull request.

        :return: The merged date of the pull request as a datetime object, or None if the pull request is not merged.
        """
        return self.__source_pull.merged_at if self.__source_pull.merged_at else None

    @property
    def assignee(self) -> Optional[str]:
        """
        Gets the assignee of the pull request.

        :return: The assignee of the pull request as a string, or None if there is no assignee.
        """
        return self.__source_pull.assignee.login if self.__source_pull.assignee else None

    @property
    def labels(self) -> list[str]:
        """
        Gets the labels of the pull request.

        :return: The labels of the pull request as a list of strings.
        """
        if self.__labels is None:
            self.__labels = [label.name for label in self.__source_pull.get_labels()]

        return self.__labels

    @property
    def is_merged(self) -> bool:
        """
        Checks if the pull request is merged.

        :return: True if the pull request is merged, False otherwise.
        """
        return self.state == self.PR_STATE_CLOSED and self.merged_at is not None and self.closed_at is not None

    @property
    def is_closed(self) -> bool:
        """
        Checks if the pull request is closed.

        :return: True if the pull request is closed, False otherwise.
        """
        return self.state == self.PR_STATE_CLOSED and self.closed_at is not None and self.merged_at is None

    @property
    def body_contains_issue_mention(self) -> bool:
        """
        Checks if the body of the pull request contains a mention of an issue.

        :return: True if the body of the pull request contains a mention of an issue, False otherwise.
        """
        return self.__body_contains_issue_mention

    @property
    def author(self) -> Optional[str]:
        """
        Gets the author of the pull request.

        :return: The author of the pull request as a string, or None if there is no author.
        """
        # TODO in Issue named 'Chapter line formatting - authors'
        # Note: maybe introduce merge author? as stand-alone attribute
        return self.__merge_commit_author()

    @property
    def contributors(self) -> list[str]:
        """
        Gets the contributors of the pull request.

        :return: The contributors of the pull request as a list of strings.
        """
        # TODO in Isssue named 'Chapter line formatting - contributors'
        return []

    @property
    def merge_commit_sha(self) -> str:
        """
        Gets the SHA of the merge commit of the pull request.

        :return: The SHA of the merge commit of the pull request as a string.
        """
        return self.__source_pull.merge_commit_sha

    @property
    def mentioned_issues(self) -> list[int]:
        """
        Gets the numbers of the issues mentioned in the body of the pull request.

        :return: The numbers of the issues mentioned in the body of the pull request as a list of integers.
        """
        return self.__mentioned_issues

    def __extract_issue_numbers_from_body(self) -> list[int]:
        """
        Extracts the numbers of the issues mentioned in the body of the pull request.

        :return: The numbers of the issues mentioned in the body of the pull request as a list of integers.
        """
        # Regex pattern to match issue numbers following keywords like "Close", "Fix", "Resolve"
        regex_pattern = re.compile(r'([Cc]los(e|es|ed)|[Ff]ix(es|ed)?|[Rr]esolv(e|es|ed))\s*#\s*([0-9]+)')

        # Extract all issue numbers from the PR body
        issue_matches = regex_pattern.findall(self.body)

        # Extract the issue numbers from the matches
        issue_numbers = [int(match[-1]) for match in issue_matches]

        if not self.__body_contains_issue_mention and len(issue_numbers) > 0:
            self.__body_contains_issue_mention = True

        return issue_numbers

    def contains_labels(self, labels: list[str]) -> bool:
        """
        Checks if the pull request contains any of the specified labels.

        :param labels: The labels to check for.
        :return: True if the pull request contains any of the specified labels, False otherwise.
        """
        for label in labels:
            if label in self.labels:
                return True
        return False

    def __merge_commit_author(self) -> Optional[str]:
        """
        Gets the author of the merge commit of the pull request.

        :return: The author of the merge commit of the pull request as a string, or None if there is no merge commit.
        """
        return None
        # if self.__merge_commits is None:
        #     return None

        # Note: check if idea of merge commit is valid - only one item in list?
        # return self.__merge_commits[0].author

    def register_commit(self, commit: Commit):
        """
        Registers a commit with the pull request.

        :param commit: The Commit object to register.
        """
        # TODO in in Issue named 'Chapter line formatting - authors' or in 'Chapter line formatting - contributors'
        #   Note: this naming is wrong
        #   - possible collection of merge commit - all commit call
        #   - possible collection of commits - direct PR call
        if self.__merge_commits is None:
            self.__merge_commits = []

        self.__merge_commits.append(commit)
