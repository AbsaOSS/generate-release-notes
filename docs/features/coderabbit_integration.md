# Feature: CodeRabbit Integration

## Purpose
Provide an automatic fallback summary for pull requests that lack an explicit Release Notes section. Uses a CodeRabbit-generated summary block when available and configured, reducing manual effort and minimizing empty chapters.

> NOTE: This action only CONSUMES a CodeRabbit summary already present in the PR body. It does NOT configure, invoke, or authenticate CodeRabbit itself. Any CodeRabbit workflow, app installation, or settings are managed outside of this action.

## How It Works
- Activation is controlled by input `coderabbit-support-active` (default: `false`). When `false`, no CodeRabbit parsing occurs.
- If Release Notes Extraction fails to find a matching section (or yields zero valid bullet lines), the action searches for a section whose heading matches `coderabbit-release-notes-title` (regex, default: `Summary by CodeRabbit`).
- The detected summary text is converted into bullet entries using existing bullet list markers (`-`, `*`, `+`) found inside the summary block.
- Groups listed in `coderabbit-summary-ignore-groups` are removed. Delimiters supported: comma (",") OR newline. The parser picks comma if present; otherwise splits by newline.
- If both explicit release notes AND a CodeRabbit section exist, only the explicit release notes are used (no merge; strict fallback behavior).
- Skip Labels still apply: PRs or issues labeled with any `skip-release-notes-labels` value are ignored entirely.

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
    coderabbit-support-active: true
    coderabbit-release-notes-title: "Summary by CodeRabbit"   # optional regex override
    coderabbit-summary-ignore-groups: "Chore,Internal"        # comma or newline separated list
    release-notes-title: "[Rr]elease [Nn]otes:"               # shown for clarity
```

### PR Body Example (no explicit release notes)
```markdown
Implementation details...

Summary by CodeRabbit
- Add MFA enrollment flow
- Improve cache invalidation

Additional notes.
```

## Example Result (fallback in effect)
```markdown
### New Features 🎉
- #233 _Add MFA enrollment flow_ developed by @alice in #234
  - Add MFA enrollment flow
  - Improve cache invalidation
```
(Exact formatting depends on Custom Row Formats and whether an issue is linked.)

## Limitations
- Only activates when no valid explicit release notes section is found.
- Relies on predictable heading text; modified headings may need a custom `coderabbit-release-notes-title` regex.
- Group filtering requires consistent group naming within the CodeRabbit summary output.
- Does not merge with partially present manual notes—manual notes have precedence.

## Related Features
- [Release Notes Extraction](./release_notes_extraction.md) – primary mechanism; CodeRabbit is only a fallback.
- [Skip Labels](./skip_labels.md) – can exclude PRs entirely (applies before fallback).
- [Duplicity Handling](./duplicity_handling.md) – marks duplicates across chapters.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
