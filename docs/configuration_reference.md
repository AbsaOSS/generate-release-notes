# Configuration Reference

This page lists all action inputs and outputs with defaults. Grouped for readability.

## Inputs

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `tag-name` | Yes | – | Target release tag (must already exist). |
| `from-tag-name` | No | "" | Explicit previous release tag; if empty semantic latest published release is used. |
| `chapters` | No | "" | YAML list of chapter objects `{ "title": str, "label": str }`. Multiple entries may share a title to aggregate labels. |
| `hierarchy` | No | `false` | Enable Issue Hierarchy Support. |
| `published-at` | No | `false` | Use previous release `published_at` timestamp instead of `created_at`. |
| `skip-release-notes-labels` | No | `skip-release-notes` | Comma‑separated labels that fully exclude issues/PRs. |
| `warnings` | No | `true` | Toggle Service Chapters generation. |
| `print-empty-chapters` | No | `true` | Print chapter headings even when empty. |
| `duplicity-scope` | No | `both` | Where duplicates are allowed: `none`, `custom`, `service`, `both`. Case-insensitive. |
| `duplicity-icon` | No | `🔔` | One-character icon prefixed on duplicate rows. |
| `verbose` | No | `false` | Enable verbose (debug) logging. |
| `release-notes-title` | No | `[Rr]elease [Nn]otes:` | Regex matching the PR body section header for manual notes. First match only. |
| `coderabbit-support-active` | No | `false` | Enable CodeRabbit fallback when manual notes absent. |
| `coderabbit-release-notes-title` | No | `Summary by CodeRabbit` | Regex for CodeRabbit summary header. |
| `coderabbit-summary-ignore-groups` | No | "" | Comma or newline list of group names to discard from CodeRabbit summary. |
| `row-format-hierarchy-issue` | No | `{type}: _{title}_ {number}` | Template for hierarchy (parent) issue rows. |
| `row-format-issue` | No | `{type}: {number} _{title}_ developed by {developers} in {pull-requests}` | Template for issue rows. |
| `row-format-pr` | No | `{number} _{title}_ developed by {developers}` | Template for PR rows. |
| `row-format-link-pr` | No | `true` | If true adds `PR:` prefix when a PR is listed without an issue. |

> CodeRabbit summaries must already be present in the PR body (produced by your own CI/App setup). This action only parses existing summaries; it does not configure or call CodeRabbit.

### Placeholder Reference

| Context | Placeholders |
|---------|--------------|
| Issue | `{type}`, `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}`, `{pull-requests}` |
| PR | `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}` |
| Hierarchy Issue | `{type}`, `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}` |

Placeholders are case-insensitive; unknown placeholders are removed silently.

### Chapters Configuration
Provide chapters as a YAML multi-line string. Each entry must define a `title` and `label`.

```yaml
with:
  chapters: |
    - {"title": "New Features 🎉", "label": "feature"}
    - {"title": "Bugfixes 🛠", "label": "bug"}
    - {"title": "Bugfixes 🛠", "label": "error"}  # merges both labels under one heading
```

Resulting chapter headings are unique by title; labels aggregate.

### Custom Chapters Behavior
- A record (issue / PR / hierarchy issue) is eligible for a user-defined chapter if it:
  - Is not skipped (no skip label), and
  - Contains a change increment (has extracted release notes OR at least one linked merged PR supplying changes), and
  - Owns at least one label matching any configured chapter label (including implicit issue type label), and
  - (For hierarchy) ultimately aggregates qualifying sub-issues/PRs.
- Issue Type is automatically merged into the issue's label set as a lowercase implicit label (e.g. `Epic`, `Feature`, `Bug`, `Task` → `epic`, `feature`, `bug`, `task`). You can reference these directly in `chapters` without adding a duplicate formal label in GitHub.
- Direct commits are excluded (no labels to match).
- Multiple entries with identical `title` merge label sets (logical OR across labels under the same heading).
- Rendering order follows the YAML order of first appearance for each unique title.
- If `duplicity-scope` excludes `custom`, a record that matched one chapter will not be added to others.
- Empty chapters: suppressed only when `print-empty-chapters: false`.
- Duplicity icon is applied per appearance count after all chapters are populated.

### Issue ↔ PR Linking
Link detection influences chapter population and Service Chapters:
- GitHub automatically links PRs to issues using closing keywords (e.g. `Fixes #123`, `Closes org/repo#45`). These become closing issue references available through the API.
- The action also queries GitHub (GraphQL) for closing issue references of each PR (internal implementation) to gather linked issues.
- If no issue is linked and required metadata is missing, affected PRs can appear in Service Chapters (e.g. *Merged PRs without Issue and User Defined Labels ⚠️*).

### Skip Logic
Any issue or PR containing at least one label from `skip-release-notes-labels` is entirely excluded from:
- Release Notes Extraction (manual section parsing)
- CodeRabbit fallback detection
- Custom (user-defined) Chapters
- Service Chapters

### Duplicates
Controlled by `duplicity-scope` and `duplicity-icon` (see [Duplicity Handling](features/duplicity_handling.md)).

## Outputs

| Name | Description |
|------|-------------|
| `release-notes` | Final Markdown block of release notes (includes Service Chapters if enabled and a Full Changelog link). |

## Quick Selection Guide

| Goal | Recommended Inputs |
|------|--------------------|
| Basic release notes | `tag-name`, `chapters` |
| Restrict time window manually | Add `from-tag-name` |
| Prefer published timestamp | `published-at: true` |
| Hide diagnostics | `warnings: false` |
| Tight output (no empty headings) | `print-empty-chapters: false` |
| Enforce no duplicates | `duplicity-scope: none` |
| Enable hierarchy rollups | `hierarchy: true` |
| Use AI fallback | `coderabbit-support-active: true` |

## Related Pages
- [Feature Tutorials](../README.md#feature-tutorials)
- [Release Notes Extraction](features/release_notes_extraction.md)
- [Service Chapters](features/service_chapters.md)
- [Duplicity Handling](features/duplicity_handling.md)
