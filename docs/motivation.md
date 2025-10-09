# Motivation

Release documentation often drifts: missing PR summaries, unlabeled issues, or manual copy/paste errors right before a release. This Action was created to enforce **repeatable, label‑driven, metadata‑rich** release notes with minimal friction for contributors.

## Problems Addressed
- Manual release note curation is slow and error-prone.
- Inconsistent formatting across releases reduces readability.
- Orphaned work (issues without PRs / PRs without notes) goes unnoticed.
- Large epics or feature umbrellas are hard to summarize without hierarchy.
- AI (CodeRabbit) summaries are useful, but only as a fallback—manual author intent stays primary.

## Design Principles
| Principle | Explanation |
|-----------|-------------|
| Determinism | Same inputs produce the same release notes; no hidden heuristics. |
| Explicit Configuration | Chapters defined in YAML; no magic label groupings. |
| Fail Safe | If explicit notes missing, optionally fall back to CodeRabbit; never silently fabricate content. |
| Transparency | Service Chapters surface hygiene issues instead of hiding them. |
| Extensibility | Row formats, hierarchy, and duplicity policy are pluggable via inputs. |
| Minimal Boilerplate | Only a tag and basic chapters required for first adoption. |

## Key Inputs Snapshot
(See full list in [Configuration Reference](configuration_reference.md).)

| Category | Inputs (examples) | Purpose |
|----------|-------------------|---------|
| Scope | `tag-name`, `from-tag-name`, `published-at` | Define time window. |
| Extraction | `release-notes-title`, `coderabbit-*` | Control where notes are sourced. |
| Filtering | `skip-release-notes-labels` | Exclude internal/noisy work. |
| Quality | `warnings`, `duplicity-scope`, `duplicity-icon` | Surface inconsistencies & handle duplicates. |
| Formatting | `chapters`, row-format inputs, `print-empty-chapters` | Control output layout & presence of empty headings. |
| Structure | `hierarchy` | Enable multi-level issue rollups. |
| Diagnostics | `verbose` | Aid debugging. |

## Outputs
| Output | Description |
|--------|-------------|
| `release-notes` | Single Markdown block containing user-defined chapters, optional Service Chapters, and a Full Changelog link. |

## Why Chapters?
Labels are already a ubiquitous classification mechanism. Mapping labels to chapter titles gives **controllable taxonomy** (marketing-friendly headings) while keeping developer workflow unchanged. Repeating a `title` with different `label` values aggregates multiple labels under the same heading (e.g., `bug` + `error` → “Bugfixes 🛠”).

## Why Service Chapters?
Instead of silently skipping incomplete metadata, the Action exposes structural gaps (e.g., unlabeled issues, merged PRs with open issues) so teams can tighten process over time.

## Why Duplicity Policy?
Some teams prefer a single canonical appearance per item; others want visibility across thematic chapters (e.g., “Breaking Changes” AND “New Features”). The `duplicity-scope` input lets teams choose without forking logic.

## Why Hierarchy?
Complex efforts (epics) fragment across multiple issues/PRs. Hierarchical rendering bundles context and contributors while still allowing individual tracking.

## Why AI Fallback (Optional)?
AI summaries can fill gaps—but only when authors forget to supply release notes. The Action never overrides explicit human-authored content.

## Lifecycle Summary
1. Resolve previous release and time window.
2. Fetch issues, PRs, commits.
3. Extract release notes (manual → fallback AI if enabled).
4. Populate custom chapters (label → title mapping).
5. Add Service Chapters (if `warnings: true`).
6. Emit final Markdown.

## Related
- [Configuration Reference](configuration_reference.md)
- [Feature Tutorials](../README.md#feature-tutorials)

