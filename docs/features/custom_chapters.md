# Feature: Custom Chapters

## Purpose
Define how issues and pull requests are grouped under human-friendly headings in the generated release notes.

## Basics
Each chapter entry requires a `title` and either:
- `label`: (legacy) single label string
- `labels`: (new) multi-label definition (comma separated string OR YAML list)

Optionally, you can add:
- `hidden`: (boolean) hide chapter from output while still tracking records (default: `false`)

```yaml
with:
  chapters: |
    - {"title": "New Features 🎉", "labels": "feature, enhancement"}        # multi-label form (comma separated)
    - {"title": "Bugfixes 🛠️", "label": "bug"}                              # legacy single-label form
    - {"title": "Platform 🧱", "labels": ["platform", "infra"]}             # multi-label form (YAML list)
    - {"title": "Internal Notes 📝", "labels": "internal", "hidden": true}  # hidden chapter
```

## Hidden Chapters

Hidden chapters allow you to define chapters that process records normally but are excluded from the final release notes output.

### Purpose
- Generate draft release notes without deleting chapter definitions
- Adds the benefit of reducing post-editing effort
- Hide work-in-progress or internal sections from stakeholders

### Behavior
When a chapter has `hidden: true`:
- **Processing**: Records ARE assigned to the chapter during population
- **Tracking**: Records in hidden chapters ARE tracked in internal lists
- **Duplicity Detection**: Hidden chapters do NOT count toward duplicity (no 🔔 icon contribution)
- **Output**: Hidden chapters are completely excluded from output rendering
- **Empty Chapter Setting**: `print-empty-chapters` has no effect on hidden chapters (always excluded)

### Examples

**Basic Usage:**
```yaml
chapters: |
  - {"title": "Features 🎉", "labels": "feature"}
  - {"title": "Bugs 🛠", "labels": "bug"}
  - {"title": "Not Implemented ⏳", "labels": "wip", "hidden": true}
  - {"title": "No Release Notes 📝", "labels": "no-rn", "hidden": true}
```

**Duplicity Behavior:**
- Record in 1 visible + 1 hidden chapter → duplicity count = 1 (no icon)
- Record in 2 visible + 1 hidden chapter → duplicity count = 2 (🔔 icon appears)
- Record in 0 visible + 2 hidden chapters → not visible in custom chapters (may appear in service chapters)

### Validation
The `hidden` field accepts:
- Boolean values: `true` or `false`
- Boolean-like strings (case-insensitive): `"true"`, `"True"`, `"false"`, `"False"`
- Invalid values log a warning and default to `false`
- Omitted field defaults to `false`

### Info Logging
When a chapter is marked as hidden, an info-level log message is emitted:
```
Chapter 'Internal Notes 📝' marked as hidden, will not appear in output (but records will be tracked)
```

### Debug Logging
With `verbose: true`, additional debug logging shows:
- Records assigned to hidden chapters with note about duplicity exclusion
- Skipped hidden chapters during rendering with record counts

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
- Invalid `hidden` value type or string

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

**Q: Do hidden chapters affect duplicity detection?**  
A: No. Hidden chapters process records but don't increment the chapter presence counter, so they don't contribute to duplicity icons.

**Q: Can I use hidden chapters for draft releases?**  
A: Yes! Mark chapters as `hidden: true` to track changes without showing them in published notes. Switch to `hidden: false` when ready to publish.

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
