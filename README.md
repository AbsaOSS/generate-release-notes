# Generate Release Notes Action

- [Motivation](#motivation)
- [Requirements](#requirements)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Usage Example](#usage-example)
- [Features](#features)
  - [Built-in](#built-in)
    - [Release Notes Extraction Process](#release-notes-extraction-process)
    - [Contributors Mention](#contributors-mention)
    - [Handling Multiple PRs](#handling-multiple-prs)
    - [No Release Notes Found](#no-release-notes-found)
  - [Select start date for closed issues and PRs](#select-start-date-for-closed-issues-and-prs)
  - [Enable skipping of release notes for specific issues using label](#enable-skipping-of-release-notes-for-specific-issues-using-label)
  - [Enable Service Chapters](#enable-service-chapters)
  - [Showing Duplicity Lines In Chapters](#showing-duplicity-lines-in-chapters)
  - [Define "From Tag" Name](#define-from-tag-name)
- [Developer Guide](#developer-guide)
- [GitHub Workflow Examples](#github-workflow-examples)
  - [Create Release Tag & Draft Release - By Workflow Dispatch](#create-release-tag--draft-release---by-workflow-dispatch)
  - [Check Release Notes Presence - in Pull Request Description](#check-release-notes-presence---in-pull-request-description)
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

| Name           | Description                                                                                                                 | Required | Default                                 |
|----------------|-----------------------------------------------------------------------------------------------------------------------------|----------|-----------------------------------------|
| `GITHUB_TOKEN` | Your GitHub token for authentication. Store it as a secret and reference it in the workflow file as secrets.GITHUB_TOKEN.   | Yes      |                                         |
| `tag-name`     | The name of the tag for which you want to generate release notes. This should be the same as the tag name used in the release workflow. | Yes      |                                         | 
| `from-tag-name` | The name of the tag from which you want to generate release notes. | No | ''                                      |
| `chapters` | An YAML array defining chapters and corresponding labels for categorization. Each chapter should have a title and a label matching your GitHub issues and PRs. | Yes |                                         | 
| `row-format-issue` | The format of the row for the issue in the release notes. The format can contain placeholders for the issue `number`, `title`, and issues `pull-requests`. The placeholders are case-sensitive. | No | `"{number} _{title}_ in {pull-requests}"` |  
| `row-format-pr` | The format of the row for the PR in the release notes. The format can contain placeholders for the PR `number`, and `title`. The placeholders are case-sensitive. | No | `"{number} _{title}_"`                  |  
| `row-format-link-pr` | If defined `true`, the PR row will begin with a `"PR: "` string. Otherwise, no prefix will be added. | No | true                                    | 
| `duplicity-scope` | Set to `custom` to allow duplicity issue lines to be shown only in custom chapters. Options: `custom`, `service`, `both`, `none`. | No | `both`                                  |  
| `duplicity-icon` | The icon used to indicate duplicity issue lines in the release notes. Icon will be placed at the beginning of the line. | No | `🔔` |  
| `published-at` | Set to true to enable the use of the `published-at` timestamp as the reference point for searching closed issues and PRs, instead of the `created-at` date of the latest release. If first release, repository creation date is used.  | No | false |
| `skip-release-notes-labels` | List labels used for detection if issues or pull requests are ignored in the Release Notes generation process. Example: `skip-release-notes, question`. | No  | `skip-release-notes` | 
| `verbose` | Set to true to enable verbose logging for detailed output during the action's execution. | No | false |
| `release-notes-title` | The title of the release notes section in the PR description. | No | `[Rr]elease [Nn]otes:` |
| `coderabbit-support-active` | Set to true to enable CodeRabbit support for generating release notes. | No | false |
| `coderabbit-release-notes-title` | The CodeRabbit's summary section title in the PR description. | No | `Summary by CodeRabbit` |
| `coderabbit-summary-ignore-groups` | List of "group names" to be ignored by release notes detection logic. Example: `Documentation, Tests, Chores, Bug Fixes`. | No | '' |

> **Notes**
> - `skip-release-notes-labels`
>  - If used on issue then Issue will be skipped during Release Notes generation.
>  - If used on PR with issue then on PR it will be ignored and PR will show as part of issue's release notes.
>  - If used on PR without issue then PR will be skipped during Release Notes generation.
> - `verbose`
>   - If workflow run in debug regime, 'verbose' logging is activated.

### Feature controls

| Name           | Description                                                                                                                 | Required | Default                              |
|----------------|-----------------------------------------------------------------------------------------------------------------------------|----------|--------------------------------------|
| `warnings` | Set to true to print service chapters in the release notes. These warnings identify issues without release notes, without user-defined labels, or without associated pull requests, and PRs without linked issues. | No       | true (Service chapters are printed.) |  
| `print-empty-chapters` | Set it to true to print chapters with no issues or PRs. | No       | true (Empty chapters are printed.) | 

## Outputs
The output of the action is a markdown string containing the release notes for the specified tag. This string can be used in subsequent steps to publish the release notes to a file, create a GitHub release, or send notifications.

See the [example of output](./examples/output_example.md).

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
    tag-name: "v0.2.0"
    from-tag-name: "v0.1.0"
    chapters: |
      - {"title": "Breaking Changes 💥", "label": "breaking-change"}
      - {"title": "New Features 🎉", "label": "enhancement"}
      - {"title": "New Features 🎉", "label": "feature"}
      - {"title": "Bugfixes 🛠", "label": "bug"}
```

#### Full example
```yaml
- name: Generate Release Notes
  id: release_notes_generator
  uses: AbsaOSS/generate-release-notes@v0.2.0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  
  with:
    tag-name: "v0.2.0"
    from-tag-name: "v0.1.0"
    chapters: |
      - {"title": "Breaking Changes 💥", "label": "breaking-change"}
      - {"title": "New Features 🎉", "label": "enhancement"}
      - {"title": "New Features 🎉", "label": "feature"}
      - {"title": "Bugfixes 🛠", "label": "bug"}

    duplicity-scope: 'service'
    duplicity-icon: '🔁'
    published-at: true
    skip-release-notes-labels: 'ignore-in-release'     # changing default value of label
    verbose: false
    release-notes-title: '[Rr]elease Notes:'

    coderabbit-support-active: 'true'
    coderabbit-release-notes-title: 'Summary by CodeRabbit'
    coderabbit-summary-ignore-groups: 'Documentation,Tests,Chores,Bug Fixes,Refactor'

    warnings: false
    print-empty-chapters: false
```

## Features
### Built-in
#### Release Notes Extraction Process

This feature automatically extracts release notes from GitHub pull request descriptions to help maintainers track meaningful changes.

##### 🔍 How Detection Works

- The Action looks for a specific section in the PR body, defined by:
  - `release-notes-title`: A regex pattern to match the release notes section header.
  - `coderabbit-support-active`: Enables fallback support for CodeRabbit summaries.
    - ✅ _Used only if no section matching `release-notes-title` is found._

##### 📏 Detection Rules
- The release notes section:
  - Can be **anywhere in the PR body**
  - Must begin with a header that matches either:
    - `release-notes-title`
    - OR `coderabbit-release-notes-title` (when CodeRabbit support is active)
  - Supports [Markdown formatting](https://www.markdownguide.org/basic-syntax/#unordered-lists)
  - Only the **first matching section** is extracted
  - Is **optional** – the Action will still proceed even if no notes are found
  - Will be **skipped silently** if the PR has a label listed in `skip-release-notes-labels`

> 🔕 If no valid section is found, the output Release Notes record will not contain any release notes.

- **Example:** 
  - Here are examples of how to structure the release notes:
```
## Release Notes:
- This update introduces a new caching mechanism that improves performance by 20%.
  - The caching mechanism reduces database queries.
    - Optimized for high-traffic scenarios.
  - Includes support for distributed caching.
  
## Release Notes:
* This update introduces a new caching mechanism that improves performance by 20%.
  * Affected only specific edge cases.
  
## Release Notes:
+ This update introduces a new caching mechanism that improves performance by 20%.

## Summary by CodeRabbit

- **New Features**
  - Introduced a new feature.
  
- **Documentation**
  - Added new descriptions.

- **Chores**
  - Added configuration files for code style.

- **Tests**
  - Introduced a complete test suite for all classes.
```
> The extraction process supports all three types of bullet points: `-`, `*`, and `+`, and their combinations. (GitHub documentation do not recommend to mix them.)
> 
> **Best Practice:** Select one character from `-`, `*`, `+` for bullet points. The Markdown parser will automatically format them as a list.

#### Handling Multiple PRs
If an issue is linked to multiple PRs, the action fetches and aggregates contributions from all linked PRs.

### Select start date for closed issues and PRs
By set **published-at** to true the action will use the `published-at` timestamp of the latest release as the reference point for searching closed issues and PRs, instead of the `created-at` date. If first release, repository creation date is used. 

### Enable skipping of release notes for specific issues using label
By defining the `skip-release-notes-labels` option, the action will skip all issues and related PRs if they contain a label defined in configuration. This is useful for issues that are not relevant for release notes.

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
  - **Purpose**: Identifies pull requests which do not contain a "Release Notes" section in description.
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

### Define "From Tag" Name
By setting the `from-tag-name` option, the action will generate release notes from the specified tag to the tag defined in the `tag-name` option. This feature is helpful for generating release notes for a specific range of tags.

The final interval is time-based. The `published-at` or `created-at` timestamp of the previous release or repository creation date, if it is the first release, is used as the starting point. The previous release is determined to be the previous semantic version tag.

## Developer Guide

See this [Developer Guide](DEVELOPER.md) for more technical, development-related information.

## GitHub Workflow Examples
GitHub Actions enable automating key parts of your development process.

### Create Release Tag & Draft Release - By Workflow Dispatch
This workflow automates the creation of a release tag and a draft release, triggered manually via a workflow dispatch.
Tag is created after successful release notes generation to avoid manual removing of the tag if the release notes are not generated due to wrong configuration.

See the [example of workflow](./examples/release_draft.yml).

#### Impact to Users
The users can trigger the workflow manually by clicking the "Run workflow" button in the Actions tab. The workflow will create a release tag and a draft release based on the release notes generated by the action.

This workflow replaces the manual process of creating a release tag and draft release, saving time and ensuring consistency in the release process.

### Check Release Notes Presence - in Pull Request Description 
This workflow checks that every pull request includes release notes in the description.

See the [example of workflow](./examples/check_pr_release_notes.yml).

#### Impact to Users
The users are expected to provide the release notes in the pull request body. See example:
```markdown
Release Notes:                          .... also valid: ## Release Notes:
- 1st line of PR's release notes
- 2nd line of PR's release notes
```

This section can be placed anywhere in the pull request body. The action will search for the release notes based on the provided title text. _Hint:_ The title can be chapter name, the Markdown format tags are ignored.

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

### What will happen when the pull request contains multiple "Release Notes" sections?
Only the first one will be used.

### What will happen when Merged PR is linked to open issues?
The PR will be mentioned in warning chapter **Merged PRs Linked to Open Issue**.
