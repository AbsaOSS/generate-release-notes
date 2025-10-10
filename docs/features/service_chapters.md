# Feature: Service Chapters

## Purpose
Highlight quality gaps or inconsistencies in the release scope: missing PR for closed issues, unlabeled issues or PRs, or direct commits. Helps maintain hygiene and encourages authors to supply complete metadata.

## How It Works
- Enabled when input `warnings` is `true` (default). When `false`, service chapters are omitted entirely.
- Builds a fixed set of diagnostic chapters after custom (user-defined) chapters are rendered.
- Honors `print-empty-chapters` (default `true`) to either show or suppress empty diagnostic sections.
- Respects `duplicity-scope`: if duplicates not allowed in Service chapters (`duplicity-scope` excludes `service`/`both`), a record appears only once.
- Skipped records (Skip Labels) are not considered.
- Issue ↔ PR linkage here relies on the same detection as main extraction: GitHub closing keywords (e.g. `Fixes #123`) plus API lookups of closing references. See [Issue ↔ PR Linking](../configuration_reference.md#issue--pr-linking).

### Service Chapter Set
| Chapter Title | Condition Reported                                                     |
|---------------|------------------------------------------------------------------------|
| Closed Issues without Pull Request ⚠️ | Closed issue with zero linked PRs                                      |
| Closed Issues without User Defined Labels ⚠️ | Closed issue missing all user-defined chapter labels                   |
| Merged PRs without Issue and User Defined Labels ⚠️ | Merged PR with no linked issue and none of the user-defined labels     |
| Closed PRs without Issue and User Defined Labels ⚠️ | Closed (not merged) PR missing issue link and user-defined labels      |
| Merged PRs Linked to 'Not Closed' Issue ⚠️ | PR merged while a linked issue is still open                           |
| Direct commits ⚠️ | Commits on default branch without PR                              |
| Others - No Topic ⚠️ | Fallback bucket when none of the above matched but the record surfaced |

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v1.6.0"
    chapters: |
      - {"title": "New Features 🎉", "label": "feature"}
      - {"title": "Bugfixes 🛠", "label": "bug"}
    warnings: true              # enable service chapters (default)
    print-empty-chapters: true  # show even when empty (default)
    duplicity-scope: "both"     # allow duplicates across custom + service
```

## Example Result
```markdown
### Closed Issues without Pull Request ⚠️
All closed issues linked to a Pull Request.

### Closed Issues without User Defined Labels ⚠️
- N/A: #129 _PoC: attempt to do chrome negotiation on a get enpoint_ in #143
  - Added Option for AWS SSM Paramter Store as alternative to AWS Secrets manager for storing credentials
  - Updated Tests to support the new addition
  - Updated ReadMe to indicate how to implement.

### Direct commits ⚠️
All direct commits are linked pull requests.
```
(Excerpt; remaining chapters omitted for brevity.)

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – controls duplicate visibility and icons.
- [Skip Labels](./skip_labels.md) – skipped records never appear here.
- [Release Notes Extraction](./release_notes_extraction.md) – determines change increments referenced.
- [Custom Row Formats](./custom_row_formats.md) – defines row layout reused here.
- Custom (user-defined) chapters are configured via YAML (`chapters` input); this page only covers diagnostic Service Chapters. For configuration details see [Configuration Reference](../configuration_reference.md#custom-chapters-behavior).

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
