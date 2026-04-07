# Feature: Custom Chapters

## Purpose
Define how issues and pull requests are grouped under human-friendly headings in the generated release notes.

## Basics
Each chapter entry requires a `title` and either:
- `label`: (legacy) single label string
- `labels`: (new) multi-label definition (comma separated string OR YAML list)

Optionally, you can add:
- `hidden`: (boolean) hide chapter from output while still tracking records (default: `false`)
- `order`: (integer) explicit rendering order; lower values appear first (default: omitted)
- `catch-open-hierarchy`: (boolean) mark as a Conditional Custom Chapter that intercepts open hierarchy parents before label routing; requires `hierarchy: true` (default: `false`)

```yaml
with:
  chapters: |
    - {"title": "New Features 🎉", "labels": "feature, enhancement", "order": 20}   # multi-label with order
    - {"title": "Bugfixes 🛠️", "label": "bug", "order": 30}                         # legacy single-label with order
    - {"title": "Breaking Changes 💥", "label": "breaking-change", "order": 10}     # rendered first
    - {"title": "Platform 🧱", "labels": ["platform", "infra"]}                      # no order → after ordered chapters
    - {"title": "Internal Notes 📝", "labels": "internal", "hidden": true}           # hidden chapter
    - {"title": "Silent Live 🤫", "catch-open-hierarchy": true}                      # Conditional Custom Chapter
```

## Hidden Chapters

Hidden chapters allow you to define chapters that process records normally but are excluded from the final release notes output.

### Purpose
- Generate draft release notes without deleting chapter definitions
- Adds the benefit of reducing post-editing effort
- Hide work-in-progress or internal sections from stakeholders

### Behavior
When a chapter has `hidden: true`:
- **Processing**: Records ARE assigned to the chapter during population
- **Tracking**: Records in hidden chapters ARE tracked in internal lists
- **Duplicity Detection**: Hidden chapters do NOT count toward duplicity (no 🔔 icon contribution)
- **Output**: Hidden chapters are completely excluded from output rendering
- **Empty Chapter Setting**: `print-empty-chapters` has no effect on hidden chapters (always excluded)

### Examples

**Basic Usage:**
```yaml
chapters: |
  - {"title": "Features 🎉", "labels": "feature"}
  - {"title": "Bugs 🛠", "labels": "bug"}
  - {"title": "Not Implemented ⏳", "labels": "wip", "hidden": true}
  - {"title": "No Release Notes 📝", "labels": "no-rn", "hidden": true}
```

**Duplicity Behavior:**
- Record in 1 visible + 1 hidden chapter → duplicity count = 1 (no icon)
- Record in 2 visible + 1 hidden chapter → duplicity count = 2 (🔔 icon appears)
- Record in 0 visible + 2 hidden chapters → not visible in custom chapters (may appear in service chapters)

### Validation
The `hidden` field accepts:
- Boolean values: `true` or `false`
- Boolean-like strings (case-insensitive): `"true"`, `"True"`, `"false"`, `"False"`
- Invalid values log a warning and default to `false`
- Omitted field defaults to `false`

### Info Logging
When a chapter is marked as hidden, an info-level log message is emitted:
```
Chapter 'Internal Notes 📝' marked as hidden, will not appear in output (but records will be tracked)
```

### Debug Logging
With `verbose: true`, additional debug logging shows:
- Records assigned to hidden chapters with note about duplicity exclusion
- Skipped hidden chapters during rendering with record counts

## Normalization Rules
1. Comma split.
2. Whitespace trimmed per token.
3. Empty tokens discarded.
4. Duplicates removed preserving first occurrence order.
5. If both `label` and `labels` present, `labels` takes precedence (single warning).
6. Invalid types (non-string/non-list) cause chapter skip with a warning.

## Inclusion Logic
A record is added to a chapter if its label set intersects the chapter’s normalized label set. Direct commits are ignored (they have no labels). A record can appear in multiple chapters; intra-chapter duplication is always suppressed.

**Exception — Conditional Custom Chapters:** when `hierarchy: true` and a `catch-open-hierarchy` chapter is defined, all open `HierarchyIssueRecord` parents are routed directly to that chapter _before_ label matching is attempted (subject to the optional label filter on the COH chapter). Label intersection does not apply for that routing decision.

## Deterministic Output
Chapter rendering order is determined as follows:
1. Chapters with an explicit `order` value are rendered first, sorted ascending by `order`.
2. Chapters without `order` follow, preserving the first-seen title order from the YAML input.
3. If multiple chapters share the same `order` value, their relative order is the first-seen title order (tie-breaker).

Without any `order` values, behavior is identical to previous versions (first appearance of each unique title).

### Repeated Title + Order
Repeated titles still represent one logical chapter. Their labels are merged.

- If repeated entries specify the same `order`, that value is used.
- If repeated entries specify conflicting `order` values, the first explicit value is kept and a warning is logged.
- If some entries omit `order` and others provide it, the explicit value is adopted.

