<!--
Sync Impact Report
Version change: 1.5.1 -> 1.6.0
Modified principles: None
Added sections: Principle 17 (Documentation-Derived Rule Synchronization)
Removed sections: None
Templates requiring updates: plan-template.md (✅), spec-template.md (✅), tasks-template.md (✅)
Follow-up TODOs: Implement doc rule scan script (regex normative terms) & add CI job; baseline first scan by 2025-11-01.
-->

# Generate Release Notes Action Constitution

## Core Principles

### Principle 1: Test‑First Reliability
All core logic (mining, filtering, record building, formatting) MUST have failing unit tests written before implementation
and passing after. Refactors MUST preserve existing green tests. No feature merges without unit tests.
Rationale: Prevent regressions & maintain deterministic behavior for CI consumers.

### Principle 2: Explicit Configuration Boundaries
Runtime behavior MUST be controlled only via declared GitHub Action inputs. Hidden flags or undeclared env vars prohibited.
Add inputs → MINOR version bump; rename/remove → MAJOR bump.
Rationale: Ensures predictability & backward compatibility for workflows pinning versions.

### Principle 3: Deterministic Output Formatting
Given identical repository state & inputs, release notes MUST be identical. Ordering MUST be stable (sorted where needed).
Row template placeholders MUST remain consistent (additions allowed; removals require MAJOR bump).
Rationale: Stable diffs & reliable downstream automation (publishing, auditing).

### Principle 4: Minimal Surface & Single Responsibility
Modules stay focused (inputs parsing, mining, building, logging). Cross-cutting concerns (tag creation, external alerts)
are excluded; implement in separate tools/actions. Avoid feature creep.
Rationale: Low maintenance cost & clear mental model.

### Principle 5: Transparency & Observability
Structured logging MUST trace lifecycle: start → inputs validated → mining done → build done → finish. Errors logged with
context; verbose flag unlocks extra diagnostics without altering behavior.
Rationale: Fast debugging in ephemeral CI environments.

### Principle 6: Safe Extensibility
New placeholders, chapters, or hierarchy features MUST default to non-breaking behavior. Provide opt-in flags if impact
uncertain. Document additions in README + release notes.
Rationale: Incremental evolution without destabilizing existing users.

### Principle 7: Resource-Conscious GitHub API Usage & Performance Budgeting
All mining MUST route through rate limiter abstractions and remain within a documented soft performance budget.
Rules:
- Disable hierarchy expansion when feature off to avoid unnecessary calls.
- Avoid redundant fetches (cache IDs once retrieved).
- Verbose runs SHOULD (and CI MAY) log: total API requests, elapsed wall-clock seconds, issues processed, PRs processed, remaining rate limit.
- Soft API call target: ≤ 3 * (issues + PRs) for typical release windows; overages require justification & follow-up optimization task.
- If remaining core rate limit <10% before optional hierarchy expansion, skip hierarchy mining with a warning (do not fail build).
- Performance baselines MUST be periodically (at least once per quarter) captured for representative repositories.
Rationale: Preserves rate limits, ensures predictably fast runtime, and prevents hidden performance regressions.

### Principle 8: Lean Python Design
Prefer pure functions; introduce classes ONLY when stateful behavior or polymorphism required. Avoid deep inheritance;
favor composition. Utility modules keep narrow surface.
Rationale: Improves readability, testability, and reduces accidental complexity.

### Principle 9: Localized Error Handling & Non-Exceptional Flow
Do NOT raise raw exceptions across module boundaries. Catch internally → log → return structured result (empty/partial).
Only unrecoverable initialization failures (e.g., missing auth token) may exit early at entry point.
Rationale: Predictable action completion and clear diagnostics.

### Principle 10: Dead Code Prohibition
Unused functions/methods (except properties or required inherited methods) MUST be removed in same PR that obsoletes them.
Utility files contain ONLY invoked logic. CI or review MUST flag new unused code.
Rationale: Prevents confusion & keeps coverage meaningful.

### Principle 11: Focused & Informative Comments
Comments MUST succinctly explain non-obvious logic, constraints, or workaround rationale. Prohibited: stale, narrative,
speculative, or redundant comments. Maintain or delete on change; never leave outdated intent.
Rationale: Enhances clarity without noise.

