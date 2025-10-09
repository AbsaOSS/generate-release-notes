# Feature: Custom Row Formats

## Purpose
Customize how individual issue, PR, and hierarchy issue lines are rendered in the release notes. Ensures output matches team conventions without post-processing.

## How It Works
- Controlled by inputs:
  - `row-format-hierarchy-issue`
  - `row-format-issue`
  - `row-format-pr`
  - `row-format-link-pr` (boolean controlling prefix `PR:` presence for standalone PR links)
- Placeholders are case-insensitive; unknown placeholders are removed.
- Available placeholders:
  - Hierarchy issue rows: `{type}`, `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}`
  - Issue rows: `{type}`, `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}`, `{pull-requests}`
  - PR rows: `{number}`, `{title}`, `{author}`, `{assignees}`, `{developers}`
- Duplicity icon (if triggered) is prefixed before the formatted row.

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v4.0.0"
    chapters: |
      - {"title": "Features", "label": "feature"}
    row-format-hierarchy-issue: "{type}: _{title}_ {number}"
    row-format-issue: "{type}: {number} _{title}_ developed by {developers} in {pull-requests}"
    row-format-pr: "{number} _{title}_ developed by {developers}"
    row-format-link-pr: true  # include PR: prefix when issue not linked
```

## Example Result

```markdown
### Features
- Task: #500 _Add inline diff viewer_ developed by @alice in #501
- PR: #505 _Add inline diff viewer_ developed by @kevin
```

(Formatting reflects the provided custom templates.)

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – may add icon before formatted line.
- [Issue Hierarchy Support](./issue_hierarchy_support.md) – hierarchy rows use their own format.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)

