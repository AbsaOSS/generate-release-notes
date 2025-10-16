# Feature: Custom Chapters

## Purpose
Define how issues and pull requests are grouped under human-friendly headings in the generated release notes.

## Basics
Each chapter entry requires a `title` and either:
- `label`: (legacy) single label string
- `labels`: (new) multi-label definition (comma separated string OR YAML list)

```yaml
with:
  chapters: |
    - {"title": "New Features 🎉", "labels": "feature, enhancement"}    # multi-label form (comma separated)
    - {"title": "Bugfixes 🛠️", "label": "bug"}                          # legacy single-label form
    - {"title": "Platform 🧱", "labels": ["platform", "infra"]}         # multi-label form (YAML list)
```

## Normalization Rules
1. Comma split.
2. Whitespace trimmed per token.
3. Empty tokens discarded.
4. Duplicates removed preserving first occurrence order.
5. If both `label` and `labels` present, `labels` takes precedence (single warning).
6. Invalid types (non-string/non-list) cause chapter skip with a warning.

## Inclusion Logic
A record is added to a chapter if its label set intersects the chapter’s normalized label set. Direct commits are ignored (they have no labels). A record can appear in multiple chapters; intra-chapter duplication is always suppressed.

## Deterministic Output
Chapter rendering order = order of first appearance of each unique title in the YAML input.

## Warnings
- Missing `title`
- Both `label` & `labels` (precedence notice)
- Invalid `labels` type
- Empty label set after normalization
- Unknown extra keys (ignored)

All warnings include the chapter title (when available) for traceability.

## Verbose Mode
Set `verbose: true` to log normalized label sets at DEBUG level.

## FAQ
**Q: Does `duplicity-scope` stop a record appearing in multiple custom chapters?**  
A: No. Cross-chapter duplication is always allowed; only intra-chapter duplication is suppressed.

**Q: Are labels case-normalized?**  
A: No. Matching is case-sensitive and uses the labels as returned by GitHub.

**Q: How do I merge more labels into an existing heading?**  
Provide multiple entries with the same `title` (legacy style) or just list them in one `labels` definition.

**Q: What if I accidentally leave a trailing comma?**  
Empty tokens are discarded; the chapter remains valid if at least one non-empty token exists.

## Example Output
```markdown
### New Features 🎉
- #410 _Add inline diff viewer_ developed by @alice in #415

### Bugfixes 🛠
- #412 _Fix cache stampede_ developed by @bob in #418
```

Use this feature to keep release notes concise and logically organized while supporting broader label groupings.

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – governs multi-chapter visibility.
- [Release Notes Extraction](./release_notes_extraction.md) – provides the change increment lines.
- [Skip Labels](./skip_labels.md) – excluded records never reach chapters.
- [Custom Row Formats](./custom_row_formats.md) – adjusts row templates.
- [Service Chapters](./service_chapters.md) – diagnostics separate from user-defined chapters.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
