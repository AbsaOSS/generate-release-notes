# SPEC — Compare-mode data mining

## Problem

The current `mine_data()` method derives a `since` timestamp from the previous release and fetches all
commits/PRs/issues in that time window. This breaks for branching release histories (e.g. maintenance
`v2.6.x` alongside a `develop`-based `v2.7.x`) because commits from the other branch fall inside the
same window.

### Concrete example

Full commit graph (abbreviated):

```
develop branch:
*  (tag: v2.7.1) 2026-05-20  Improve Kafka consumer throughput (#1401)
*  (tag: v2.7.0) 2026-05-14  Fix new service access role (#1363)
*  2026-05-07  Fix/1346 custom hive table (#1349)
*  2026-05-07  Collect latest OpenAPI changes (#1330)
| maintenance/v2.6.x branch:
| *  (tag: v2.6.5) 2026-05-20  Backport: handle empty schema in Hive (#1402)
| *  (tag: v2.6.4) 2026-05-14  Fix new service access role (#1363)   ← cherry-pick
| *  (tag: v2.6.3) 2026-05-07  Fix/1346 custom hive table (#1349)    ← cherry-pick
|/
*  (tag: v2.6.0) 2026-04-21  Fixes for update-ca-certificates (#1318)
```

#### Case 1 — `v2.6.4` (released same day as `v2.7.0`)

Generating release notes for `v2.6.4` (previous: `v2.6.3`):

- **Timestamp mode (current):** `since = published_at(v2.6.3) = 2026-05-07`.
  `repo.get_commits(since=…)` returns every commit authored between 2026-05-07 and 2026-05-14
  on **any branch** — including `#1349` and `#1330` from develop. Those belong to `v2.7.0`, not
  `v2.6.4`, yet they appear in the release notes output.

- **Compare mode (new):** `repo.compare("v2.6.3", "v2.6.4")` returns only the commits reachable
  from `v2.6.4` but **not** from `v2.6.3` — exactly `#1363`. That is the correct set.

#### Case 2 — `v2.6.5` (released after `v2.7.0` and `v2.7.1`)

This case is even more broken with the timestamp approach.

Generating release notes for `v2.6.5` (previous: `v2.6.4`):

- **Timestamp mode (current):** `since = published_at(v2.6.4) = 2026-05-14`.
  `repo.get_commits(since=…)` returns everything authored between 2026-05-14 and 2026-05-20 on
  **any branch** — that includes `#1363` (v2.7.0) and `#1401` (v2.7.1) from develop. Neither of
  those belongs in the `v2.6.5` patch release notes, but both appear in the output. As more `v2.7.x`
  releases accumulate, the noise grows linearly.

- **Compare mode (new):** `repo.compare("v2.6.4", "v2.6.5")` returns only `#1402` — the single
  backport commit unique to `v2.6.5`. That is the correct set, regardless of how many `v2.7.x`
  commits exist in the same timestamp window.

The equivalent Git command the user already uses manually:
```
git log --oneline --right-only --cherry-pick v2.6.4...v2.6.5
```

---

## Solution

### When compare mode activates

Compare mode is used when the `from-tag-name` action input is explicitly provided. When it is absent,
the existing timestamp-based path runs unchanged.

### PyGitHub API used

`repo.compare(base: str, head: str) → Comparison`

- Calls `GET /repos/{owner}/{repo}/compare/{base}...{head}` (three-dot diff — commits in `head` not reachable from `base`).
- Available in PyGitHub ≥ 2.x; confirmed present in the project's locked version (`PyGithub==2.9.1`).
- Returns a `github.Comparison.Comparison` object with:
  - `commits: PaginatedList[github.Commit.Commit]` — up to 10,000 commits, fully iterable; same `Commit` type already used throughout the codebase.
  - `files: list[File]` — first 300 changed files only (not used here).
- The `Commit` objects have the same shape as those returned by `repo.get_commits()`, so no type conversion is needed downstream.

`repo.get_pull(number: int) → PullRequest`

