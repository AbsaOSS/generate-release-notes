# Feature: Date Selection

## Purpose
Choose which timestamp from the previous release defines the cutoff boundary (the "since" moment) for included issues, PRs, and commits. Provides control for teams that publish releases later than they create them.

## How It Works
- Input `published-at` (boolean, default `false`).
- When `published-at: true`, the previous release’s `published_at` timestamp is used.
- When `false`, the previous release’s `created_at` timestamp is used.
- If no prior release exists (first release), all issues are fetched without a filtration.

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v1.6.0"
    from-tag-name: "v1.5.0"  # defines the previous release
    published-at: true        # use published_at instead of created_at
    chapters: |
      - {"title": "Features", "label": "feature"}
      - {"title": "Fixes", "label": "bug"}
```

## Example Result
```markdown
### Features
- #360 _Add audit event sink_ developed by @dev in #365

#### Full Changelog
https://github.com/org/repo/compare/v1.5.0...v1.6.0
```
(The included only records occurred after the chosen previous release timestamp.)

## Related Features
- [Tag Range Selection](./tag_range.md) – defines which releases bound the window.
- [Service Chapters](./service_chapters.md) – uses same time window for diagnostics.
- [Release Notes Extraction](./release_notes_extraction.md) – only scans PRs within the window.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)

