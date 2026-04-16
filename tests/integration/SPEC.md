# Integration Test Specification — generate-release-notes

## Scope

These tests verify that multiple real components work together correctly end-to-end.
The offline suite calls `main.run()` directly with `INPUT_*` env vars, a mocked GitHub
instance, and a controlled `MinedData` returned by a patched `DataMiner`.
The GitHub API network layer is never reached.

## Architecture — how the offline integration tests work

### Call stack exercised

```
main.run()
  → ActionInputs  (reads INPUT_* env vars)
  → ReleaseNotesGenerator.generate()
      → DataMiner.mine_data()          ← MOCKED: returns pre-built MinedData
      → FilterByRelease.filter()       ← real: time-based record filtering
      → DefaultRecordFactory.generate()← real: Issue/PR/Commit → Record objects
      → ReleaseNotesBuilder.build()    ← real: assembles final markdown
          → CustomChapters.populate()  ← real: label-based routing, COH, hidden
          → ServiceChapters.populate() ← real: warning chapters, exclusion rules
```

### Mock boundaries

| Boundary | Technique | Why |
|---|---|---|
| GitHub API (`Github`) | `mocker.patch("main.Github")` | Prevents real HTTP calls; rate-limiter wired to never sleep |
| `DataMiner.mine_data()` | `mocker.patch.object(DataMiner, "mine_data")` | Returns a hand-crafted `MinedData` with mock `Issue`/`PR`/`Commit` objects |
| `DataMiner.check_repository_exists()` | `mocker.patch.object(…, return_value=True)` | Skips real repo lookup |
| `get_issues_for_pr` (GraphQL) | `mocker.patch(…, return_value=set())` | Prevents sub-issue API calls; hierarchy tests would override this |
| `DataMiner.mine_missing_sub_issues()` | Patched in hierarchy tests only | Returns controlled parent→sub-issue mappings |

### Fixture factories (`conftest.py`)

Each factory creates a `pytest-mock` `Mock(spec=<GitHubClass>)` with the minimum
attributes the pipeline reads.  Tests compose these into `MinedData` via the
`build_mined_data()` helper.

| Factory | Creates | Key parameters |
|---|---|---|
| `make_issue` | `Issue` mock | `number, state, labels, title, body, user_login, closed_at` |
| `make_pr` | `PullRequest` mock | `number, title, body, user_login, labels, merged, merge_commit_sha` |
| `make_commit` | `Commit` mock | `sha, message, author_login` |
| `make_repo` | `Repository` mock | `full_name` |
| `make_release` | `GitRelease` mock | `tag_name` |

### Capture helper

`_capture_run(patch_env, overrides)` sets env vars, writes `GITHUB_OUTPUT` to a
temp file, calls `main.run()`, and parses the GitHub Actions multiline output
format (`release-notes<<EOF … EOF`) back into a plain string.

### Snapshot workflow

Run `WRITE_SNAPSHOTS=1 pytest tests/integration/test_builder_pipeline.py` to
regenerate `fixtures/test_full_pipeline_snapshot.md`.  Without that env var the
test performs a byte-for-byte comparison against the stored file.

## File layout

```
tests/integration/
    SPEC.md                              # this file
    conftest.py                          # shared fixtures and build_mined_data helper
    fixtures/
        test_full_pipeline_snapshot.md   # golden output for T-INT-01
    test_builder_pipeline.py             # T-INT-01 … T-INT-29 (offline, no token needed)
    live/
        test_bulk_sub_issue_collector.py # live smoke test (requires GITHUB_TOKEN)
```

---

## Test cases

