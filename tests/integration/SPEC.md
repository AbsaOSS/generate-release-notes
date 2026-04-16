# Integration Test Specification — generate-release-notes

## Scope

These tests verify that multiple real components work together correctly end-to-end by calling
`main.run()` directly with `INPUT_*` env vars, a mocked GitHub instance, and a controlled
`MinedData` returned by a patched `DataMiner`.  The GitHub API network layer is never reached.

Call stack exercised: `main.run()` → `ActionInputs` → `ReleaseNotesGenerator.generate()` →
`FilterByRelease.filter()` → `DefaultRecordFactory.generate()` → `ReleaseNotesBuilder.build()` →
`CustomChapters.populate()` + `ServiceChapters.populate()` → final markdown string.

GitHub model objects (`Issue`, `PullRequest`, `Commit`, `Repository`, `GitRelease`) are mocked
at the `DataMiner.mine_data()` boundary using `pytest-mock`.  `get_issues_for_pr` (GitHub
GraphQL call) is patched at its import site in `default_record_factory`.

## File layout

```
tests/integration/
    SPEC.md
    conftest.py                    # shared fixtures and build_mined_data helper
    fixtures/
        test_full_pipeline_snapshot.md   # golden output for T-INT-01; regenerate with WRITE_SNAPSHOTS=1
    test_builder_pipeline.py       # T-INT-01 … T-INT-05 (offline)
    live/
        test_bulk_sub_issue_collector.py   # T-INT-LIVE-01 (requires GITHUB_TOKEN)
```

> **Snapshot workflow:** Run `WRITE_SNAPSHOTS=1 pytest tests/integration/test_builder_pipeline.py`
> to (re-)generate `fixtures/test_full_pipeline_snapshot.md`.  Without that env var the test
> performs a 1:1 string comparison against the stored file.
>
> **Live tests:** CI runs `pytest tests/integration/live/` only when `GITHUB_TOKEN` is available
> (non-fork PRs).  The offline suite in `test_builder_pipeline.py` never requires a token.

---

## Offline test cases (implemented)

| ID | Name | Status | One-line intent |
|---|---|---|---|
| T-INT-01 | `test_full_pipeline_snapshot` | ✅ Implemented | Full `main.run()` pipeline produces a 1:1 golden snapshot |
| T-INT-02 | `test_warnings_false_suppresses_service_chapters` | ✅ Implemented | `warnings=false` eliminates all service chapter output |
| T-INT-03 | `test_print_empty_chapters_false_hides_empty_headings` | ✅ Implemented | Empty custom chapter headings are suppressed when flag is off |
| T-INT-04 | `test_skip_labels_exclude_record_from_all_chapters` | ✅ Implemented | Skip-labeled records are absent from both custom and service chapters |
| T-INT-05 | `test_chapter_order_field_governs_output_sequence` | ✅ Implemented | `order` field controls ascending rendering sequence |

### T-INT-01 golden snapshot covers

The fixture file `fixtures/test_full_pipeline_snapshot.md` captures all of:

- Custom chapters (Bugfixes, Features, Enhancements) with rows and extracted release notes
- Duplicity scope `both` — issue with two labels appears in two chapters; second appearance has 🔔 icon
- Release notes extraction from issue body (`i2`) and from PR body (`pr10`)
- Skip label — `i4` and `i4`'s PR are silently absent everywhere
- Issues with no PR (`i5`, `i6`) routing into service chapters only (not in custom chapters)
- Unlinked merged PR (`pr40`) in "Merged PRs without Issue and User Defined Labels ⚠️"
- Direct commit (`c1`) in "Direct commits ⚠️"
- Empty service chapters rendered with placeholder text (`print_empty_chapters=true`)
- `#### Full Changelog` footer with compare URL

## Remaining scenarios (not yet implemented)