- Calls `GET /repos/{owner}/{repo}/pulls/{pull_number}`.
- Returns a full `github.PullRequest.PullRequest` object — same type as those in `data.pull_requests` today.

### What changes in `DataMiner.mine_data()`

**Timestamp mode (unchanged path):**
1. Derive `data.since` from the previous release timestamp.
2. `repo.get_commits(since=data.since)` — all commits authored after that timestamp on the default branch.
3. `repo.get_pulls(state="closed", base=default_branch)` — all closed PRs; `FilterByRelease` trims them by `merged_at >= data.since`.
4. `repo.get_issues(since=data.since)` — all issues updated after that timestamp.

**Compare mode (new path):**
1. Derive `data.since` from the previous release timestamp (same as before — used by `_get_issues` for
   unrelated issue fetching, kept for consistency with the rest of the pipeline).
2. `comparison = repo.compare(from_tag, to_tag)` — returns only commits reachable from `to_tag` but
   not from `from_tag`. Same semantics as `git log --right-only --cherry-pick from_tag...to_tag`.
3. Iterate `comparison.commits` to collect the commit objects and their SHAs.
4. Extract PR numbers from the commit messages (helper `_extract_pr_numbers_from_commits`):
   - Pattern A (squash-merge): `(#NNN)` anywhere in the message → PR number `NNN`.
   - Pattern B (merge-commit): `Merge pull request #NNN from …` → PR number `NNN`.
   - Both patterns handled by a single regex `\(#(\d+)\)|Merge pull request #(\d+)`.
   - Cherry-picks are handled automatically: the commit message on the maintenance branch is
     identical to the one on develop, so the PR number is always present regardless of which SHA
     was used for the cherry-pick.
5. For each extracted PR number, call `repo.get_pull(number)` to retrieve the full PR object.
   `None` results (deleted/missing PRs) are silently skipped.
6. `data.pull_requests` is populated with only those PRs; `data.issues` is left as `{}`.
7. `data.compare_commit_shas` is set to the set of SHAs from step 3.

### What changes in `FilterByRelease`

`FilterByRelease` currently trims commits and PRs by timestamp. In compare mode the commit/PR set is
already exact, so timestamp trimming must be skipped.

Guard: if `data.compare_commit_shas` is non-empty, copy commits and PRs through unchanged; otherwise
run the existing timestamp filter logic.

### New field on `MinedData`

`compare_commit_shas: set[str]` — empty by default; set to the SHA strings of all commits returned by
`repo.compare(…)` in compare mode. Acts as the sentinel that tells `FilterByRelease` which path to take.

### What does NOT change

- Issue fetching and filtering logic is untouched.
- `data.since` is still derived from the previous release and propagated everywhere that uses it
  (e.g. `custom_chapters.since` for release-note extraction date-gating).
- The semantic-version ordering path for finding the previous release is untouched.
- All downstream record building (factory, chapters, builder) is unaffected.

---

## Files changed

- `release_notes_generator/model/mined_data.py` — add `compare_commit_shas: set[str]` field
- `release_notes_generator/data/miner.py` — add compare-mode branch in `mine_data()`; add helper `_extract_pr_numbers_from_commits()`
- `release_notes_generator/data/filter.py` — skip timestamp filter for PRs and commits when `compare_commit_shas` is non-empty

---

## Test cases (confirmed green ✅)

All 22 tests implemented and passing (`tests/unit/release_notes_generator/data/`).

### Helper: `DataMiner._extract_pr_numbers_from_commits` — `test_miner.py`

