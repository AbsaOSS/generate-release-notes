# Generate Release Notes Action

This GitHub Action automatically generates release notes for a given release tag by categorizing contributions into user-defined chapters based on labels. It streamlines the process of documenting new features, bug fixes, and breaking changes in your project releases.

## Motivation

Generate Release Notes action is dedicated to enhance the quality and organization of project documentation. Its primary purpose is to categorize release notes according to various labels, perfectly aligning with the unique organizational needs of each project. In addition, it offers robust support for acknowledging the efforts of contributors, thereby fostering a sense of recognition and appreciation within the team. Another noteworthy feature of this tool is its capability to detect potential gaps in documentation, ensuring that release notes are comprehensive and leave no stone unturned. Well maintained release notes are a vital component in maintaining high-quality, meticulously organized documentation, which is indispensable in the development process. This repository reflects our commitment to excellence in project documentation and team collaboration.

## Usage

### Prerequisites

Before we begin, ensure you have a GitHub Token with permission to fetch repository data such as Issues and Pull Requests.

### Adding the Action to Your Workflow

Add the following step to your GitHub workflow (in example are used non-default values):

```yaml
- name: Generate Release Notes
  id: generate_release_notes
  uses: AbsaOSS/generate-release-notes@0.1.0
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
    warnings: false
    published-at: true
    skip-release-notes-label: 'ignore-in-release'     # changing default value of label
    print-empty-chapters: false
    chapters-to-pr-without-issue: true
```

### Configure the Action
Configure the action by customizing the following parameters based on your needs:

- **GITHUB_TOKEN** (required): Your GitHub token for authentication. Store it as a secret and reference it in the workflow file as secrets.GITHUB_TOKEN.
- **tag-name** (required): The name of the tag for which you want to generate release notes. This should be the same as the tag name used in the release workflow.
- **chapters** (required): A JSON string defining chapters and corresponding labels for categorization. Each chapter, like "Breaking Changes", "New Features", and "Bugfixes", should have a title and a label matching your GitHub issues and PRs.
- **warnings** (optional): Set to true to enable warnings in the release notes. These warnings identify issues without release notes, without user-defined labels, or without associated pull requests, and PRs without linked issues. Defaults to false if not specified.
- **published-at** (optional): Set to true to enable the use of the `published-at` timestamp as the reference point for searching closed issues and PRs, instead of the `created-at` date of the latest release.
- **skip-release-notes** (optional): Set to a label name to skip issues and PRs with this label from release notes process generation. Defaults to `skip-release-notes` if not specified.
- **print-empty-chapters** (optional): Set to true to print chapters with no issues or PRs. Defaults to false if not specified.
- **chapters-to-pr-without-issue** (optional): Set false to avoid application of custom chapters for PRs without linked issues. Defaults to true if not specified.

## Setup
### Build the Action:
If you need to build the action locally:

```bash
npm install
npm run build
```

Then, commit action.yml and dist/index.js to your repository.

### Run unit test
First install [jest](https://jestjs.io/) testing framework.
```
npm install --save-dev jest
npm install @actions/core
npm install @actions/github
```
Launch unit tests.
```
npm test
```

## Features
### Release Notes Extraction Process

This action requires that your GitHub issues include comments with specific release notes. Here's how it works:

#### Extraction Method
The action scans through comments on each closed issue since the last release. It identifies comments that follow the specified format and extracts the content as part of the release notes.

**Note**: The time considered for the previous release is based on its creation time. This means that the action will look for issues closed after the creation time of the most recent release to ensure that all relevant updates since that release are included.

#### Comment Format
For an issue's contributions to be included in the release notes, it must contain a comment starting with "Release Notes" followed by the note content. This comment is typically added by the contributors.

Here is an example of the content for a 'Release Notes' string, which is not case-sensitive:
```
Release Notes
- This update introduces a new caching mechanism that improves performance by 20%.
```
Using `-` as a bullet point for each note is the best practice. The Markdown parser will automatically convert it to a list.

These comments are not required for action functionality. If an issue does not contain a "Release Notes" comment, it will be marked accordingly in the release notes. This helps maintainers quickly identify which issues need attention for documentation.

### Contributors Mention
Along with the release note content, the action also gathers a list of contributors for each issue. This includes issue assignees and authors of linked pull requests' commits, providing acknowledgment for their contributions in the release notes.

### Handling Multiple PRs
If an issue is linked to multiple PRs, the action fetches and aggregates contributions from all linked PRs.

#### No Release Notes Found
If no valid "Release Notes" comment is found in an issue, it will be marked accordingly. This helps maintainers quickly identify which issues need attention for documentation.

#### Warnings
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


Each warning chapter acts as a quality check, ensuring that the release notes are comprehensive, well-organized, and meaningful. By addressing these warnings, project maintainers can significantly improve the clarity and effectiveness of their release documentation.


### Contribution Guidelines

We welcome contributions to the Generate Release Notes Action! Whether you're fixing bugs, improving documentation, or proposing new features, your help is appreciated.

#### How to Contribute
- **Submit Pull Requests**: Feel free to fork the repository, make changes, and submit a pull request. Please ensure your code adheres to the existing style and all tests pass.
- **Report Issues**: If you encounter any bugs or issues, please report them via the repository's [Issues page](https://github.com/AbsaOSS/generate-release-notes/issues).
- **Suggest Enhancements**: Have ideas on how to make this action better? Open an issue to suggest enhancements.

Before contributing, please review our [contribution guidelines](https://github.com/AbsaOSS/generate-release-notes/blob/master/CONTRIBUTING.md) for more detailed information.

### License Information

This project is licensed under the Apache License 2.0. It is a liberal license that allows you great freedom in using, modifying, and distributing this software, while also providing an express grant of patent rights from contributors to users.

For more details, see the [LICENSE](https://github.com/AbsaOSS/generate-release-notes/blob/master/LICENSE) file in the repository.

### Contact or Support Information

If you need help with using or contributing to Generate Release Notes Action, or if you have any questions or feedback, don't hesitate to reach out:

- **Issue Tracker**: For technical issues or feature requests, use the [GitHub Issues page](https://github.com/AbsaOSS/generate-release-notes/issues).
- **Discussion Forum**: For general questions and discussions, join our [GitHub Discussions forum](https://github.com/AbsaOSS/generate-release-notes/discussions).

### FAQs
#### Why is in generated Release Notes content mentioned co-author without link to his GitHub account?
Co-authors can be added into a commit message by using the `Co-authored-by` trailer in the commit message. This trailer is used by GitHub to link the commit to the co-author's GitHub account. The co-author's name is mentioned in the generated Release Notes without a link to his GitHub account.
```
Co-authored-by: NAME <NAME@EXAMPLE.COM>
```
The Release Notes generator is trying to get Github user by call GitHub API with the co-author's email address. If the user is found, the generator will use the user's name and link to his GitHub account. If the user is not found, the generator will use the co-author's name without a link to his GitHub account.
This leads to the situation when the co-author's name is mentioned in the generated Release Notes without a link to his GitHub account.

#### Will the action provide duplicate line in chapters if the issue contains multiple labels?
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

#### What will happen when the issue contains multiple "Release Notes" comments?
All issue comments are checked for presence of `Release Notes` string. All detected release notes are collected printed under issue.

#### What will happen when Merged PR is linked to open issues?
The PR will be mentioned in warning chapter **Merged PRs Linked to Open Issue**.