### Principle 12: Test Path Mirroring
Unit tests MUST mirror source file paths inside `tests/unit/`:
`release_notes_generator/<subdirs>/file.py` → `tests/unit/release_notes_generator/<subdirs>/test_file.py`.
Rules:
- New tests follow mirroring immediately.
- Grouping multiple source files in one test file requires justification (shared invariant or helper pattern).
- Legacy categorized folders (`tests/release_notes`, `tests/data`, `tests/model`, `tests/utils`) are transitional; migrate gradually without lowering coverage.
Rationale: Streamlines navigation, encourages focused tests, reduces ambiguity in ownership.

### Principle 13: Branch Naming Consistency
All new work branches MUST start with an approved prefix followed by a concise kebab-case descriptor (optional leading numeric ID).
Allowed prefixes (enforced):
- `feature/`  → Feature & enhancement work introducing new capability or non-trivial behavior
- `fix/`      → Bug fixes addressing defects (issues labeled bug/error)
- `docs/`     → Documentation-only changes (README, docs/, CONTRIBUTING, DEVELOPER guides)
- `chore/`    → Maintenance, dependency updates, CI adjustments, refactors without behavioral change
Examples:
- `feature/add-hierarchy-support`, `feature/123-hierarchy-support`
- `fix/456-null-pointer-on-empty-labels`
- `docs/improve-hierarchy-guide`
- `chore/update-pylint-config`
Rules:
- Prefix MUST be one of the allowed set; otherwise branch renamed before PR.
- Descriptor: lowercase kebab-case; hyphens only; no spaces/underscores/trailing slash.
- Optional numeric ID may precede description: `fix/987-label-trim`.
- Avoid vague terms (`update`, `changes`); state intent (`improve-logging`, `relabel-duplicate-detection`).
- Forbidden: mixing categories, uppercase, camelCase.
- Scope alignment: PR description MUST align with chosen prefix category.
Rationale: Enables automated classification, clearer history semantics, and supports CI policy enforcement.

### Principle 14: Static Typing Discipline
All production modules MUST be fully type-checked with `mypy` (no silent exclusion beyond legacy transitional areas explicitly documented).
Rules:
- New code MAY NOT introduce `# type: ignore` without inline justification.
- Broad `Any` disallowed unless interacting with third-party library lacking stubs (justify in PR).
- Progressive enforcement: expand mypy coverage to tests by 2025-11-01 (create issue if deadline adjustment needed).
Rationale: Early defect detection, self-documenting APIs, safer refactors.

### Principle 15: TODO Debt Governance
Inline `TODO` (or `FIXME`) MUST include an issue reference (`#<id>`). Format: `# TODO(<issue-id>|<tracking-tag>): <action>`.
Rules:
- Missing issue link blocks merge (unless converted immediately to issue during review).
- TODO lifetime max: 2 MINOR releases; aged TODOs trigger escalation issue.
- Deprecated TODO replaced by comment removal OR fixed code in same PR.
Rationale: Prevents silent entropy & ensures planned remediation of technical debt.

### Principle 16: Security & Token Handling
No secrets or token fragments MAY be logged (even at DEBUG). Environment access limited to documented inputs.
Rules:
- Mask potentially sensitive substrings when logging dynamic user inputs.
- Dependencies updated under `chore/` branches; review for supply chain risk (pin versions in requirements files).
- Introduce new external services ONLY with explicit README threat notes (data sent, retention, opt-in flag).
Rationale: Protects consumers using default GITHUB_TOKEN and mitigates leakage risk.

### Principle 17: Documentation‑Derived Rule Synchronization
Normative statements (MUST/SHOULD/SHALL/REQUIRED) introduced or changed in project Markdown docs (e.g., `README.md`,
`CONTRIBUTING.md`, `DEVELOPER.md`, any `docs/**/*.md`) MUST be reconciled with this constitution & templates.
Rules:
- Every PR modifying *.md files that adds/changes normative language MUST include one of:
  1. “Aligns with existing Principle X” (explicit reference), OR
  2. A Constitution amendment (new/updated principle), OR
  3. Justification that wording is purely explanatory (no new rule) using phrase: `NON-NORMATIVE` in PR description.
