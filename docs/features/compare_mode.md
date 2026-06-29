# Feature: Compare Mode

## Purpose
Ensure release notes for a maintenance branch contain **only** the changes that belong
to that branch, even when a parallel development branch (`v2.7.x`) is active and produces
commits in the same timestamp window.

## The Problem Compare Mode Solves

The default (timestamp) approach asks GitHub: *"give me all commits/PRs since time T".*
That works perfectly when every release is on a single linear history. It breaks the
moment two release streams run in parallel.

**Concrete example — two active streams:**

```text
develop:
*  (tag: v2.7.1) 2026-05-20  Improve Kafka consumer throughput (#1401)
*  (tag: v2.7.0) 2026-05-14  Fix new service access role (#1363)
*  2026-05-07  Fix/1346 custom hive table (#1349)
|
| maintenance/v2.6.x:
| *  (tag: v2.6.5) 2026-05-20  Backport: handle empty schema in Hive (#1402)
| *  (tag: v2.6.4) 2026-05-14  Fix new service access role (#1363)  ← cherry-pick
| *  (tag: v2.6.3) 2026-05-07  Fix/1346 custom hive table (#1349)   ← cherry-pick
|/
*  (tag: v2.6.0) 2026-04-21  Fixes for update-ca-certificates (#1318)
```

Generating release notes for **`v2.6.5`** (previous: `v2.6.4`):

| Mode | What is fetched | Correct? |
|---|---|---|
| **Timestamp** | Everything between 2026-05-14 and 2026-05-20 on *any* branch → `#1363` (v2.7.0) + `#1401` (v2.7.1) + `#1402` | ❌ two develop PRs contaminate the patch notes |
| **Compare** | Only commits reachable from `v2.6.5` but **not** `v2.6.4` → `#1402` only | ✅ |

---

## How Compare Mode Works

### Activation

Compare mode is active **when `from-tag-name` is explicitly provided**. When it is absent
the existing timestamp path runs unchanged.

> **Prerequisite — both tags must exist:**  Before the compare API is called, the action
> looks up each tag via `get_git_ref("tags/<tag>")`. If either tag is absent the action
> exits immediately with a tag-specific error message naming the missing tag.

### Step 1 — Graph-based commit selection

Instead of asking "what happened after time T?", the action asks GitHub: *"what commits
exist in `tag-name` that do not exist in `from-tag-name`?"*

This is a pure graph operation — it follows the commit ancestry tree, not the clock.
The result is exactly the set of commits unique to the current release, regardless of
when they were authored or which branch they live on.

### Step 2 — PRs derived from commit messages, not from a time filter

Rather than fetching all closed PRs and filtering by timestamp, compare mode reads the
PR numbers directly from the commit messages returned in Step 1. Both common merge
styles are recognised:

- **Squash-merge:** `Fix new service access role (#1363)`
- **Merge-commit:** `Merge pull request #1363 from org/branch`

Each unique PR number is then fetched individually by number. This means only the PRs
that actually belong to the release are ever loaded.

Cherry-picks are handled automatically: the commit message on the maintenance branch
preserves the original PR number, so the right PR is always found even though the
commit SHA differs from the one on develop.

### Step 3 — Why a PR can have a date before `data.since`

When a commit is cherry-picked, the PR object that gets fetched is the *original* PR —
the one that was merged onto develop weeks or months earlier. Its `merged_at` date is
that old develop date, which is before the previous maintenance tag's timestamp
(`data.since`).

Timestamp mode would silently drop it. Compare mode keeps it, because the commit graph
(not the clock) is the authority on what belongs in the release.

### Step 4 — `data.since` is still set, but only used for issues

`data.since` is always derived from the previous release's timestamp, in both modes.
In compare mode it is **not used to filter PRs or commits** — that job is already done
by the graph in Step 1. It is only used for:

- Fetching recently-updated **issues** (issue filtering is timestamp-based in both modes)
- Date-gating **release notes extraction** from PR/issue body text

### Step 5 — The filter stage passes PRs and commits through unchanged

`FilterByRelease` — the stage that normally drops PRs and commits older than
`data.since` — detects that compare mode is active and skips that timestamp check
entirely. The PR and commit sets arriving from `mine_data` are already exact; no further
trimming is needed or correct.

Issues are always filtered by timestamp regardless of mode.

---

## Data Flow

```
from-tag-name provided?
        │
     ┌──┴──────────────────────┐
    YES (compare mode)         NO (timestamp mode)
     │                         │
  Validate both tags exist      get_commits(since=data.since)
  (exit with error if missing)  get_pulls(state=closed)
     │                              │
  GitHub Compare API:          FilterByRelease drops
  commits unique to to-tag     PRs/commits before since
     │
  extract PR numbers
  from commit messages
     │
  fetch each PR by number
     │
  FilterByRelease: skip timestamp check — pass everything through
```

---

## Activation

```yaml
- name: Generate Release Notes
  uses: AbsaOSS/generate-release-notes@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag-name: ${{ github.event.inputs.tag-name }}           # the release being generated
    from-tag-name: ${{ github.event.inputs.from-tag-name }} # the previous release, activates compare mode when supplied
    chapters: |
      - {"title": "Bugfixes 🛠", "label": "bug"}
      - {"title": "Features 🎉", "label": "feature"}
```

> **When to use:** always supply `from-tag-name` when releasing from a maintenance branch
> that runs in parallel with a development branch.  Omitting it is fine for purely
> linear release histories.

---

## Related Features

- [Tag Range Selection](./tag_range.md) – explains the user-facing `from-tag-name` input and
  its interaction with compare mode.
- [Date Selection](./date_selection.md) – controls whether `created_at` or `published_at`
  is used as `data.since` (applies in both modes).
- [Release Notes Extraction](./release_notes_extraction.md) – uses `data.since` for body
  scanning; unaffected by compare mode.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
