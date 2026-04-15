# Feature: Service Chapters

## Purpose
Highlight quality gaps or inconsistencies in the release scope: missing PR for closed issues, unlabeled issues or PRs, or direct commits. Helps maintain hygiene and encourages authors to supply complete metadata.

## How It Works
- Enabled when input `warnings` is `true` (default). When `false`, service chapters are omitted entirely.
- Builds a fixed set of diagnostic chapters after custom (user-defined) chapters are rendered.
- The "Closed Issues without User Defined Labels" chapter appears immediately after user-defined chapters, followed by the remaining service chapters.
- Honors `print-empty-chapters` (default `true`) to either show or suppress empty diagnostic sections.
- Respects `duplicity-scope`: if duplicates not allowed in Service chapters (`duplicity-scope` excludes `service`/`both`), a record appears only once.
- Skipped records (Skip Labels) are not considered.
- Issue ↔ PR linkage here relies on the same detection as main extraction: GitHub closing keywords (e.g. `Fixes #123`) plus API lookups of closing references. See [Issue ↔ PR Linking](../configuration_reference.md#issue--pr-linking).

### Service Chapter Set
The service chapters appear in the following order in the generated release notes:

1. **Closed Issues without User Defined Labels ⚠️** (appears first, immediately after user-defined chapters)
2. Closed Issues without Pull Request ⚠️
3. Merged PRs without Issue and User Defined Labels ⚠️
4. Closed PRs without Issue and User Defined Labels ⚠️
5. Merged PRs Linked to 'Not Closed' Issue ⚠️
6. Direct commits ⚠️
7. Others - No Topic ⚠️

| Chapter Title | Condition Reported                                                     |
|---------------|------------------------------------------------------------------------|
| **Closed Issues without User Defined Labels ⚠️** | Closed issue missing all user-defined chapter labels                   |
| Closed Issues without Pull Request ⚠️ | Closed issue with zero linked PRs                                      |
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
    warnings: true                     # enable service chapters (default)
    hidden-service-chapters: ''        # hide specific service chapters (default: empty)
    service-chapter-order: ''          # custom display order (default: empty = default order)
    service-chapter-exclude: ''        # label-exclusion rules per chapter (default: empty)
    print-empty-chapters: true         # show even when empty (default)
    duplicity-scope: "both"            # allow duplicates across custom + service
```

### Granular Chapter Control
Use `hidden-service-chapters` to selectively hide individual service chapters:

```yaml
- name: Generate Release Notes
  with:
    warnings: true
    hidden-service-chapters: |
      Direct Commits ⚠️
      Others - No Topic ⚠️
```

Or use comma-separated format:
```yaml
    hidden-service-chapters: "Direct Commits ⚠️, Others - No Topic ⚠️"
```

**Available service chapter titles:**
- `Closed Issues without Pull Request ⚠️`
- `Closed Issues without User Defined Labels ⚠️`
- `Merged PRs without Issue and User Defined Labels ⚠️`
- `Closed PRs without Issue and User Defined Labels ⚠️`
- `Merged PRs Linked to 'Not Closed' Issue ⚠️`
- `Direct Commits ⚠️`
- `Others - No Topic ⚠️`

**Note:** Title matching is exact and case-sensitive. When `warnings: false`, all service chapters are hidden regardless of the `hidden-service-chapters` setting.

### Custom Display Order
Use `service-chapter-order` to control the order in which service chapters appear:

```yaml
- name: Generate Release Notes
  with:
    warnings: true
    service-chapter-order: |
      Others - No Topic ⚠️
      Direct commits ⚠️
      Closed Issues without Pull Request ⚠️
```

Or use comma-separated format:
```yaml
    service-chapter-order: "Others - No Topic ⚠️, Direct commits ⚠️"
```

**Behavior:**
- Listed chapters are rendered first in the given order.
- Any service chapters not listed are appended afterward in the default order.
- If omitted, the default order is preserved.
- Unknown titles are logged as errors and skipped.
- Duplicate titles are logged as errors and skipped.

**Available service chapter titles (default order):**
1. `Closed Issues without User Defined Labels ⚠️`
2. `Closed Issues without Pull Request ⚠️`
3. `Merged PRs without Issue and User Defined Labels ⚠️`
4. `Closed PRs without Issue and User Defined Labels ⚠️`
5. `Merged PRs Linked to 'Not Closed' Issue ⚠️`
6. `Direct commits ⚠️`
7. `Others - No Topic ⚠️`

**Note:** Title matching is exact and case-sensitive. The `service-chapter-order` input is independent of `hidden-service-chapters`; hidden chapters are still hidden even if listed in the order.

### Label-Based Exclusion Rules
Use `service-chapter-exclude` to filter out issues/PRs from service chapters by label combinations. Each rule is a group of labels that must **all** be present on a record (AND logic) for the record to be excluded. Multiple groups per chapter are evaluated with OR logic (any group match excludes the record).

**Per-chapter exclusion** — excludes a matching record from that chapter only:

```yaml
- name: Generate Release Notes
  with:
    warnings: true
    service-chapter-exclude: |
      Closed Issues without Pull Request ⚠️:
        - [scope:security, type:tech-debt]
        - [scope:security, type:false-positive]
      Others - No Topic ⚠️:
        - [wontfix]
```

**Global exclusion** — use the reserved key `"*"` to exclude matching records from **all** service chapters:

```yaml
- name: Generate Release Notes
  with:
    warnings: true
    service-chapter-exclude: |
      "*":
        - [scope:security, type:tech-debt]
      Closed Issues without Pull Request ⚠️:
        - [scope:security, type:false-positive]
```

**Behavior:**
- Within a group, all labels must be present on the issue (AND logic).
- Across groups, any single match is sufficient to exclude (OR logic).
- The `"*"` key applies to every service chapter; a matching record is dropped entirely.
- Per-chapter rules only affect the specified chapter; the record may still appear in other chapters.
- Global exclusion takes precedence over per-chapter rules.
- Label strings that do not appear on any record simply prevent the group from matching.
- Unknown chapter titles are skipped with a warning.
- If omitted or empty, no exclusion is applied.

## Example Result
```markdown
### Closed Issues without User Defined Labels ⚠️
- N/A: #129 _PoC: attempt to do chrome negotiation on a get enpoint_ in #143
  - Added Option for AWS SSM Paramter Store as alternative to AWS Secrets manager for storing credentials
  - Updated Tests to support the new addition
  - Updated ReadMe to indicate how to implement.

### Closed Issues without Pull Request ⚠️
All closed issues linked to a Pull Request.

### Direct commits ⚠️
All direct commits are linked pull requests.
```
**Excerpt:** Remaining chapters omitted for brevity.

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – controls duplicate visibility and icons.
- [Skip Labels](./skip_labels.md) – skipped records never appear here.
- [Release Notes Extraction](./release_notes_extraction.md) – determines change increments referenced.
- [Custom Row Formats](./custom_row_formats.md) – defines row layout reused here.
- Custom (user-defined) chapters are configured via YAML (`chapters` input); this page only covers diagnostic Service Chapters. For configuration details see [Configuration Reference](../configuration_reference.md#custom-chapters-behavior).

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
