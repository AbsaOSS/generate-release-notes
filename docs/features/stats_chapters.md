# Feature: Statistics & Anti-game Chapters

## Purpose
Surface skip-label usage statistics so that maintainers can audit who and what is being excluded from release notes via skip labels. Discourages overuse of the `skip-release-notes` label by making the practice visible.

## How It Works
- Enabled when input `show-stats-chapters` is `true` (default). When `false`, stats chapters are omitted entirely.
- Iterates **all** records, including those with `skip=True`, to compute totals and skip counts.
- The chapter is only rendered when at least one record in the release window carries a skip label. If nothing was skipped, the entire section is omitted regardless of `print-empty-chapters`.
- Honors `print-empty-chapters` for individual sub-sections: when `true` (default), sub-sections where no records were skipped but records exist are still shown (with a zero skipped count). When `false`, only sub-sections with at least one skipped record are rendered.
- Rendered after Service Chapters (or after Custom Chapters if `warnings: false`).

### Sub-sections

The chapter contains four fixed sub-sections in the following order:

#### 1. PR Authors
Compares PR authors and their usage of the skip label.

| Column | Description |
|--------|-------------|
| Author | PR author (`@login`) or `(no author)` |
| Total PRs | All PRs by that author |
| Skipped PRs | PRs by that author carrying a skip label |

#### 2. Issue Authors / Assignees
Compares issue authors and assignees and their usage of the skip label. A person appearing as both author and assignee of different issues is counted once per issue involvement.

| Column | Description |
|--------|-------------|
| Author / Assignee | Person (`@login`) or `(no author)` |
| Total Issues | Issues where this person is author or assignee |
| Skipped Issues | Skipped issues where this person is author or assignee |

#### 3. Issue Labels
Compares non-skip labels on issues and their usage of the skip label.

| Column | Description |
|--------|-------------|
| Label | Non-skip label on the issue, or `(no label)` |
| Total Issues | Issues carrying that label |
| Skipped Issues | Skipped issues carrying that label |

#### 4. PR Labels
Compares non-skip labels on PRs and their usage of the skip label.

| Column | Description |
|--------|-------------|
| Label | Non-skip label on the PR, or `(no label)` |
| Total PRs | PRs carrying that label |
| Skipped PRs | Skipped PRs carrying that label |

All sub-sections sort rows by skipped count descending, then by name ascending. Skip-label names are excluded from label buckets.

## Configuration
```yaml
- name: Generate Release Notes
  id: release_notes_scrapper
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: "v2.0.0"
    chapters: |
      - {"title": "Features", "label": "feature"}
      - {"title": "Fixes", "label": "bug"}
    show-stats-chapters: true          # enabled by default
    print-empty-chapters: true         # show sub-sections even with zero skips
```

To disable:
```yaml
    show-stats-chapters: false
```

## Example Result
```markdown
### Skip Release Notes Label Usage ⚠️
#### PR Authors
| Author | Total PRs | Skipped PRs |
|--------|-----------|-------------|
| @alice | 5 | 3 |
| @bob | 2 | 0 |

#### Issue Authors / Assignees
| Author / Assignee | Total Issues | Skipped Issues |
|--------------------|--------------|----------------|
| @alice | 6 | 3 |
| @bob | 4 | 2 |

#### Issue Labels
| Label | Total Issues | Skipped Issues |
|-------|--------------|----------------|
| bug | 6 | 4 |
| enhancement | 3 | 1 |
| (no label) | 2 | 2 |

#### PR Labels
| Label | Total PRs | Skipped PRs |
|-------|-----------|-------------|
| bug | 2 | 1 |
| (no label) | 1 | 1 |
```

## Related Features
- [Skip Labels](./skip_labels.md) – defines which labels mark records as skipped.
- [Service Chapters](./service_chapters.md) – quality diagnostics (skipped records are excluded there).

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
