# Configuration Reference

This page lists all action inputs and outputs with defaults. Grouped for readability.

## Inputs

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `tag-name` | Yes | – | Target release tag (must already exist). |
| `from-tag-name` | No | "" | Explicit previous release tag; if empty semantic latest published release is used. |
| `chapters` | No | "" | YAML multi-line list of chapter entries (title + label or labels). Optional flags: `hidden: true` excludes chapter from output; `catch-open-hierarchy: true` marks the chapter as a Conditional Custom Chapter that intercepts all open hierarchy parent issues before label routing (requires `hierarchy: true`). Supports legacy `label` or multi `labels` definitions. |
| `hierarchy` | No | `false` | Enable Issue Hierarchy Support. |
| `published-at` | No | `false` | Use previous release `published_at` timestamp instead of `created_at`. |
| `skip-release-notes-labels` | No | `skip-release-notes` | Comma‑separated labels that fully exclude issues/PRs. |
| `warnings` | No | `true` | Toggle Service Chapters generation. |
| `hidden-service-chapters` | No | "" | Comma or newline list of service chapter titles to hide from output. Title matching is exact and case-sensitive. Only effective when `warnings: true`. |
| `service-chapter-order` | No | "" | Comma or newline list of service chapter titles controlling display order. Listed titles render first; unlisted titles appended in default order. Title matching is exact and case-sensitive. Only effective when `warnings: true`. |
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
| `super-chapters` | No | "" | YAML multi-line list of super-chapter entries (`title` + `label`/`labels`). Groups regular chapters under higher-level headings by label. See [Super Chapters](features/custom_chapters.md#super-chapters). |

> CodeRabbit summaries must already be present in the PR body (produced by your own CI/App setup). This action only parses existing summaries; it does not configure or call CodeRabbit.

### Placeholder Reference

| Context | Placeholders |
|---------|--------------|
| Issue | `{type}`, `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}`, `{pull-requests}` |
| PR | `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}` |
| Hierarchy Issue | `{type}`, `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}` |

Placeholders are case-insensitive; unknown placeholders are removed silently.

### Chapters Configuration
Provide chapters as a YAML multi-line string. Each entry must define a `title` and either `label` (legacy) or `labels` (multi-label). Optionally include `hidden: true` to exclude the chapter from output while still processing records. Set `catch-open-hierarchy: true` to create a Conditional Custom Chapter that captures open hierarchy parents before label routing.

```yaml
with:
  chapters: |
    - {"title": "Breaking Changes 💥", "label": "breaking-change"}          # legacy single-label form
    - {"title": "Internal Notes 📝", "labels": "internal", "hidden": true}  # hidden chapter
    - {"title": "Silent Live 🤫", "catch-open-hierarchy": true}              # Conditional Custom Chapter
```

Resulting chapter headings are unique by title; label sets aggregate across repeated titles (logical OR). Whitespace is trimmed; duplicates removed preserving first-seen order.

### Custom Chapters Behavior
- A record (issue / PR / hierarchy issue) is eligible for a user-defined chapter if it:
  - Is not skipped (no skip label), and
  - Contains a change increment, and
  - Has at least one label intersecting the chapter’s label set.
- Direct commits are excluded (no labels).
- `label` vs `labels` precedence: if both exist, `labels` is used and a warning logged once.
- Multi-label tokens may be separated by commas.
- Empty or invalid label definitions skip the chapter with a warning (do not abort generation).
- A record may appear in multiple chapters (cross-chapter duplication always allowed, independent of `duplicity-scope`). Intra-chapter duplicates are suppressed.
- Ordering: Chapters rendered in order of first appearance of each unique title.
- When verbose mode is enabled, normalized label sets are logged at DEBUG level.
- **Hidden chapters**: Chapters with `hidden: true` are processed normally (records assigned and tracked) but:
  - Are excluded from final output rendering
  - Do NOT count toward duplicity detection (no 🔔 icon contribution)
  - Are always omitted regardless of `print-empty-chapters` setting

### Conditional Custom Chapters (`catch-open-hierarchy`)
A chapter with `catch-open-hierarchy: true` intercepts **open** `HierarchyIssueRecord` parents before any label-based routing, sending them to a dedicated section (e.g. "Silent Live"). When the parent eventually closes it falls back to normal label-based routing.

- Requires `hierarchy: true`. When hierarchy is disabled, the key is accepted but has no effect and a warning is logged.
- At most **one** chapter may set `catch-open-hierarchy: true`; extras are ignored with a warning.
- **Optional label filter**: add `labels` alongside `catch-open-hierarchy` to restrict interception to matching labels only. Open hierarchy parents that carry none of those labels fall through to normal routing.
- Can be combined with `hidden: true` to silently track in-progress hierarchy work without printing it.

```yaml
chapters: |
  - title: "New Features 🎉"
    labels: "feature, epic"
  - title: "Silent Live 🤫"
    catch-open-hierarchy: true      # capture all open hierarchy parents
  - title: "Bugfixes 🛠️"
    labels: "bug"
```

With an optional label filter:
```yaml
  - title: "Silent Live 🤫"
    catch-open-hierarchy: true
    labels: "feature, epic"         # only intercept open parents carrying these labels
```

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
| Hide all service chapters | `warnings: false` |
| Hide specific service chapters | `hidden-service-chapters: "Direct Commits ⚠️, Others - No Topic ⚠️"` |
| Reorder service chapters | `service-chapter-order: "Others - No Topic ⚠️, Direct commits ⚠️"` |
| Tight output (no empty headings) | `print-empty-chapters: false` |
| Enforce no duplicates | `duplicity-scope: none` |
| Enable hierarchy rollups | `hierarchy: true` |
| Track in-progress hierarchy work | `hierarchy: true` + add `catch-open-hierarchy: true` chapter |
| Use AI fallback | `coderabbit-support-active: true` |

## Related Pages
- [Feature Tutorials](../README.md#feature-tutorials)
- [Release Notes Extraction](features/release_notes_extraction.md)
- [Service Chapters](features/service_chapters.md)
- [Duplicity Handling](features/duplicity_handling.md)