| # | Name | Intent | Commit messages | Expected `set[int]` |
|---|------|--------|-----------------|---------------------|
| 1 | `test_extract_pr_numbers_squash_format` | Squash-merge `(#NNN)` tail | `["Fix service access role (#1363)"]` | `{1363}` |
| 2 | `test_extract_pr_numbers_merge_format` | Merge-commit `Merge pull request #NNN` header | `["Merge pull request #1358 from org/branch"]` | `{1358}` |
| 3 | `test_extract_pr_numbers_multiple_commits` | All PR numbers from multiple commits | 3 commits: `"…(#10)"`, `"Merge pull request #20 from …"`, `"…(#30)"` | `{10, 20, 30}` |
| 4 | `test_extract_pr_numbers_deduplicates` | Same PR referenced in two commits is returned once | `["Fix A (#42)", "Follow-up for #42 (#42)"]` | `{42}` |
| 5 | `test_extract_pr_numbers_no_references` | No `#NNN` patterns → empty set | `["Initial commit", "Fix typo in README"]` | `set()` |
| 6 | `test_extract_pr_numbers_empty_input` | Empty commit list → empty set | `[]` | `set()` |
| 7 | `test_extract_pr_numbers_multiline_message` | PR number in second line of message | `["Subject line\n\nFixes behaviour (#77)"]` | `{77}` |

### `DataMiner.mine_data()` — compare mode — `test_miner.py`

| # | Name | Intent | Setup | Expected |
|---|------|--------|-------|----------|
| 8 | `test_mine_data_compare_mode_uses_compare_api` | `repo.compare` is called (not `get_commits`) | `is_from_tag_name_defined=True`, from-tag=`v2.6.3`, to-tag=`v2.6.4`; compare returns 1 commit `#1363` | `repo.compare` called once; `repo.get_commits` NOT called; `data.compare_commit_shas == {sha_of_1363}` |
| 9 | `test_mine_data_compare_mode_fetches_prs_by_number` | PRs fetched individually by number from message | Compare commit message `"Fix (#42)"`; `repo.get_pull(42)` returns mock PR | `data.pull_requests == {mock_pr: repo}` |
| 10 | `test_mine_data_compare_mode_multiple_prs` | Two commits → two distinct PRs fetched | Messages `"A (#10)"` and `"B (#20)"`; both `get_pull` calls return valid PRs | `len(data.pull_requests) == 2` |
| 11 | `test_mine_data_compare_mode_leaves_issues_empty` | `data.issues` is `{}` in compare mode | Any compare setup | `data.issues == {}` |
| 12 | `test_mine_data_compare_mode_sets_data_since` | `data.since` still derived from release `created_at` | Release with `created_at=2026-05-07`; `published-at=false` | `data.since == datetime(2026, 5, 7)` |
| 13 | `test_mine_data_compare_mode_sets_data_since_published_at` | `data.since` uses `published_at` when flag set | Release with `published_at=2026-05-08`; `published-at=true` | `data.since == datetime(2026, 5, 8)` |
| 14 | `test_mine_data_compare_mode_skips_none_prs` | `get_pull` returning `None` silently omitted | Compare commit refs PR #99; `get_pull(99)` returns None | `data.pull_requests == {}` |
| 15 | `test_mine_data_compare_mode_no_pr_numbers_in_message` | Commit with no PR ref produces no PRs | Commit message `"Bump version to 2.6.4"` | `data.pull_requests == {}`; `data.compare_commit_shas` non-empty |

### `DataMiner.mine_data()` — timestamp mode (regression) — `test_miner.py`

| # | Name | Intent | Setup | Expected |
|---|------|--------|-------|----------|
| 16 | `test_mine_data_timestamp_mode_uses_get_commits` | Timestamp path calls `get_commits(since=…)` not `compare` | `is_from_tag_name_defined=False`; `data.since` set | `repo.get_commits` called with `since=data.since`; `repo.compare` NOT called |
| 17 | `test_mine_data_timestamp_mode_compare_shas_empty` | `compare_commit_shas` is empty set in timestamp mode | `is_from_tag_name_defined=False` | `data.compare_commit_shas == set()` |

### `FilterByRelease` — compare mode guard — `test_filter.py`

