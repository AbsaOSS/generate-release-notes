# Feature: Release Notes Extraction

## Purpose
Extract structured release note lines from pull request (and issue) descriptions. Provides a predictable, labeled section that is transformed into categorized chapters. Reduces manual curation and enforces consistent formatting.

## How It Works
- Detects the first section in the PR body whose heading/title line matches the configurable regex input `release-notes-title` (default: `[Rr]elease [Nn]otes:`). Only the first match is used; later matches are ignored (first matching section rule).
- Reads subsequent list lines until a blank line, a new heading, or end of body. Supported bullet markers: `-`, `*`, `+` (mixed usage allowed).
- Each bullet becomes a release note entry attached to the PR (and, when applicable, its linked issue); formatting of the final output row is controlled separately by Custom Row Formats.
- If no matching section (or it’s empty after filtering) AND CodeRabbit Integration is enabled, the CodeRabbit summary section may be used as a fallback (see CodeRabbit Integration).
- Issue ↔ PR linkage is determined both by GitHub closing keywords in PR bodies (e.g. `Fixes #123`) and by API lookups of closing references. See [Issue ↔ PR Linking](../configuration_reference.md#issue--pr-linking).

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v1.2.0"
    chapters: |
      - {"title": "New Features 🎉", "label": "feature"}
      - {"title": "Bugfixes 🛠", "label": "bug"}
    release-notes-title: "[Rr]elease [Nn]otes:"       # optional regex override
    skip-release-notes-labels: "skip-release-notes,internal-doc" # comma-separated list
    coderabbit-support-active: false                  # fallback disabled here
```

### PR Body Example (author input)
```markdown
Some intro text

Release Notes:
- Add user MFA enrollment flow
* Improve cache invalidation logic
+ Adjust logging level for retries

Other commentary...
```

## Example Result
```markdown
### New Features 🎉
- PR: #123 _PR title_ developed by @alice
  - Add user MFA enrollment flow
  - Improve cache invalidation logic
  - Adjust logging level for retries
```
(Formatting depends on row format settings and whether the issue/PR linkage exists.)

## Related Features
- [CodeRabbit Integration](./coderabbit_integration.md) – fallback when explicit notes section is absent.
- [Skip Labels](./skip_labels.md) – exclude items entirely from extraction.
- [Custom Row Formats](./custom_row_formats.md) – control placeholder layout of resulting lines.
- [Duplicity Handling](./duplicity_handling.md) – mark lines appearing in multiple chapters.
- [Issue Hierarchy Support](./issue_hierarchy_support.md) – presentation when parent/child issues are involved.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
