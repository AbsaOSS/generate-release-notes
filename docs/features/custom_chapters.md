# Feature: Custom Chapters

## Purpose
Map issue and PR labels to human-friendly chapter titles. Lets teams group multiple labels under a single heading and control output order without modifying repository label taxonomy.

## How It Works
- Input `chapters` is a YAML list; each entry contains `title` + `label`.
- Multiple entries with the same `title` aggregate labels into one chapter (logical OR).
- Records qualify when: not skipped, contain a change increment (at least one linked merged PR), and have ≥1 matching label (explicit or implicit Issue Type label).
  - Issue Type is automatically merged as a lowercase implicit label (e.g. `Epic` → `epic`, `Feature` → `feature`, `Bug` → `bug`, `Task` → `task`). You can reference these directly in `chapters` without creating extra labels in the repository.
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
      - {"title": "Epics", "label": "epic"}          # using implicit issue type label
    duplicity-scope: "custom"
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

## FAQ
**Why didn’t my issue appear in any chapter?**
- It has a skip label (see [Skip Labels](./skip_labels.md)).
- It has no change increment (no merged PR linked to it).
- Its labels (including implicit issue type) don’t match any configured chapter labels.
- It’s still open and hierarchy/Service Chapters logic filtered it (for some diagnostics scenarios) but not eligible for user chapters.
- Duplicates disabled (`duplicity-scope` excludes `custom`) and it already appeared under an earlier matching chapter.

**How do I group by issue types without adding labels?**  Use the lowercase implicit type (`epic`, `feature`, `bug`, `task`) in `chapters`.

**Why is a chapter heading empty?** Either no records qualified or they were all skipped/excluded by duplicity scope. Disable empty headings via `print-empty-chapters: false`.

**Can a PR-only item appear without an issue?** Yes—if its labels match a chapter. The line will format using the PR row template.

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – governs multi-chapter visibility.
- [Release Notes Extraction](./release_notes_extraction.md) – provides the change increment lines.
- [Skip Labels](./skip_labels.md) – excluded records never reach chapters.
- [Custom Row Formats](./custom_row_formats.md) – adjusts row templates.
- [Service Chapters](./service_chapters.md) – diagnostics separate from user-defined chapters.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
