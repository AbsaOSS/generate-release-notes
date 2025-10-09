# Feature: Tag Range Selection

## Purpose
Define the window of work (issues, PRs, commits) to include in the release notes by specifying current and optional previous tags. Ensures only changes since the chosen baseline are reported.

## How It Works
- Required input `tag-name` sets the target release tag (e.g. `v1.6.0`).
  - **Important**: this tag must exist in the repository; otherwise, the action fails.
- Optional input `from-tag-name` sets an explicit starting tag. When provided, the action fetches that release directly.
- If `from-tag-name` is NOT set, the action picks the latest published, non-draft, non-prerelease tag by semantic version ordering (may differ from most recently created chronologically if versions were pushed out-of-order).
  - If no prior release exists (first release), no filtering is applied; all issues/PRs are considered.
- Tag normalization: both `1.6.0` and `v1.6.0` are treated as `v1.6.0` internally.
- The time boundary ("since" value) is derived from the selected previous release timestamp (see Date Selection for which timestamp field is used).

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v1.6.0"         # current release tag
    from-tag-name: "v1.5.0"    # optional; if omitted semantic latest prior release is used
    chapters: |
      - {"title": "Features", "label": "feature"}
      - {"title": "Fixes", "label": "bug"}
```

## Example Result
```markdown
### Features
- #350 _Add MFA enrollment API_ developed by @alice in #355

#### Full Changelog
https://github.com/org/repo/compare/v1.5.0...v1.6.0
```
(The compare URL reflects both `from-tag-name` and `tag-name`.)

## Related Features
- [Date Selection](./date_selection.md) – defines which timestamp of the previous release becomes the cutoff.
- [Service Chapters](./service_chapters.md) – uses the same time window to assess gaps.
- [Release Notes Extraction](./release_notes_extraction.md) – only processes PRs/issues within the computed window.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)

