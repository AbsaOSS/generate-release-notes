# Feature: Custom Chapters

## Purpose
Map issue and PR labels to human-friendly chapter titles. Lets teams group multiple labels under a single heading and control output order without modifying repository label taxonomy.

## How It Works
- Input `chapters` is a YAML list; each entry contains `title` + `label`.
- Multiple entries with the same `title` aggregate labels into one chapter (logical OR).
- Records qualify when: not skipped, contain a change increment (linked merged PR), and have ≥1 matching label.
- Direct commits are ignored (no labels) and appear only in Service Chapters if relevant.
- Duplicates across chapters depend on `duplicity-scope` (see Duplicity Handling). If disallowed, first match wins.
- Empty chapters printed only when `print-empty-chapters: true`.

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v2.1.0"
    chapters: |
      - {"title": "New Features 🎉", "label": "feature"}
      - {"title": "New Features 🎉", "label": "enhancement"}
      - {"title": "Bugfixes 🛠", "label": "bug"}
    duplicity-scope: "custom"   # allow duplicates among user chapters only
    print-empty-chapters: true
```

## Example Result
```markdown
### New Features 🎉
- #410 _Add inline diff viewer_ developed by @alice in #415

### Bugfixes 🛠
- #412 _Fix cache stampede_ developed by @bob in #418
```
(Multiple labels under the same title unify into one heading.)

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – governs multi-chapter visibility.
- [Release Notes Extraction](./release_notes_extraction.md) – provides the change increment lines.
- [Skip Labels](./skip_labels.md) – excluded records never reach chapters.
- [Custom Row Formats](./custom_row_formats.md) – adjusts row templates.
- [Service Chapters](./service_chapters.md) – diagnostics separate from user-defined chapters.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)

