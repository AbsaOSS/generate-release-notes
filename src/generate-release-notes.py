# from github import Github
import os


def get_input(name: str) -> str:
    return os.getenv(f'INPUT_{name.replace("-", "_").upper()}')


def set_output(name: str, value: str):
    output_file = os.getenv('GITHUB_OUTPUT', None)
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f'{name}={value}\n')
    else:
        raise EnvironmentError('GITHUB_OUTPUT environment variable is not set.')


def set_failed(message: str):
    print(f'::error::{message}')
    exit(1)


def info(message: str):
    print(message)



 # OLD CODE
# def fetch_latest_release(github_instance, owner, repo):
#     print(f"Starting to fetch the latest release for {owner}/{repo}")
#     try:
#         release = github_instance.get_repo(f"{owner}/{repo}").get_latest_release()
#         print(f"Found latest release for {owner}/{repo}: {release.tag_name}, created at: {release.created_at}, published at: {release.published_at}")
#         return release
#     except Exception as error:
#         print(f"Fetching latest release for {owner}/{repo}: {error}")
#         return None
#
# def get_related_prs_for_issue(github_instance, issue_number, repo_owner, repo_name):
#     print(f"Fetching related PRs for issue #{issue_number}")
#     related_prs = github_instance.get_repo(f"{repo_owner}/{repo_name}").get_issue(issue_number).get_events()
#     pull_request_events = [event for event in related_prs if event.event == 'cross-referenced' and event.source.issue.pull_request is not None]
#     if pull_request_events:
#         print(f"Found {len(pull_request_events)} related PRs for issue #{issue_number}")
#     else:
#         print(f"Found 0 related PRs for issue #{issue_number}")
#     return pull_request_events
#
# def get_contributors(assignees, commit_authors):
#     login_assignees = [f"@{assignee.login}" for assignee in assignees]
#     combined = login_assignees + commit_authors
#     if not combined:
#         return {"\"Missing Assignee or Contributor\""}
#     return set(combined)
#
# def get_pr_commit_authors(github_instance, repo_owner, repo_name, related_prs):
#     commit_authors = set()
#     for event in related_prs:
#         authors = get_pr_commit_authors_by_pr_number(github_instance, repo_owner, repo_name, event.source.issue.number)
#         commit_authors.update(authors)
#     return commit_authors
#
# def get_pr_commit_authors_by_pr_number(github_instance, repo_owner, repo_name, pr_number):
#     commit_authors = set()
#     commits = github_instance.get_repo(f"{repo_owner}/{repo_name}").get_pull(pr_number).get_commits()
#     for commit in commits:
#         commit_authors.add(f"@{commit.author.login}")
#         co_authors = commit.commit.message.split('Co-authored-by:')
#         if len(co_authors) > 1:
#             for co_author_line in co_authors[1:]:
#                 email_match = re.search(r'<([^>]+)>', co_author_line)
#                 name_match = re.search(r'Co-authored-by: (.+) <', co_author_line)
#                 if email_match and name_match:
#                     email = email_match.group(1)
#                     name = name_match.group(1).strip()
#                     print(f"Searching for GitHub user with email: {email}")
#                     search_result = github_instance.search_users(f"{email} in:email")
#                     if search_result.totalCount > 0:
#                         commit_authors.add(f"@{search_result[0].login}")
#                     else:
#                         print(f"No public GitHub account found for email: {email}")
#                         commit_authors.add(name)
#     return commit_authors
#
# def get_issue_comments(github_instance, issue_number, repo_owner, repo_name):
#     return github_instance.get_repo(f"{repo_owner}/{repo_name}").get_issue(issue_number).get_comments()
#
# def get_pr_comments(github_instance, pr_number, repo_owner, repo_name):
#     return github_instance.get_repo(f"{repo_owner}/{repo_name}").get_pull(pr_number).get_review_comments()
#
# def extract_release_notes_from_comments(comments):
#     release_notes = []
#     for comment in comments:
#         if comment.body.lower().startswith('release notes'):
#             note_content = comment.body.replace(/^release notes:?.*(\r\n|\n|\r)?/i, '').strip()
#             processed_content = "\n".join(
#                 ["  - " + line.strip() if not line.startswith("-") else line.replace(/^\s*[\r\n]/gm, '').replace(/^/gm, '  ')
#             for line in note_content.split('\n')])
#             release_notes.append(processed_content)
#     return release_notes
#
# def sort_map_and_convert_to_string(map_data):
#     sorted_content_array = sorted(map_data.items(), key=lambda x: x[0])
#     return "\n".join([entry[1] for entry in sorted_content_array])