## Warnings
- Missing `title`
- Both `label` & `labels` (precedence notice)
- Invalid `labels` type
- Empty label set after normalization
- Unknown extra keys (ignored)
- Invalid `hidden` value type or string
- Invalid `order` value (non-integer); ignored with warning
- Conflicting `order` values for repeated titles; first explicit value kept
- Invalid `catch-open-hierarchy` value type or string; defaults to `false`
- Duplicate `catch-open-hierarchy: true` chapters; only first is used
- `catch-open-hierarchy: true` with `hierarchy: false` at runtime; emitted once per `populate()` call

All warnings include the chapter title (when available) for traceability.

## Verbose Mode
Set `verbose: true` to log normalized label sets at DEBUG level.

## FAQ
**Q: Does `duplicity-scope` stop a record appearing in multiple custom chapters?**  
A: No. Cross-chapter duplication is always allowed; only intra-chapter duplication is suppressed.

**Q: Are labels case-normalized?**  
A: No. Matching is case-sensitive and uses the labels as returned by GitHub.

**Q: How do I merge more labels into an existing heading?**  
Provide multiple entries with the same `title` (legacy style) or just list them in one `labels` definition.

**Q: What if I accidentally leave a trailing comma?**  
Empty tokens are discarded; the chapter remains valid if at least one non-empty token exists.

**Q: Do hidden chapters affect duplicity detection?**  
A: No. Hidden chapters process records but don't increment the chapter presence counter, so they don't contribute to duplicity icons.

**Q: Can I use hidden chapters for draft releases?**  
A: Yes! Mark chapters as `hidden: true` to track changes without showing them in published notes. Switch to `hidden: false` when ready to publish.

**Q: Can an open hierarchy parent appear in both a Conditional Custom Chapter and a normal label chapter?**  
A: No. When a record is intercepted by the `catch-open-hierarchy` gate it is exclusively routed to the Conditional Custom Chapter; normal label matching is skipped entirely for that record. Only closed hierarchy parents and non-hierarchy records go through normal label routing.

## Example Output
```markdown
### New Features 🎉
- #410 _Add inline diff viewer_ developed by @alice in #415

### Bugfixes 🛠
- #412 _Fix cache stampede_ developed by @bob in #418
```

Use this feature to keep release notes concise and logically organized while supporting broader label groupings.

## Conditional Custom Chapter (`catch-open-hierarchy`)

A **Conditional Custom Chapter** intercepts hierarchy issue parents that are still **open**, routing them to a dedicated section (e.g. "Silent Live") instead of the normal label-based chapters. This is useful when a parent Feature spans multiple releases: in-progress work appears under "Silent Live" while the Feature is open, and once it closes it falls back to normal label routing (e.g. "New Features").

### Requirements
- `hierarchy: true` must be enabled. When hierarchy is disabled, `catch-open-hierarchy` is parsed and validated but has no routing effect (a warning is logged).
- At most **one** chapter may set `catch-open-hierarchy: true`. If a second is encountered, a warning is logged and it is ignored.

### Configuration

**Basic — catch all open hierarchy parents:**
```yaml
chapters: |
  - title: "New Features 🎉"
    labels: "feature, epic"
  - title: "Silent Live 🤫"
    catch-open-hierarchy: true
  - title: "Bugfixes 🛠️"
    labels: "bug"
```

**With optional label filter — only intercept open hierarchy parents carrying matching labels:**
```yaml
chapters: |
  - title: "Silent Live 🤫"
    catch-open-hierarchy: true
    labels: "feature, epic"
```

Without `labels`, all open hierarchy parents are captured regardless of their labels.

### Routing Logic
1. For each record, if hierarchy is enabled and a Conditional Custom Chapter exists:
   - If the record is a `HierarchyIssueRecord` **and** the parent issue is **open**:
     - If the chapter has no labels, or the record carries at least one of the chapter's labels → route to the Conditional Custom Chapter and skip normal label routing.
     - Otherwise → fall through to normal label routing.
2. Closed hierarchy parents are never intercepted; they use normal label-based routing.
3. Non-hierarchy records are never affected.

```
For each record:
  ├─ Hierarchy disabled?               → skip gate, use normal label routing
  ├─ Not a HierarchyIssueRecord?       → skip gate, use normal label routing
  ├─ Parent is closed?                 → skip gate, use normal label routing
  └─ Parent is open + COH chapter exists:
       ├─ Chapter has no labels?       → route to COH chapter (exclusive)
       ├─ Record matches a label?      → route to COH chapter (exclusive)
       └─ No label match?             → fall through to normal label routing
```

A record routed to the Conditional Custom Chapter is **never** duplicated into a label chapter — routing is exclusive.

### Combining with `hidden`
A `catch-open-hierarchy` chapter can also be `hidden: true` to silently track open hierarchy parents without printing them.

