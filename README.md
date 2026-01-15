# Release Notes Scrapper Action

Automatically generate **structured release notes** directly from your GitHub issues and pull requests.  
Categorize changes, highlight contributors, and maintain consistent release documentation — all fully automated.

[![Version](https://img.shields.io/github/v/release/AbsaOSS/generate-release-notes)](https://github.com/AbsaOSS/generate-release-notes/releases)
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Release%20Notes%20Scrapper-blue)](https://github.com/marketplace/actions/release-notes-scrapper)

- [Overview](#overview)
- [Motivation](#motivation)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Example Workflow](#example-workflow)
- [Feature Tutorials](#feature-tutorials)
- [Troubleshooting](#troubleshooting)
- [Developer & Contribution Guide](#developer--contribution-guide)
- [License & Support](#license--support)

## Overview

**Release Notes Scrapper Action** scans issues, pull requests, and commits to create categorized release notes for your project releases.  
It groups changes by labels (e.g., “Bugfixes 🛠”, “New Features 🎉”) and extracts relevant content from PR descriptions or CodeRabbit summaries.

### Key Benefits
- Fully automated release note generation
- Categorization by labels or issue hierarchy
- Built-in “Service Chapters” to detect missing or incomplete release notes
- Configurable templates and icons
- Smart duplicate detection

## Motivation

Good documentation isn’t optional — it’s your project’s memory.  
This Action was created to make structured release documentation effortless and consistent across teams.

👉 For the full background and design principles, see [docs/motivation.md](/docs/motivation.md)

## Quick Start

Add the following step to your workflow to start generating release notes.

```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v1.2.0"
    chapters: |
      - {"title": "Breaking Changes 💥", "label": "breaking-change"}          # legacy single-label form
      - {"title": "New Features 🎉", "labels": "feature, enhancement"}        # multi-label form (comma separated)
      - {"title": "Bugfixes 🛠", "labels": ["bug", "error"]}                  # multi-label form (YAML list)
```

**Example output snippet:**

```markdown
### New Features 🎉
- #23 _Feature title_ author is @root assigned to @neo developed by @morpheus in #24
  - Added support for multi-factor authentication.

### Bugfixes 🛠
- PR: #25 _Copy not allowed_ author is @dependabot[bot] assigned to @smith developed by @smith
  - File copy operation has been implemented.

#### Full Changelog
https://github.com/org/repo/compare/v1.1.0...v1.2.0
```

**That’s it** — the Action will:

1. Fetch all closed issues and PRs from latest till now.
2. Categorize them by labels.
3. Extract release note text and contributors.
4. Output a Markdown section ready for publishing.

## Requirements

To run this action successfully, make sure your environment meets the following requirements:

| Requirement                | Description                                                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| **GitHub Token**           | A GitHub token with permission to read issues, pull requests, and releases. Usually available as `${{ secrets.GITHUB_TOKEN }}`. |
| **Python 3.11+**           | The action internally runs on Python 3.11 or higher. If you’re developing locally or testing, ensure this version is available. |
| **Repository Permissions** | The action needs at least `read` access to issues and pull requests, and `write` access to create or update release drafts.     |
| **YAML Chapters Config**   | Each chapter must have a `title`, and a `label` or `labels`. Example: `{"title": "Bugfixes 🛠", "labels": "bug, fix"}`.         |

## Configuration

Only a few inputs are required to get started:

| Name           | Description                                                                  | Required | Default |
|----------------|------------------------------------------------------------------------------|----------|---------|
| `GITHUB_TOKEN` | GitHub token for authentication                                              | Yes      | -       |
| `tag-name`     | Target tag for the release                                                   | Yes      | -       |
| `chapters`     | YAML multi-line list mapping titles to labels (supports `label` or `labels`) | No       | -       | 
| `verbose`      | Enable detailed logging                                                      | No       | false   |

For the full input and output reference, see [Configuration reference](docs/configuration_reference.md).  
For how label → chapter mapping and aggregation works, see [Custom Chapters Behavior](docs/configuration_reference.md#custom-chapters-behavior).

> **Important**: tag defined by `tag-name` must exist in the repository; otherwise, the action fails.

## Example Workflow

You can integrate this Action with your release process.

### Example — Manual Release Dispatch

```yaml
name: "Create Release & Notes"
on:
  workflow_dispatch:
    inputs:
      tag-name:
        description: 'Existing git tag to use for this draft release. Syntax: "v[0-9]+.[0-9]+.[0-9]+". Ensure the tag is created and pushed before running.'
        required: true

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate Release Notes
        id: notes
        uses: AbsaOSS/generate-release-notes@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag-name: ${{ github.event.inputs.tag-name }}
          chapters: |
            - {"title": "New Features 🎉", "labels": "enhancement, feature"}
            - {"title": "Bugfixes 🛠", "labels": "error, bug"}
            - {"title": "Infrastructure 🚧", "label": "infrastructure"}
            - {"title": "Documentation 📚", "label": "documentation"}
            - {"title": "Internal Notes 📝", "labels": "internal", "hidden": true}
            - {"title": "Not Implemented ⏳", "labels": "wip", "hidden": true}

      - name: Create Draft Release
        uses: softprops/action-gh-release@v2
        with:
          name: ${{ github.event.inputs.tag-name }}
          tag_name: ${{ github.event.inputs.tag-name }}
          body: ${{ steps.notes.outputs.release_notes }}
          draft: true
```

For more complex automation scenarios, see the [examples](examples) folder.

## Feature Tutorials

Each feature is documented separately — click a name below to learn configuration, examples, and best practices.

| Feature                                                               | Scope                     | Description                                                                                                    |
|-----------------------------------------------------------------------|---------------------------|----------------------------------------------------------------------------------------------------------------|
| [Release Notes Extraction](docs/features/release_notes_extraction.md) | Extraction                | Core logic that scans descriptions to extract structured release notes (and optionally CodeRabbit summaries).  |
| [CodeRabbit Integration](docs/features/coderabbit_integration.md)     | Extraction                | Optional extension to Release Notes Extraction, enabling AI-generated summaries when PR notes are missing.     |
| [Skip Labels](docs/features/skip_labels.md)                           | Filtering                 | Exclude issues/PRs carrying configured labels from all release notes.                                          |
| [Service Chapters](docs/features/service_chapters.md)                 | Quality & Warnings        | Surfaces gaps: issues without PRs, unlabeled items, PRs without notes, etc.                                    |
| [Duplicity Handling](docs/features/duplicity_handling.md)             | Quality & Warnings        | Marks duplicate lines when the same issue appears in multiple chapters.                                        |
| [Tag Range Selection](docs/features/tag_range.md)                     | Time Range                | Chooses scope via `tag-name`/`from-tag-name`.                                                                  |
| [Date Selection](docs/features/date_selection.md)                     | Time Range                | Chooses scope via timestamps (`published-at` vs `created-at`).                                                 |
| [Custom Row Formats](docs/features/custom_row_formats.md)             | Formatting & Presentation | Controls row templates and placeholders (`{number}`, `{title}`, `{developers}`, …).                            |
| [Custom Chapters](docs/features/custom_chapters.md)                   | Formatting & Presentation | Maps labels to chapter headings; aggregates multiple labels under one title.                                   |
| [Issue Hierarchy Support](docs/features/issue_hierarchy_support.md)   | Formatting & Presentation | Displays issue → sub-issue relationships.                                                                      |
| [Verbose Mode](docs/features/verbose_mode.md)                         | Diagnostics & Technical   | Adds detailed logs for debugging.                                                                              |

_Category legend (keep it consistent across docs)_

- **Extraction** – how notes are gathered (core behavior).
- **Filtering** – what gets included/excluded.
- **Quality & Warnings** – health checks that keep releases clean.
- **Time Range** – how the release window is determined.
- **Formatting & Presentation** – how lines look.
- **Diagnostics & Technical** – tooling, logs, debug.

## Troubleshooting
Common questions and quick pointers.

| Symptom | Likely Cause | Where to Read More |
|---------|--------------|--------------------|
| Issue/PR missing from a chapter | Skip label applied | [Skip Labels](docs/features/skip_labels.md) |
| Issue missing but its PR appears | No change increment detected for issue (no merged PR linkage) | [Release Notes Extraction](docs/features/release_notes_extraction.md) |
| Chapter heading is empty | No qualifying records OR duplicates suppressed | [Custom Chapters](docs/features/custom_chapters.md#faq) |
| Expected duplicate not shown | `duplicity-scope` excludes that chapter category | [Duplicity Handling](docs/features/duplicity_handling.md) |
| CodeRabbit section ignored | Manual release notes section already present OR support disabled | [CodeRabbit Integration](docs/features/coderabbit_integration.md) |

More Q&A: see the [Custom Chapters FAQ](docs/features/custom_chapters.md#faq).

## Developer & Contribution Guide

We love community contributions!
- [Developer Guide](DEVELOPER.md)
- [Contributing Guide](CONTRIBUTING.md)

Typical contributions include:
- Fixing bugs or edge cases
- Improving documentation or examples
- Adding new configuration options

## License & Support

This project is licensed under the **Apache License 2.0**.
See the [LICENSE](/LICENSE) file for full terms.

### Support & Contact
- [Issues](https://github.com/AbsaOSS/generate-release-notes/issues)
- [Discussions](https://github.com/AbsaOSS/generate-release-notes/discussions)

## Acknowledgements

Thanks to all contributors and teams who helped evolve this Action.
Your feedback drives continuous improvement and automation quality.