| ID | Name | Intent | Status |
|---|---|---|---|
| T-INT-01 | `test_full_pipeline_snapshot` | Full `main.run()` pipeline produces a 1:1 golden snapshot | ✅ |
| T-INT-02 | `test_warnings_false_suppresses_service_chapters` | `warnings=false` eliminates all service chapter output | ✅ |
| T-INT-03 | `test_print_empty_chapters_false_hides_empty_headings` | Empty custom chapter headings suppressed when flag is off | ✅ |
| T-INT-04 | `test_skip_labels_exclude_record_from_all_chapters` | Skip-labeled records absent from both custom and service chapters | ✅ |
| T-INT-05 | `test_chapter_order_field_governs_output_sequence` | `order` field controls ascending rendering sequence | ✅ |
| T-INT-06 | `test_duplicity_scope_both_shows_icon_in_two_chapters` | Dual-labeled record appears in both chapters with 🔔 icon | ✅ |
| T-INT-07 | `test_duplicity_scope_none_record_appears_once` | scope=none prevents service-to-service duplication (record eligible for two service chapters appears in only one) | ✅ |
| T-INT-08 | `test_hidden_chapter_tracked_but_absent_from_output` | Hidden chapter heading and record content are absent from rendered output; visible chapters unaffected | ✅ |
| T-INT-09 | `test_service_chapter_global_exclude_drops_record` | Record matching `"*"` exclusion rule is absent from all service chapters | ✅ |
| T-INT-10 | `test_release_notes_extraction_from_issue_and_pr_body` | Release-notes blocks extracted and rendered under the record row | ✅ |
| T-INT-11 | `test_duplicity_scope_custom_allows_custom_prevents_service` | scope=custom allows custom-chapter dups but prevents service dups | ✅ |
| T-INT-12 | `test_per_chapter_service_exclude_rule` | Per-chapter exclude rule hides record from that chapter only | ✅ |
| T-INT-13 | `test_hidden_service_chapters_selective` | Hidden service chapters are omitted while others remain visible | ✅ |
| T-INT-14 | `test_multi_label_chapter_matches_any_label` | Chapter with `labels: [a, b]` matches records carrying either label | ✅ |
| T-INT-15 | `test_no_previous_release_includes_all_records` | No previous release → all records included unfiltered | ✅ |
| T-INT-16 | `test_custom_row_format_issue` | Custom `row-format-issue` template changes the rendered row | ✅ |
| T-INT-17 | `test_closed_pr_not_merged_routes_to_service_chapter` | Closed-but-not-merged PR lands in correct service chapter | ✅ |
| T-INT-18 | `test_open_issue_with_pr_routes_to_merged_prs_linked_open` | Open issue with linked PR routes to service chapter | ✅ |
| T-INT-19 | `test_service_chapter_ordering` | Reordering service chapters changes their position | ✅ |
| T-INT-20 | `test_coderabbit_release_notes_extraction` | CodeRabbit summary extracted when active and no explicit release notes | ✅ |
| T-INT-21 | `test_super_chapters_group_chapters_under_headings` | Super-chapters group custom chapters under level-2 headings | ✅ |
| T-INT-22 | `test_hierarchy_parent_sub_issue_rendering` | Hierarchy parent renders sub-issues indented beneath it | ✅ |
| T-INT-23 | `test_duplicity_scope_service_allows_service_prevents_custom` | scope=service allows service-chapter dups; custom chapters always duplicate | ✅ |
| T-INT-24 | `test_custom_row_format_pr` | Custom `row-format-pr` template changes unlinked PR row | ✅ |
| T-INT-25 | `test_row_format_link_pr_false` | `row-format-link-pr=false` removes "PR:" prefix | ✅ |
| T-INT-26 | `test_published_at_true_filters_by_published_timestamp` | `published-at=true` shifts filter boundary to published_at | ✅ |
| T-INT-27 | `test_coderabbit_summary_ignore_groups` | CodeRabbit ignore-groups filters excluded groups from output | ✅ |
| T-INT-28 | `test_custom_release_notes_title_regex` | Custom `release-notes-title` regex matches non-default heading | ✅ |
| T-INT-29 | `test_multiple_skip_release_notes_labels` | Multiple comma-separated skip labels all exclude records | ✅ |

### T-INT-01 golden snapshot covers

The fixture `fixtures/test_full_pipeline_snapshot.md` captures:

- Custom chapters (Bugfixes, Features, Enhancements) with rows
- Duplicity scope `both` — issue with two labels in two chapters; 🔔 icon on duplicate
- Release notes extraction from issue body and PR body
- Skip label — record silently absent everywhere
- Issues with no PR routing into service chapters only
- Unlinked merged PR in its service chapter
- Direct commit in its service chapter
- Empty service chapters with placeholder text (`print_empty_chapters=true`)
- `#### Full Changelog` footer with compare URL

## Live test cases (require `GITHUB_TOKEN`)

| ID | Name | Intent |
|---|---|---|
| LIVE-01 | `test_bulk_sub_issue_collector_smoke` | `BulkSubIssueCollector` queries the real GitHub API against `AbsaOSS/generate-release-notes` |

> CI runs live tests only when `GITHUB_TOKEN` is available (non-fork PRs).
> The offline suite never requires a token.
