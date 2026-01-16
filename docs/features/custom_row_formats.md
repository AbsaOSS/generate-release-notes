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
- **Empty field suppression**: When a placeholder value is empty, the generator intelligently omits the surrounding text fragment for specific placeholders (`{type}`, `{assignees}`, `{developers}`, `{pull-requests}`):
  - If `{type}` is empty → the entire `{type}:` or `{type} ` prefix is omitted (no "N/A" placeholder)
  - If `{assignees}` is empty → the entire `assigned to {assignees}` phrase is omitted
  - If `{pull-requests}` is empty → the `in {pull-requests}` suffix is omitted
  - If both `{developers}` and `{pull-requests}` are empty → the entire `developed by {developers} in {pull-requests}` phrase is omitted
  - Note: Other placeholders (`{number}`, `{title}`, `{author}`) do not trigger suppression and are replaced with empty strings if missing
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
- #505 _Dependency Dashboard update_ author is @renovate[bot]
- PR: #506 _Add inline diff viewer_ developed by @kevin
```

_Formatting reflects the provided custom templates. Note how issues without a type omit the type prefix, and issues without PRs omit the "in {pull-requests}" suffix._

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – may add icon before formatted line.
- [Issue Hierarchy Support](./issue_hierarchy_support.md) – hierarchy rows use their own format.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)

