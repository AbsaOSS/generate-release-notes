# Generate Release Notes Action

- [Motivation](#motivation)
- [Requirements](#requirements)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Usage Example](#usage-example)
- [Features](#features)
  - [Built-in](#built-in)
    - [Release Notes Support](#release-notes-support)
      - [Handling Issue Mentioned By Multiple PRs](#handling-issue-mentioned-by-multiple-prs)
      - [No Release Notes Found](#no-release-notes-found)
      - [Issue, Pull Request or Commit Row formatting](#issue-pull-request-or-commit-row-formatting)
        - [Supported row format keywords](#supported-row-format-keywords)
    - [Contributors Mention](#contributors-mention)
    - [Handling Issue Mentioned By Multiple PRs](#handling-issue-mentioned-by-multiple-prs)
    - [No Release Notes Found](#no-release-notes-found)
  - [Select start date for closed issues and PRs](#select-start-date-for-closed-issues-and-prs)
  - [Enable skipping of release notes for specific issues using label](#enable-skipping-of-release-notes-for-specific-issues-using-label)
  - [Enable Service Chapters](#enable-service-chapters)
  - [Showing Duplicity Lines In Chapters](#showing-duplicity-lines-in-chapters)
- [Get Started](#get-started)
- [Run Static Code Analysis](#running-static-code-analysis)
- [Run Black Tool Locally](#run-black-tool-locally)
- [Run Unit Test](#running-unit-test)
- [Run Action Locally](#run-action-locally)
- [Contribution Guidelines](#contribution-guidelines)
  - [How to Contribute](#how-to-contribute)
- [License Information](#license-information)
- [Contact or Support Information](#contact-or-support-information)
- [FAQs](#faqs)

## Description

This GitHub Action automatically generates release notes for a given release tag by categorizing contributions into user-defined chapters based on labels. It streamlines the process of documenting new features, bug fixes, and breaking changes in your project releases.

## Motivation

Generate Release Notes action is dedicated to enhance the quality and organization of project documentation. Its primary purpose is to categorize release notes according to various labels, perfectly aligning with the unique organizational needs of each project. In addition, it offers robust support for acknowledging the efforts of contributors, thereby fostering a sense of recognition and appreciation within the team. Another noteworthy feature of this tool is its capability to detect potential gaps in documentation, ensuring that release notes are comprehensive and leave no stone unturned. Well maintained release notes are a vital component in maintaining high-quality, meticulously organized documentation, which is indispensable in the development process. This repository reflects our commitment to excellence in project documentation and team collaboration.

## Requirements
- **GitHub Token**: A GitHub token with permission to fetch repository data such as Issues and Pull Requests.
- **Python 3.11+**: Ensure you have Python 3.11 installed on your system.

## Inputs
### `GITHUB_TOKEN`
- **Description**: Your GitHub token for authentication. Store it as a secret and reference it in the workflow file as secrets.GITHUB_TOKEN.
- **Required**: Yes

### `tag-name`
- **Description**: The name of the tag for which you want to generate release notes. This should be the same as the tag name used in the release workflow.
- **Required**: Yes

### `chapters`
- **Description**: A JSON string defining chapters and corresponding labels for categorization. Each chapter should have a title and a label matching your GitHub issues and PRs.
- **Required**: Yes

### `row-format-issue`
- **Description**: The format of the row for the issue in the release notes. The format can contain placeholders for the issue `number`, `title`, and issues `pull-requests`. The placeholders are case-sensitive.
- **Required**: No
- **Default**: `#{number} _{title}_ {pull-requests} {assignee} {implemented-by} {contributed-by}"`

### `row-format-pr`
- **Description**: The format of the row for the PR in the release notes. The format can contain placeholders for the PR `number`, `title`, and PR `pull-requests`. The placeholders are case-sensitive.
- **Required**: No
- **Default**: `#{number} _{title}_ {assignee} {implemented-by} {contributed-by}`

### `row-format-link-pr`
- **Description**: If defined `true`, the PR row will begin with a `"PR: "` string. Otherwise, no prefix will be added.
- **Required**: No
- **Default**: true

### `duplicity-scope`
- **Description**: Set to `custom` to allow duplicity issue lines to be shown only in custom chapters. Options: `custom`, `service`, `both`, `none`.
- **Required**: No
- **Default**: `both`

### `duplicity-icon`
- **Description**: The icon used to indicate duplicity issue lines in the release notes. Icon will be placed at the beginning of the line.
- **Required**: No
- **Default**: `🔔`

### `published-at`
- **Description**: Set to true to enable the use of the `published-at` timestamp as the reference point for searching closed issues and PRs, instead of the `created-at` date of the latest release. If first release, repository creation date is used.
- **Required**: No
- **Default**: false

### `skip-release-notes-label`
- **Description**: Set to a label name to skip issues and PRs with this label from the release notes process generation.
- **Required**: No
- **Default**: `skip-release-notes`

### `verbose`
- **Description**: Set to true to enable verbose logging for detailed output during the action's execution.
- **Required**: No
- **Default**: false
- **Note**: If workflow run in debug regime, 'verbose' logging is activated.

### Feature controls

### `warnings`
- **Description**: Set to true to print service chapters in the release notes. These warnings identify issues without release notes, without user-defined labels, or without associated pull requests, and PRs without linked issues.
- **Required**: No
- **Default**: true (Service chapters are printed.)

### `print-empty-chapters`
- **Description**: Set it to true to print chapters with no issues or PRs.
- **Required**: No
- **Default**: true (Empty chapters are printed.)


## Outputs
The output of the action is a markdown string containing the release notes for the specified tag. This string can be used in subsequent steps to publish the release notes to a file, create a GitHub release, or send notifications.

See the [example of output](./examples/output_example.md).

### Supported Row Types
#### Issue Row
An issue row may have multiple pull requests linked to it. These pull requests are associated using GitHub-supported keywords like closes, fixes, or resolves.

**Example**
- #33 _Example bugfix_ in [#44](https://github.com/absa-group/living-doc-example-project/pull/44), [#36](https://github.com/absa-group/living-doc-example-project/pull/36), [#35](https://github.com/absa-group/living-doc-example-project/pull/35), [#34](https://github.com/absa-group/living-doc-example-project/pull/34) assigned to @miroslavpojer developed by @miroslavpojer co-authored by Saša Zejnilović <zejnils@gmail.com>
  - Another solved typos. Hello from second RLS notes comment.
  - Solved some typos.

#### Pull Request Row
A pull request row represents one PR made against the repository. This pull request does not mention any issues.

**Example**
- PR: #41 _Initial commit._ assigned to @miroslavpojer developed by @miroslavpojer
  - Test release notes nr1
  - Test release notes nr2

#### Direct Commit Row
A direct commit row represents a commit that is not tied to any pull request or issue. This commit is not associated with any pull request.

**Example**
- Commit: fbe8e558f914cd58d8e7aab8c7d0c77f934aa707 developed by @miroslavpojer

## Usage Example

### Prerequisites

Before we begin, ensure you have a GitHub Token with permission to fetch repository data such as Issues and Pull Requests.

### Adding the Action to Your Workflow

Add the following step to your GitHub workflow (in example are used non-default values):

#### Default
```yaml
- name: Generate Release Notes
  id: release_notes_generator
  uses: AbsaOSS/generate-release-notes@v0.2.0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  
  with:
    tag-name: "v0.1.0"
    chapters: '[
      {"title": "Breaking Changes 💥", "label": "breaking-change"},
      {"title": "New Features 🎉", "label": "enhancement"},
      {"title": "New Features 🎉", "label": "feature"},
      {"title": "Bugfixes 🛠", "label": "bug"}
    ]'
```

#### Full example
```yaml
- name: Generate Release Notes
  id: release_notes_generator
  uses: AbsaOSS/generate-release-notes@v0.2.0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  
  with:
    tag-name: "v0.1.0"
    chapters: '[
      {"title": "Breaking Changes 💥", "label": "breaking-change"},
      {"title": "New Features 🎉", "label": "enhancement"},
      {"title": "New Features 🎉", "label": "feature"},
      {"title": "Bugfixes 🛠", "label": "bug"}
    ]'
    duplicity-scope: 'service'
    duplicity-icon: '🔁'
    published-at: true
    skip-release-notes-label: 'ignore-in-release'     # changing default value of label
    verbose: false

    warnings: false
    print-empty-chapters: false
    row-format-issue: '#{number} _{title}_ {pull-requests} {assignee} {developed-by} {co-authored-by}'
    row-format-pr: '#{number} _{title}_ {assignee} {developed-by} {co-authored-by}'
    row-format-link-pr: true
```

## Features
### Built-in
#### Release Notes Support
This action enables GitHub pull requests to include a dedicated section for release notes in its description, making it easier for maintainers to track changes and updates.

- **Format:** The section must begin with the title `Release Notes:`, followed by the release notes in bullet points.
- **Example:** Here is an example of how to structure the release notes (case-sensitive):
```
Release Notes:
- This update introduces a new caching mechanism that improves performance by 20%.
```
- **Best Practice:** Use `-` for bullet points. The Markdown parser will automatically format them as a list.
- **Optional:** Including release notes is not mandatory for the action of this GH action.

The action scans pull request descriptions for the `Release Notes:` section and extracts any content that follows the specified format.

#### Handling Issue Mentioned By Multiple PRs
If an issue is linked from multiple PRs, the action fetches and aggregates developers and contributions from all linked PRs.

#### No Release Notes Found
If no valid `Release Notes:` section is found in a pull request description, it will be mentioned in dedicated service chapters. This helps maintainers quickly identify which pull request need attention for documentation.

#### Issue, Pull Request or Commit Row formatting
Format of the different row types can be customized. The placeholders are case-sensitive. Each row type supports different set of keywords.

##### Supported row format keywords
- **Issue & Pull Request**
  - `{number}`: 
    - Issue or PR number.
  - `{title}`: 
    - Issue or PR title.
  - `{pull-requests}`: 
    - List of PRs linked to the issue. Adds a list of PRs linked to the issue in the row with `in` prefix:
      - _Example:_ `#{number} _{title}_ {pull-requests}` => "[#43]() _title_ in [#PR1](), [#PR2](), [#PR3]()"
    - Not used in PR row format. Pull Request type already define single PR.
  - `{assingee}`: 
    - Issue or PR assignee. Adds a login of assignees in the row with `assigned to` prefix:
      - `#{number} _{title}_ {assignee}` => "[#43]() _title_ implemented by @login1"
  - `{assignees}`: 
    - Issue or PR assignees. Adds a list of assignees logins in the row with `assigned to` prefix:
      - `#{number} _{title}_ {assignees}` => "[#43]() _title_ implemented by @login1, @login2"
    - This is alternative representation of multiple assignees provided by GitHub.
  - `{developed-by}`: 
    - List of PR developer(s) login(s). Adds a login of commit authors for PR(s) in the row with `developed by` prefix:
      - `#{number} _{title}_ {developed-by}` => "[#43]() _title_ developed by @login1"
  - `{co-authored-by}`: 
    - List of PR contributors. Adds a login of contributors in the row with `co-authored by` prefix:
      - `#{number} _{title}_ {co-authored-by}` => "[#43]() _title_ co-authored by @login1 @login2"
    - Co-authors are detected in PR commit messages by detection of GitHub supported trailer `Co-authored-by`.
- **Commit**
  - `{sha}`: 
    - Commit SHA.
  - `{author}`: 
    - Commit author login.
  - `{co-authors}`: 
    - List of commit contributors. Co-authors are detected in commit messages by detection of GitHub supported trailer `Co-authored-by`.

### Select start date for closed issues and PRs
By set **published-at** to true the action will use the `published-at` timestamp of the latest release as the reference point for searching closed issues and PRs, instead of the `created-at` date. If first release, repository creation date is used. 

### Enable skipping of release notes for specific issues using label
By set **skip-release-notes-label** to true the action will skip all issues and related PRs if they contain a label defined in configuration. This is useful for issues that are not relevant for release notes.

### Enable Service Chapters
If the `warnings` option is enabled in the action's configuration, the release notes will include sections that highlight possible issues.

The action includes four specific warning chapters to highlight potential areas of improvement in release documentation. Each chapter serves a distinct purpose:

- **_Closed Issues Without Pull Request_**
  - **Purpose**: This chapter lists issues that have been closed since the last release but are not linked to any pull requests.
  - **Importance**: Helps maintainers identify changes that might not have been properly reviewed or documented through PRs, ensuring the integrity of the release documentation.

- **_Closed Issues Without User-Defined Labels_**
  - **Purpose**: Displays issues lacking the labels defined in the `chapters` configuration.
  - **Importance**: Ensures all issues are categorized correctly according to the project's classification system. It aids in organizing release notes into predefined chapters effectively.

- **_Closed Issues Without Release Notes_**
  - **Purpose**: Identifies issues that do not contain a "Release Notes" comment.
  - **Importance**: Ensures that all significant changes are properly documented in the release notes, enhancing the completeness and usefulness of the release information provided to end-users.

- **_Merged PRs Without Linked Issue_**
  - **Purpose**: Lists pull requests that are not associated with any issues.
  - **Importance**: Encourages linking PRs to issues for better traceability and understanding of why changes were made. It also helps in maintaining a cohesive narrative in the project history and release notes.

- **_Merged PRs Linked to Open Issue_**
  - **Purpose**: This section identifies merged pull requests that are still linked to issues which are open.
  - **Importance**: Highlighting these PRs indicates potential discrepancies or ongoing work related to the PR. It helps in ensuring that all issues addressed by PRs are properly closed and documented, maintaining the accuracy and relevance of the project's issue tracking.

- **_Closed PRs Without Linked Issue_**
  - **Purpose**: Lists pull requests that are closed (not merged) but not associated with any issues.
  - **Importance**: Highlighting closed PRs without linked issues ensures transparency in the project's history. It helps track important decisions and clarifies the reasoning behind changes, even if they aren't merged. This practice enhances the project's documentation quality and aids in understanding its evolution.

- **_Others - No Topic_**
  - **Purpose**: This chapter lists issues that do not fall into any of the predefined chapters.
  - **Importance**: Helps maintainers identify issues that may not have been categorized correctly. This ensures that all issues are properly documented and organized in the release notes.

Each warning chapter acts as a quality check, ensuring that the release notes are comprehensive, well-organized, and meaningful. By addressing these warnings, project maintainers can significantly improve the clarity and effectiveness of their release documentation.


### Showing Duplicity Lines In Chapters
By setting the `duplicity-scope` with one of the options, the action will show whether the duplicity issue lines are correct.
- `custom`: will show duplicity lines only in custom chapters.
- `service`: will show duplicity lines only in service chapters.
- `both`: will show duplicity lines in both custom and service chapters.
- `none`: will hide duplicity lines in all chapters.

Duplicity lines in `custom` chapters can point to potential issues with wrong labeling. In contrast, duplicity lines in `service` chapters can help maintainers identify areas with the most significant problems to address.

By setting `duplicity-icon` you can customize the icon used to indicate duplicity issue lines in the release notes. Icon will be placed at the beginning of the line. The duplicity icon is visible from **second** occurrence of the issue in the selected scope.

## Get Started

Clone the repository and navigate to the project directory:

```
git clone https://github.com/AbsaOSS/generate-release-notes.git
cd generate-release-notes
```

Install the dependencies:

```
pip install -r requirements.txt
export PYTHONPATH=<your path>/generate-release-notes/src
```

## Running Static Code Analysis

This project uses Pylint tool for static code analysis. Pylint analyses your code without actually running it. It checks for errors, enforces, coding standards, looks for code smells etc.

Pylint displays a global evaluation score for the code, rated out of a maximum score of 10.0. We are aiming to keep our code quality high above the score 9.5.

### Set Up Python Environment
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run your commands

deactivate
```

This command will also install a Pylint tool, since it is listed in the project requirements.

### Run Pylint
Run Pylint on all files that are currently tracked by Git in the project.
```
pylint $(git ls-files '*.py')
```

To run Pylint on a specific file, follow the pattern `pylint <path_to_file>/<name_of_file>.py`.

Example:
```
pylint release-notes-generator/generator.py
``` 

## Run Black Tool Locally
This project uses the [Black](https://github.com/psf/black) tool for code formatting.
Black aims for consistency, generality, readability and reducing git diffs.
The coding style used can be viewed as a strict subset of PEP 8.

The project root file `pyproject.toml` defines the Black tool configuration.
In this project we are accepting the line length of 120 characters.

Follow these steps to format your code with Black locally:

### Set Up Python Environment
From terminal in the root of the project, run the following command:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This command will also install a Black tool, since it is listed in the project requirements.

### Run Black
Run Black on all files that are currently tracked by Git in the project.
```shell
black $(git ls-files '*.py')
```

To run Black on a specific file, follow the pattern `black <path_to_file>/<name_of_file>.py`.

Example:
```shell
black release_notes_generator/generator.py
``` 

### Expected Output
This is the console expected output example after running the tool:
```
All done! ✨ 🍰 ✨
1 file reformatted.
```


## Running Unit Test

Unit tests are written using pytest. To run the tests, use the following command:

```
pytest tests/
```

This will execute all tests located in the tests directory and generate a code coverage report.

TODO: add another example for partial run
pytest tests/release_notes_generator/utils/test_utils.py

debug only - how to run measuremnt on isolated test set
pytest --cov=. tests/release_notes_generator/utils/test_utils.py --cov-fail-under=80 --cov-report=html

## Code Coverage

Code coverage is collected using pytest-cov coverage tool. To run the tests and collect coverage information, use the following command:

```
pytest --cov=release_notes_generator --cov-report html tests/
```



See the coverage report on the path:

```
htmlcov/index.html
```

## Run Action Locally
Create *.sh file and place it in the project root.

```bash
#!/bin/bash

# Set environment variables based on the action inputs
export INPUT_TAG_NAME="v0.2.0"
export INPUT_CHAPTERS='[
  {"title": "Breaking Changes 💥", "label": "breaking-change"},
  {"title": "New Features 🎉", "label": "enhancement"},
  {"title": "New Features 🎉", "label": "feature"},
  {"title": "Bugfixes 🛠", "label": "bug"}
]'
export INPUT_WARNINGS="true"
export INPUT_PUBLISHED_AT="true"
export INPUT_SKIP_RELEASE_NOTES_LABEL="ignore-in-release"
export INPUT_PRINT_EMPTY_CHAPTERS="true"
export INPUT_VERBOSE="true"

# CI in-build variables
export GITHUB_REPOSITORY="< owner >/< repo-name >"
export INPUT_GITHUB_TOKEN=$(printenv <your-env-token-var>)

# Run the Python script
python3 ./<path-to-action-project-root>/main.py
```

## GitHub Workflow Examples
GitHub Actions enable automating key parts of your development process.

### Create Release Tag & Draft Release - By Workflow Dispatch
This workflow automates the creation of a release tag and a draft release, triggered manually via a workflow dispatch.
Tag is created after successful release notes generation to avoid manual removing of the tag if the release notes are not generated due to wrong configuration.

See the [example of workflow](./examples/release_draft.yml).

### Check Release Notes Presence - in Pull Request Description 
This workflow checks that every pull request includes release notes in the description.
- The check can be skipped by using the `skip-release-notes` label.
- The check is searching a `[Rr]elease [Nn]otes:` strings in the PR description.

See the [example of workflow](./examples/check_pr_release_notes.yml).

## Contribution Guidelines

We welcome contributions to the Generate Release Notes Action! Whether you're fixing bugs, improving documentation, or proposing new features, your help is appreciated.

### How to Contribute
- **Submit Pull Requests**: Feel free to fork the repository, make changes, and submit a pull request. Please ensure your code adheres to the existing style and all tests pass.
- **Report Issues**: If you encounter any bugs or issues, please report them via the repository's [Issues page](https://github.com/AbsaOSS/generate-release-notes/issues).
- **Suggest Enhancements**: Have ideas on how to make this action better? Open an issue to suggest enhancements.

Before contributing, please review our [contribution guidelines](https://github.com/AbsaOSS/generate-release-notes/blob/master/CONTRIBUTING.md) for more detailed information.

## License Information

This project is licensed under the Apache License 2.0. It is a liberal license that allows you great freedom in using, modifying, and distributing this software, while also providing an express grant of patent rights from contributors to users.

For more details, see the [LICENSE](https://github.com/AbsaOSS/generate-release-notes/blob/master/LICENSE) file in the repository.

## Contact or Support Information

If you need help with using or contributing to Generate Release Notes Action, or if you have any questions or feedback, don't hesitate to reach out:

- **Issue Tracker**: For technical issues or feature requests, use the [GitHub Issues page](https://github.com/AbsaOSS/generate-release-notes/issues).
- **Discussion Forum**: For general questions and discussions, join our [GitHub Discussions forum](https://github.com/AbsaOSS/generate-release-notes/discussions).

## FAQs
### Why is in generated Release Notes content mentioned co-author without link to his GitHub account?
Co-authors can be added into a commit message by using the `Co-authored-by` trailer in the commit message. This trailer is used by GitHub to link the commit to the co-author's GitHub account. The co-author's name is mentioned in the generated Release Notes without a link to his GitHub account.
```
Co-authored-by: NAME <NAME@EXAMPLE.COM>
```
The Release Notes generator is trying to get Github user by call GitHub API with the co-author's email address. If the user is found, the generator will use the user's name and link to his GitHub account. If the user is not found, the generator will use the co-author's name without a link to his GitHub account.
This leads to the situation when the co-author's name is mentioned in the generated Release Notes without a link to his GitHub account.

### Will the action provide duplicate line in chapters if the issue contains multiple labels?
Let's imagine that we have an issue which has three labels: `enhancement`, `feature`, `bug`.
We defined chapters for our GH actions this way:
```
    chapters: '[
      {"title": "Breaking Changes 💥", "label": "breaking-change"},
      {"title": "New Features 🎉", "label": "enhancement"},
      {"title": "New Features 🎉", "label": "feature"},
      {"title": "Bugfixes 🛠", "label": "bug"}
    ]'
```
Then in chapters `New Features 🎉` and `Bugfixes 🛠` will be duplicated lines for this issue. When mentioned second+ times then **[Duplicate]** prefix will be visible.
In the `New Features 🎉` chapter will be mentioned this issue once only.

### What will happen when the issue contains multiple "Release Notes" comments?
All issue comments are checked for presence of `Release Notes` string. All detected release notes are collected printed under issue.

### What will happen when Merged PR is linked to open issues?
The PR will be mentioned in warning chapter **Merged PRs Linked to Open Issue**.
