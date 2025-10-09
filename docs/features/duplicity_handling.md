# Feature: Duplicity Handling

## Purpose
Control whether the same record (issue / PR / hierarchy issue / commit) can appear in multiple chapters and visually mark duplicates. Prevents clutter while still allowing intentional multi-label visibility.

## How It Works
- Input `duplicity-scope` defines where duplicates are allowed: `none`, `custom`, `service`, `both` (case-insensitive).
- When a record matches multiple user-defined chapters and scope permits (`custom` or `both`), it can appear more than once.
- Service Chapters obey the same rule: duplicates allowed only if scope includes `service` or `both`.
- A duplicate (present in >1 chapter) is prefixed by the single-character icon from `duplicity-icon` (default: 🔔) when rendered.
- If duplicates are disallowed for a given group, additional occurrences are skipped silently (no placeholder or warning).

### Choosing `duplicity-scope`
| Value | Custom Chapters Duplicates | Service Chapters Duplicates | Icon Applied (if >1 appearance) | Typical Use Case |
|-------|----------------------------|------------------------------|---------------------------------|------------------|
| `none` | No | No | Never (only single appearance) | Strict single-source classification |
| `custom` | Yes | No | Yes (in custom) | Emphasize multi-label themes; keep diagnostics lean |
| `service` | No | Yes | Yes (in service) | Observe all diagnostic contexts; keep user chapters clean |
| `both` | Yes | Yes | Yes | Maximum visibility across all chapter types |

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v3.0.0"
    chapters: |
      - {"title": "Features", "label": "feature"}
      - {"title": "Quality", "label": "quality"}
    duplicity-scope: "both"   # none|custom|service|both
    duplicity-icon: "🔔"       # must be exactly one character
```

## Example Result
```markdown
### Features
🔔 #410 _Improve cache layer_ developed by @alice in #415

### Quality
🔔 #410 _Improve cache layer_ developed by @alice in #415
```
(Icon appears because the same record appeared in two chapters with scope permitting duplicates.)

## Related Features
- [Service Chapters](./service_chapters.md) – also affected by duplicity scope.
- [Custom Row Formats](./custom_row_formats.md) – icon is prefixed before formatted line.
- [Skip Labels](./skip_labels.md) – skipped records never produce duplicates.
- [Release Notes Extraction](./release_notes_extraction.md) – determines which records have change increments.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