| ID | Name | One-line intent | Input summary | Expected output |
|---|---|---|---|---|
| T-INT-01 | `test_full_pipeline_custom_and_service_chapters` | Builder assembles all sections in correct order | 1 closed issue with `feature` label (→ custom chapter); 1 closed issue with no PR & no label (→ two service chapters); 1 direct commit. `warnings=True`, `print_empty_chapters=True` | Markdown: custom chapter first, then service chapter block, then `#### Full Changelog\n<url>` footer |
| T-INT-02 | `test_duplicity_scope_both_record_in_two_chapters_with_icon` | A dual-labeled record appears in both matching chapters, annotated with the duplicity icon | 1 issue with labels `["feature", "quality"]`; two chapters one per label; `duplicity_scope=both`, `duplicity_icon=🔔` | Issue row appears in **both** chapters; each row starts with `🔔` |
| T-INT-03 | `test_duplicity_scope_none_record_appears_once_no_icon` | First-match-wins; record absent from service chapters because already counted | Same dual-labeled issue as T-INT-02; `duplicity_scope=none` | Issue row appears in exactly one chapter; no `🔔`; record absent from service chapter output |
| T-INT-04 | `test_skip_labels_exclude_record_from_all_chapters` | Skipped record is invisible to both custom and service chapters | 1 normal `feature` issue; 1 `internal`-only issue; 1 issue with both `feature` and `internal`; `skip_release_notes_labels=internal` | Only the pure `feature` issue appears anywhere in the output; the other two are absent from all chapter sections |
| T-INT-05 | `test_hidden_chapter_tracked_but_absent_from_output` | Hidden chapter withholds rows from markdown but still counts the record | 1 issue labeled `wip`; chapter `{"title": "WIP", "label": "wip", "hidden": true}`; `duplicity_scope=both` | `### WIP` heading absent from output; record IS in `populated_record_numbers_list` so it does NOT re-appear in service chapters |
| T-INT-06 | `test_catch_open_hierarchy_chapter_intercepts_open_hierarchy_parent` | Open `HierarchyIssueRecord` is routed to the COH chapter, bypassing normal label matching | 1 open `HierarchyIssueRecord` labeled `["epic", "feature"]`; `catch_open_hierarchy` chapter for `epic`; separate `feature` chapter; `hierarchy=True` | The record appears in the COH chapter only; `feature` chapter is empty |
| T-INT-07 | `test_print_empty_chapters_false_suppresses_empty_headings` | Empty chapters are not rendered when flag is off | 2 chapters; only 1 has a matching record; `print_empty_chapters=False` | Output contains the populated chapter heading; empty chapter heading is absent |
| T-INT-08 | `test_warnings_false_suppresses_entire_service_chapter_block` | The `warnings` flag completely gates service chapter rendering | 1 unlinked merged PR (would normally hit a service chapter); `warnings=False` | No service chapter headings in output; `#### Full Changelog` footer is still present |
| T-INT-09 | `test_service_chapter_global_exclude_rule_drops_record` | A record matching the global `"*"` exclusion rule is absent from all service chapters | 1 closed issue with no label (hits "Closed Issues Without User Defined Labels"); global exclude rule `{"*": [["no-notes"]]}`, issue carries label `"no-notes"` | The issue does not appear in any service chapter section |
| T-INT-10 | `test_custom_chapter_order_field_governs_output_sequence` | Chapters render in `order`-ascending sequence regardless of declaration order | 3 chapters declared C→B→A with `order` values 30, 20, 10 respectively; one record per chapter | Output heading sequence is A (order 10), B (order 20), C (order 30) |

---

## Live test cases (require `GITHUB_TOKEN`)

| ID | Name | One-line intent | Input summary | Expected output |
|---|---|---|---|---|
| T-INT-LIVE-01 | `test_bulk_sub_issue_collector_smoke` | `BulkSubIssueCollector` can query the real GitHub API and accumulate parent→sub maps | Token from env; 2 fixed parent issue refs from `AbsaOSS/generate-release-notes`; max 2 scan iterations | Collector completes without error; `parents_sub_issues` attribute is a dict (possibly empty) |

---

## Fixtures required in `conftest.py`

| Fixture | Signature | Purpose |
|---|---|---|
| `make_issue_record` | `(mocker) -> Callable[[int, str, list[str], bool, int], IssueRecord]` | Factory: `(number, state, labels, skip, pr_count)` |
| `make_pr_record` | `(mocker) -> Callable[[int, bool, list[str], bool], PullRequestRecord]` | Factory: `(number, merged, labels, skip)` |
| `make_commit_record` | `(mocker) -> Callable[[str], CommitRecord]` | Factory: `(sha)` |
| `patch_env` | `(monkeypatch) -> Callable[[dict], None]` | Set `INPUT_*` env vars + required defaults, then reset `ActionInputs` class state |
| `build_notes` | `(patch_env, make_issue_record, …) -> Callable[[records, chapters_yaml, …], str]` | Compose records dict → `ReleaseNotesBuilder.build()` → return markdown string |