def run():
    print('Starting Release Notes Generator GitHub Action')

    try:
        tag_name = get_input('tag-name')
        chapters_json = get_input('chapters')
        warnings = get_input('warnings') == 'true'
        published_at = get_input('published-at') == 'true'
        skip_release_notes_label_raw = get_input('skip-release-notes-label')
        skip_release_notes_label = skip_release_notes_label_raw if skip_release_notes_label_raw else 'skip-release-notes'
        print_empty_chapters = get_input('print-empty-chapters') == 'true'
        chapters_to_pr_without_issue = get_input('chapters-to-pr-without-issue') == 'true'
        verbose_logging = get_input('verbose') == 'true'

        if verbose_logging:
            info(f'Verbose: {verbose_logging}')
            info(f'Tag name: {tag_name}')
            info(f'Chapters JSON: {chapters_json}')
            info(f'Warnings: {warnings}')
            info(f'Published at: {published_at}')
            info(f'Skip release notes label: {skip_release_notes_label}')
            info(f'Print empty chapters: {print_empty_chapters}')
            info(f'Chapters to PR without issue: {chapters_to_pr_without_issue}')


        # NEW CODE

    except Exception as error:
        print(f'Action failed with error: {error}')
        set_failed(f'Action failed with error: {error}')



    # OLD CODE
    # github_token = os.getenv('GITHUB_TOKEN')
    # tag_name = os.getenv('INPUT_TAG_NAME')
    # github_repository = os.getenv('GITHUB_REPOSITORY')
    # duplicate = "- _**[Duplicate]**_ #"
    #
    # if not github_token:
    #     raise ValueError("GitHub token is missing.")
    # if not github_repository:
    #     raise ValueError("GITHUB_REPOSITORY environment variable is missing.")
    # if not tag_name:
    #     raise ValueError("Tag name is missing.")
    #
    # owner, repo = github_repository.split('/')
    # repo_owner = owner
    # repo_name = repo
    # chapters_json = os.getenv('INPUT_CHAPTERS') or "[]"
    # warnings = os.getenv('INPUT_WARNINGS', 'true').lower() == 'true'
    # skip_label = os.getenv('INPUT_SKIP_RELEASE_NOTES_LABEL', 'skip-release-notes')
    # use_published_at = os.getenv('INPUT_PUBLISHED_AT', 'false').lower() == 'true'
    # print_empty_chapters = os.getenv('INPUT_PRINT_EMPTY_CHAPTERS', 'true').lower() == 'true'
    # chapters_to_pr_without_issue = os.getenv('INPUT_CHAPTERS_TO_PR_WITHOUT_ISSUE', 'true').lower() == 'true'
    #
    # github_instance = Github(github_token)
    # try:
    #     latest_release = fetch_latest_release(github_instance, repo_owner, repo_name)
    #
    #     closed_issues_only_issues = fetch_closed_issues(github_instance, repo_owner, repo_name, latest_release, use_published_at, skip_label)
    #     if closed_issues_only_issues:
    #         print(f"Found {len(closed_issues_only_issues)} closed issues (only Issues) since last release")
    #     else:
    #         print(f"Found 0 closed issues (only Issues) since last release")
    #
    #     titles_to_labels_map = parse_chapters_json(chapters_json)
    #     chapter_contents = {label: {} for label in titles_to_labels_map.keys()}
    #     closed_issues_without_release_notes = {}
    #     closed_issues_without_user_labels = {}
    #     closed_issues_without_pr = {}
    #     merged_prs_linked_to_open_issue = {}
    #     closed_prs_without_link_to_issue = {}
    #     merged_prs_without_link_to_issue = {}
    #
    #     for issue in closed_issues_only_issues:
    #         related_prs = get_related_prs_for_issue(github_instance, issue.number, repo_owner, repo_name)
    #         pr_links = ", ".join([f"[#{event.source.issue.number}]({event.source.issue.html_url})" for event in related_prs])
    #         release_notes_raw = get_release_notes_from_comments(github_instance, issue.number, issue.title, issue.assignees, repo_owner, repo_name, related_prs, pr_links)
    #         release_notes = release_notes_raw.replace(/^- x#/, '- #')
    #
    #         if warnings and release_notes_raw.startswith('- x#'):
    #             closed_issues_without_release_notes[issue.number] = release_notes
    #
    #         found_user_labels = False
    #         for title, labels in titles_to_labels_map.items():
    #             if any(label in [lbl.name for lbl in issue.labels] for label in labels):
    #         if found_user_labels:
    #             chapter_contents[title][issue.number] = release_notes.replace(/^- #/, duplicate)
    #         else:
    #             chapter_contents[title][issue.number] = release_notes
    #         found_user_labels = True
    #
    #         if not found_user_labels and warnings:
    #             closed_issues_without_user_labels[issue.number] = release_notes
    #
    #         if not related_prs and warnings:
    #             closed_issues_without_pr[issue.number] = release_notes
    #
    #         if warnings:
    #             merged_prs_since_last_release = fetch_pull_requests(github_instance, repo_owner, repo_name, latest_release, use_published_at, skip_label)
    #         if merged_prs_since_last_release:
    #             print(f"Found {len(merged_prs_since_last_release)} merged PRs since last release")
    #         for pr in sorted(merged_prs_since_last_release, key=lambda x: x.created_at):
    #             if not is_pr_linked_to_issue(github_instance, pr.number, repo_owner, repo_name):
    #         release_notes = get_release_notes_from_pr_comments(github_instance, pr.number, pr.title, pr.assignees, repo_owner, repo_name)
    #         found_user_labels = False
    #         if chapters_to_pr_without_issue:
    #             for title, labels in titles_to_labels_map.items():
    #         if any(label in [lbl.name for lbl in pr.labels] for label in labels):
    #             if found_user_labels:
    #         chapter_contents[title][pr.number] = release_notes.replace(/^- #/, duplicate)
    #         else:
    #         chapter_contents[title][pr.number] = release_notes
    #         found_user_labels = True
    #         if not found_user_labels:
    #             merged_prs_without_link_to_issue[pr.number] = release_notes
    #         else:
    #             if is_pr_linked_to_open_issue(github_instance, pr.number, repo_owner, repo_name):
    #         merged_prs_linked_to_open_issue[pr.number] = f"- #{pr.number} _{pr.title}_\n"
    #
    #         closed_prs_since_last_release = fetch_pull_requests(github_instance, repo_owner, repo_name, latest_release, use_published_at, skip_label, 'closed')
    #         if closed_prs_since_last_release:
    #             print(f"Found {len(closed_prs_since_last_release)} closed PRs since last release")
    #         for pr in sorted(closed_prs_since_last_release, key=lambda x: x.created_at):
    #             if not is_pr_linked_to_issue(github_instance, pr.number, repo_owner, repo_name):
    #         release_notes = get_release_notes_from_pr_comments(github_instance, pr.number, pr.title, pr.assignees, repo_owner, repo_name)
    #         found_user_labels = False
    #         if chapters_to_pr_without_issue:
    #             for title, labels in titles_to_labels_map.items():
    #         if any(label in [lbl.name for lbl in pr.labels] for label in labels):
    #             if found_user_labels:
    #         chapter_contents[title][pr.number] = release_notes.replace(/^- #/, duplicate)
    #         else:
    #         chapter_contents[title][pr.number] = release_notes
    #         found_user_labels = True
    #         if not found_user_labels:
    #             closed_prs_without_link_to_issue[pr.number] = release_notes
    #
    #         changelog_url = f"https://github.com/{repo_owner}/{repo_name}/compare/{latest_release.tag_name}...{tag_name}" if latest_release else f"https://github.com/{repo_owner}/{repo_name}/commits/{tag_name}"
    #         print('Changelog URL:', changelog_url)
    #
    #         release_notes = ''
    #         for title in titles_to_labels_map.keys():
    #             title_map = chapter_contents.get(title)
    #         if title_map and title_map:
    #             content = sort_map_and_convert_to_string(title_map)
    #         release_notes += f"### {title}\n" + (content if content else "No entries detected.") + "\n\n"
    #         else:
    #         if print_empty_chapters:
    #             release_notes += f"### {title}\nNo entries detected.\n\n"
    #
    #         if warnings:
    #             release_notes += f"### Closed Issues without Pull Request ⚠️\n" + (sort_map_and_convert_to_string(closed_issues_without_pr) or "All closed issues linked to a Pull Request.") + "\n\n"
    #         release_notes += f"### Closed Issues without User Defined Labels ⚠️\n" + (sort_map_and_convert_to_string(closed_issues_without_user_labels) or "All closed issues contain at least one of user defined labels.") + "\n\n"
    #         release_notes += f"### Closed Issues without Release Notes ⚠️\n" + (sort_map_and_convert_to_string(closed_issues_without_release_notes) or "All closed issues have release notes.") + "\n\n"
    #         release_notes += f"### Merged PRs without Linked Issue and Custom Labels ⚠️\n" + (sort_map_and_convert_to_string(merged_prs_without_link_to_issue) or "All merged PRs are linked to issues.") + "\n\n"
    #         release_notes += f"### Merged PRs Linked to Open Issue ⚠️\n" + (sort_map_and_convert_to_string(merged_prs_linked_to_open_issue) or "All merged PRs are linked to Closed issues.") + "\n\n"
    #         release_notes += f"### Closed PRs without Linked Issue and Custom Labels ⚠️\n" + (sort_map_and_convert_to_string(closed_prs_without_link_to_issue) or "All closed PRs are linked to issues.") + "\n\n"
    #
    #         release_notes += f"#### Full Changelog\n{changelog_url}"
    #         print('Release Notes:', release_notes)
    #
    # except Exception as error:
    #     if error.status == 404:
    #         print('Repository not found. Please check the owner and repository name.')
    #         raise error
    #     elif error.status == 401:
    #         print('Authentication failed. Please check your GitHub token.')
    #         raise error
    #     else:
    #         print(f"Error fetching data: {error}")
    #         raise error

if __name__ == '__main__':
    run()