- If conflict between doc text and a principle arises, the constitution prevails until amended; PR MUST either patch docs or amends principles in same PR.
- Introduced process steps (e.g., ��run script X before commit”) MUST appear in: (a) constitution governance or quality gates section, OR (b) tasks template if feature-scoped.
- A Doc Rule Scan Script (planned) parses changed Markdown lines for regex: `\b(MUST|SHOULD|SHALL|REQUIRED)\b` and fails CI unless reconciliation note present.
- Template Propagation: When new normative doc rule is adopted, update: plan-template Constitution Check, spec-template alignment bullets, tasks-template path/quality gates.
- Quarterly Audit: Run scan across repo; produce report listing normative statements without principle references; open issues for each orphan.
Rationale: Prevents silent drift between contributor docs and enforceable governance; ensures single source of truth & predictable automation.

## Quality & Testing

- Test Directory Structure:
  - tests/unit/: All unit tests (test_<module>.py) — required location.
  - tests/integration/: End-to-end tests (integration_test.py to be migrated here when reorganized).
  - tests/fixtures/: Optional static data samples.
  - tests/helpers/ & tests/utils/: Test-only helpers.
- Framework: pytest ONLY.
- Coverage: Enforce threshold ≥80% (uses --cov-fail-under=80). New logic must keep or raise coverage.
- Independence: Tests MUST not depend on execution order or mutate global state beyond fixture scope.
- Parametrization: Use @pytest.mark.parametrize instead of manual loops.
- Integration tests import public interfaces only.
- Failing tests are written first (Principle 1) for new core logic.
- Path mirroring (Principle 12) enforced for all new/changed modules.
- Branch naming check enforced (Principle 13).
- Typing coverage gate (Principle 14).
- TODO audit gate (Principle 15).
- Performance summary logged in verbose mode (Principle 7) when enabled.
- Documentation rule sync: PR review checklist confirms Principle 17 compliance for any *.md normative additions.

## Workflow & Quality Gates

Pre-merge mandatory local (and CI) gates:
1. Formatting: black --check (line length 120).
2. Linting: pylint global score ≥9.5 (no fatal errors).
3. Typing: mypy (0 blocking errors); justify new ignores.
4. Tests: pytest all green.
5. Coverage: ≥80% overall; justify any temporary dip.
6. Dead Code: remove or justify.
7. Determinism: repeat test run yields identical sample output.
8. Branch Naming: enforced allowed prefix.
9. TODO Governance: all TODOs issue-linked & within lifetime window.
10. Performance Budget (when verbose/perf job active): API call soft target evaluation (Principle 7).
11. Documentation Rule Sync: normative doc changes reconciled per Principle 17.

Quality Gate Failure Handling:
- Minor failures (formatting, lint) → immediate fix; no waivers unless urgent hotfix.
- Coverage dip → explicit justification + recovery issue.
- Non-deterministic output → BLOCKING.
- Branch naming violation → BLOCKING until renamed.
- TODO governance failure → BLOCKING (fix or link issue).
- Performance overrun → CONDITIONAL (document + follow-up optimization task) unless causing timeouts → BLOCKING.
- Documentation rule sync failure → BLOCKING until reconciliation (add amendment or clarify NON-NORMATIVE).

## Governance

- Constitution supersedes ad-hoc practices; PRs MUST state compliance or list justified exceptions.
- Versioning (this constitution): Semantic (MAJOR.MINOR.PATCH).
  - MAJOR: Remove/redefine a principle or backward incompatible process change.
  - MINOR: Add new principle/section or materially expand guidance.
  - PATCH: Clarifications, numbering/order corrections, non-semantic wording.
- Amendment Flow:
  1. Propose change with rationale & impact assessment.
  2. Update Sync Impact Report header (include affected templates & TODOs).
  3. Bump version according to rule above.
  4. Obtain ≥1 maintainer approval (emergency fixes allow post-hoc review).
- Compliance Review: PR template SHOULD reference Principles 1, 2, 7, 10, 12, 13, 14, 15, 17 + coverage threshold.
- Backward Compatibility: Input names & placeholder semantics require MAJOR bump if changed.
- Enforcement: CI automates formatting, lint, typing, tests, coverage, branch prefix, TODO lint, and optional performance logging.

**Version**: 1.6.0 | **Ratified**: 2025-10-12 | **Last Amended**: 2025-10-15