| # | Name | Intent | Setup | Expected |
|---|------|--------|-------|----------|
| 18 | `test_filter_compare_mode_passes_prs_through` | PRs kept regardless of `merged_at` when in compare mode | `compare_commit_shas` non-empty; PR `merged_at` is 30 days before `data.since` | PR present in `filtered.pull_requests` |
| 19 | `test_filter_compare_mode_passes_commits_through` | Commits kept regardless of author date when in compare mode | `compare_commit_shas` non-empty; commit author date is 30 days before `data.since` | Commit present in `filtered.commits` |
| 20 | `test_filter_compare_mode_passes_multiple_prs_and_commits` | All PRs and commits pass through unfiltered | `compare_commit_shas` non-empty; 3 PRs and 2 commits all dated before `data.since` | All 3 PRs and 2 commits in filtered result |
| 21 | `test_filter_timestamp_mode_filters_old_prs` | Timestamp mode: PR before `since` is excluded | `compare_commit_shas == set()`; PR `merged_at` before `data.since` | PR absent from `filtered.pull_requests` |
| 22 | `test_filter_timestamp_mode_keeps_recent_prs` | Timestamp mode: PR after `since` is kept | `compare_commit_shas == set()`; PR `merged_at` after `data.since` | PR present in `filtered.pull_requests` (regression guard) |

---

## Proposed documentation updates

These changes should be applied to the user-facing docs once the feature ships.

### `docs/features/tag_range.md`

Replace the **How It Works** section with:

```markdown
## How It Works

### Timestamp mode (default when `from-tag-name` is omitted)
- The previous release's timestamp is used as the `since` boundary.
- Commits, PRs, and issues updated after that timestamp are fetched.
- **Limitation:** breaks for branching release histories — commits from other active branches
  (e.g. `v2.7.x`) fall inside the same timestamp window and appear in the patch release notes.

### Compare mode (activated when `from-tag-name` is explicitly provided)
- Uses the GitHub Compare API (`GET /repos/{owner}/{repo}/compare/{from-tag}...{to-tag}`).
- Returns only commits reachable from `tag-name` but **not** from `from-tag-name`, regardless
  of timestamp or branch.
- PR numbers are extracted from those commit messages; only the matching PRs are fetched.
- Cherry-picks are handled automatically: the commit message on the maintenance branch preserves
  the original PR reference.
- Equivalent: `git log --oneline --right-only --cherry-pick <from-tag>...<to-tag>`

**Example** — `v2.6.5` (previous: `v2.6.4`):

​```
develop:
*  (tag: v2.7.1) 2026-05-20  Improve Kafka consumer throughput (#1401)
*  (tag: v2.7.0) 2026-05-14  Fix new service access role (#1363)
maintenance/v2.6.x:
| *  (tag: v2.6.5) 2026-05-20  Backport: handle empty schema in Hive (#1402)
| *  (tag: v2.6.4) 2026-05-14  Fix new service access role (#1363)  ← cherry-pick
|/
*  (tag: v2.6.0) 2026-04-21  …
​```

- **Timestamp mode** fetches commits between 2026-05-14 and 2026-05-20 on any branch → captures
  `#1363` and `#1401` from develop. Incorrect.
- **Compare mode** (`repo.compare("v2.6.4", "v2.6.5")`) returns only `#1402`. Correct.

### Other behaviour (both modes)
- Tag normalization: `1.6.0` and `v1.6.0` are both accepted.
- `data.since` is still derived from the previous release in compare mode (used for issue fetching
  and release-note extraction date-gating).
- If no prior release exists (first release), all issues/PRs are included.
```

Also update the **Configuration** example to show `from-tag-name: "v2.6.4"` and the
**Example Result** to show only `#1402`.

---

### `docs/configuration_reference.md`

Update the `from-tag-name` row description from:

> `Explicit previous release tag; if empty semantic latest published release is used.`

To:

> `Explicit previous release tag. When provided, activates compare mode (graph-based commit
> selection via GitHub Compare API), which is correct for branching release histories
> (e.g. maintenance v2.6.x alongside v2.7.x). If empty, semantic latest published release is
> used with timestamp-based filtering. See [Tag Range](../docs/features/tag_range.md).`
