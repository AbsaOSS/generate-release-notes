# Feature: Skip Labels

## Purpose
Exclude all issues and pull requests from release notes chapters population process when they carry one of the configured labels. Keeps internal, noise, or non-user-facing work out of published notes.

## How It Works
- Controlled by input `skip-release-notes-labels` (comma‑separated). Default: `skip-release-notes`.
- If any label on an issue or PR matches the configured list, that record is marked as skipped (`skip=True`).
- Skipped records are ignored by: Custom Chapters, and Service Chapters population logic.

>  **Observable effect:** they do not appear in any chapter, even if they would otherwise match.

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v2.0.0"
    chapters: |
      - {"title": "Features", "label": "feature"}
      - {"title": "Fixes", "label": "bug"}
    skip-release-notes-labels: "skip-release-notes,internal,ops"
```

### Example
Given PR #120 labeled `internal`:
```markdown
Features
- (no line for #120 – it was skipped)
```

## Example Result
```markdown
### Features
- #118 _Add MFA support_ developed by @alice in #119

### Fixes
- #121 _Resolve cache eviction bug_ developed by @bob in #122

#### Full Changelog
https://github.com/org/repo/compare/v1.5.0...v2.0.0

```
> (Internal / skipped items not shown.)

## Related Features
- [Service Chapters](./service_chapters.md) – skipped items don’t appear as warnings.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
