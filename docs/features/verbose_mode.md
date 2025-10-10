# Feature: Verbose Mode

## Purpose
Provide detailed debug logging to troubleshoot configuration, data mining boundaries, label resolution, and chapter population decisions. Useful when release notes output is incomplete or unexpected.

## How It Works
- Controlled by input `verbose` (default: `false`). Set to `true` to enable debug logs.
- Also auto-enabled when the GitHub Actions runner sets `RUNNER_DEBUG=1` (e.g., via repository secrets / workflow debug).
- Emits detailed context: received inputs, debug messages during processing steps, received data from API calls.
- **Does not alter functional behavior** — only log verbosity.

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
      - {"title": "Features", "label": "feature"}
    verbose: true  # enable debug logging
```

## Example Result
```text
INFO  Building Release Notes
DEBUG Repository: org/repo
DEBUG Tag name: v1.6.0
DEBUG From tag name: v1.5.0
DEBUG Skip release notes labels: ['skip-release-notes', 'internal']
DEBUG Duplicity scope: BOTH
DEBUG Release notes title: [Rr]elease [Nn]otes:
DEBUG CodeRabbit support active: False
```
(Output abbreviated; actual log lines may vary.)

## Related Features
- [Release Notes Extraction](./release_notes_extraction.md) – debug lines show title regex and detection results.
- [Service Chapters](./service_chapters.md) – logs help trace why records appear (or not) in warnings.
- [Tag Range Selection](./tag_range.md) & [Date Selection](./date_selection.md) – logs display cutoff and release timing decisions.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)

