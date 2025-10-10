# Feature: Issue Hierarchy Support

## Purpose
Represent issue → sub-issue relationships directly in release notes, aggregating linked sub-issues and their pull requests under hierarchical parents. Gives stakeholders a structured view of larger deliverables.

## How It Works
- Enabled via input `hierarchy: true` (default: `false`). When disabled, all issues render flat.
- Parent issues are detected; sub-issues (and nested hierarchy issues) are fetched and ordered by level. Levels indent with two spaces per depth; nested items use list markers (`-`).
- Only closed sub-issues that contain a change increment (merged PR to default branch) are rendered; open ones, and PR to non default branch are ignored.
- Each hierarchy issue line can expand with its own extracted release notes block if present (prefixed with `_Release Notes_:` heading within the item block).

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v1.6.0"
    hierarchy: true
    chapters: |
      - {"title": "New Features 🎉", "label": "feature"}
```

## Example Result
```markdown
### New Features 🎉
- Epic: _Make Login Service releasable under new Maven central repository_ #140
  - Updated `sbt.version` to `1.11.5` for release.
  - Updated Developers
  - Updated `sbt-ci-release` to `1.11.2`
  - Updated `scala213 = "2.13.13"`
  - Feature: _Add user MFA enrollment flow_ #123 developed by @alice in #124
    - Add user MFA enrollment flow
```
(1st four indented bullets under Epic line represent the extracted release notes from the parent hierarchy issue's body.)

## Related Features
- [Custom Row Formats](./custom_row_formats.md) – controls hierarchy line rendering.
- [Service Chapters](./service_chapters.md) – flags missing change increments if hierarchy parents lack qualifying sub-issues.
- [Duplicity Handling](./duplicity_handling.md) – duplicate hierarchy items can be icon-prefixed if allowed.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)