### Validation
- `catch-open-hierarchy` accepts boolean values (`true`/`false`) and boolean-like strings.
- Invalid values log a warning and default to `false`.
- Duplicate `catch-open-hierarchy: true` chapters are reduced to the first; a warning is logged for the rest.
- When `hierarchy: false`, a warning is logged once at populate time: `"catch-open-hierarchy has no effect when hierarchy is disabled"`.

## Super Chapters

**Super chapters** group regular chapters under higher-level headings based on a separate label. This is useful in monorepo or multi-module projects where the same chapter structure (Features, Bugfixes, …) should appear once per component.

### Configuration

Define super chapters via the `super-chapters` input — a YAML array with `title` and `label`/`labels`:

```yaml
with:
  super-chapters: |
    - title: "Atum Server"
      label: "atum-server"
    - title: "Atum Agent"
      labels: "atum-agent, atum-agent-spark"
  chapters: |
    - {"title": "Enhancements", "label": "enhancement"}
    - {"title": "Bugfixes", "label": "bug"}
```

### Rendering

When super chapters are configured the output uses `##` headings for super chapters and `###` for regular chapters nested inside:

```markdown
## Atum Server
### Enhancements
- #10 _Streaming API_ developed by @alice in #12

### Bugfixes
- #15 _Fix timeout_ developed by @bob in #16

## Atum Agent
### Enhancements
- #20 _Checkpointing_ developed by @carol in #22
```

### Behavior
- A record is placed under a super-chapter if it carries at least one label matching the super-chapter's labels.
- A record can appear in **multiple** super-chapters if its labels match more than one.
- Within each super-chapter, records are routed to regular chapters by the normal label-matching rules.
- Empty super chapters (no matching records) respect the `print-empty-chapters` setting:
  - `print-empty-chapters: true` → header is printed with `No entries detected.`
  - `print-empty-chapters: false` → header is omitted entirely
- `## Uncategorized` is only emitted when there are actually unmatched records; `print-empty-chapters` has no effect on it.
- When no super chapters are configured, output is flat (unchanged from previous behavior).

### Hierarchy Split (with `hierarchy: true`)

With `hierarchy: true`, super-chapter matching uses each hierarchy record's **full aggregated label set** — own labels plus all descendant labels recursively at every depth. So an Epic matches a super chapter even when the relevant label lives only on a grandchild Task (e.g. Epic → Feature → Task).

The record is then split by which descendants belong to which super chapter:

| Descendants | Output |
|---|---|
| All match one super chapter | Record appears in that super chapter only |
| None match any super chapter | Record appears in `## Uncategorized` only |
| Some match, some don't | Record appears in the matching super chapter **and** in `## Uncategorized`, each showing only its own subset |
| Match multiple super chapters | Record appears in each matching super chapter with its relevant subset |
| Match multiple SCs + some unmatched | Record appears in each matching super chapter and in `## Uncategorized` |

#### Example

Epic #1 has Task #2 (`scope:frontend`) and Task #3 (`scope:backend`):

```yaml
super-chapters: |
  - title: "Frontend"
    label: "scope:frontend"
  - title: "Backend"
    label: "scope:backend"
chapters: |
  - {"title": "New Features", "labels": "feature"}
```

```markdown
## Frontend
### New Features
- Epic: _Add user authentication_ #1
  - #2 _Build login form_

## Backend
### New Features
- Epic: _Add user authentication_ #1
  - #3 _Add JWT endpoint_
```

If Epic #1 also had Task #4 with no super-chapter label, it would additionally appear in `## Uncategorized` with only Task #4.

#### 3-level depth

The same split works when the matching label is on a grandchild. Epic #1 → Feature #2 → Task #3 (`scope:security`):

```markdown
## Security
### New Features
- Epic: _Add authentication_ #1
  - Feature: _Auth flow_ #2
    - #3 _Add JWT endpoint_
```

Feature #2 has no `scope:security` label of its own, but its aggregated set includes it via Task #3, so it is routed to the Security super chapter.

Children within each rendered node are sorted **ascending by issue number**.

### Validation
- Non-dict entries are skipped with a warning.
- Entries missing `title` are skipped with a warning.
- Entries where `title` is present but is not a string, or is blank/whitespace-only, are skipped with a warning.
- Entries missing `label`/`labels` are skipped with a warning.
- An invalid `label`/`labels` type (not a string or list) is treated as empty and causes the entry to be skipped with a warning.
- Empty labels after normalization (e.g. only blank tokens) cause the entry to be skipped with a warning.

## Related Features
- [Duplicity Handling](./duplicity_handling.md) – governs multi-chapter visibility.
- [Release Notes Extraction](./release_notes_extraction.md) – provides the change increment lines.
- [Skip Labels](./skip_labels.md) – excluded records never reach chapters.
- [Custom Row Formats](./custom_row_formats.md) – adjusts row templates.
- [Service Chapters](./service_chapters.md) – diagnostics separate from user-defined chapters.

← [Back to Feature Tutorials](../../README.md#feature-tutorials)
