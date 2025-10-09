# Feature: Release Notes Extraction

This feature extracts structured release notes directly from pull request descriptions.

## Purpose

Automatically ensures that all merged PRs include a readable, human-written summary of their impact.

## How It Works

1. Scans PR body for section matching `release-notes-title` regex.
2. Fallbacks to CodeRabbit summaries when enabled.
3. Supports Markdown lists with `-`, `*`, or `+`.
4. Skips PRs labeled with `skip-release-notes-labels`.

## Example Configuration

```yaml
with:
  release-notes-title: '[Rr]elease [Nn]otes:'
  coderabbit-support-active: true
  coderabbit-release-notes-title: 'Summary by CodeRabbit'
```

## Example PR Body

```markdown
## Release Notes:
- Added caching mechanism improving performance by 20%.
- Added distributed cache layer.
```

## Output Example

See examples/output_example.md (TODO link)

```yaml

