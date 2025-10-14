<!--
Sync Impact Report
Version change: 1.1.0 -> 1.2.0
Modified principles: Added Principle 12 (Test Path Mirroring)
Added sections: Expanded Test Directory Structure rules with mirroring requirement
Removed sections: None
Templates requiring updates: plan-template.md (✅), tasks-template.md (✅), spec-template.md (✅)
Deferred TODOs: Migrate legacy categorized test folders to mirrored paths
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

### Principle 7: Resource-Conscious GitHub API Usage
All mining MUST route through rate limiter abstractions. Disable hierarchy expansion when feature off. Avoid redundant
fetches (cache IDs once retrieved). Performance concerns addressed before merging API-heavy features.
Rationale: Preserves rate limits & improves speed.

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
Speculative, or redundant comments. Maintain or delete on change; never leave outdated intent.
Rationale: Enhances clarity without noise.

### Principle 12: Test Path Mirroring
Unit tests MUST mirror source file paths inside `tests/unit/`:
`release_notes_generator/<subdirs>/file.py` → `tests/unit/release_notes_generator/<subdirs>/test_file.py`.
Rules:
- New tests follow mirroring immediately.
- Grouping multiple source files in one test file requires justification (shared invariant or helper pattern).
- Legacy categorized folders (`tests/release_notes`, `tests/data`, `tests/model`, `tests/utils`) are transitional; migrate gradually without lowering coverage.
Rationale: Streamlines navigation, encourages focused tests, reduces ambiguity in ownership.

## Quality & Testing

- Test Directory Structure:
  - tests/unit/: All unit tests (test_<module>.py) — required location.
  - tests/integration/: End-to-end tests (integration_test.py to be migrated here when reorganized).
  - tests/fixtures/: Optional static data samples.
  - tests/helpers/ & tests/utils/: Test-only helpers (utils may merge into helpers).
- Framework: pytest ONLY (no unittest classes).
- Coverage: Enforce threshold ≥80% (existing command uses --cov-fail-under=80). New logic must keep or raise coverage.
- Independence: Tests MUST not depend on run order or mutate shared global state beyond fixture scope.
- Parametrization: Use @pytest.mark.parametrize instead of manual loops.
- Integration tests import public interfaces only (e.g., main entry, generator class).
- Failing tests are written first (Principle 1) for new core logic.
- NEW: Path mirroring (Principle 12) enforced for all new/changed modules.
- Transitional Migration Plan: Add tasks in upcoming PRs to relocate remaining categorized tests.

## Workflow & Quality Gates

Pre-merge local mandatory checkers (from DEVELOPER.md):
1. Formatting: black --check (line length 120 per pyproject.toml).
2. Linting: pylint global score target ≥9.5 (no fatal errors).
3. Typing: mypy (0 blocking errors) — treat Any proliferation as smell (justify if unavoidable).
4. Tests: pytest all green.
5. Coverage: ≥80% overall; justify any temporary dip (must be recovered within next PR).
6. Dead Code: grep for unused utilities; remove or reference usage in same PR.
7. Determinism: (Manual) Validate repeated runs produce identical output for sample dataset.

Quality Gate Failure Handling:
- Minor failures (formatting, lint) → fix immediately; do not merge with waivers unless urgent hotfix.
- Coverage dip → requires explicit justification + recovery plan (link issue ID).
- Non-deterministic output → BLOCKING until resolved.

## Governance

- Constitution supersedes ad-hoc practices; PRs MUST state compliance or list justified exceptions.
- Versioning (this constitution): Semantic (MAJOR.MINOR.PATCH).
  - MAJOR: Remove/redefine a principle or backward incompatible process change.
  - MINOR: Add new principle/section (current change qualifies here).
  - PATCH: Clarifications/typos with no semantic effect.
- Amendment Flow:
  1. Propose change with rationale & impact assessment.
  2. Update Sync Impact Report header (include affected templates & TODOs).
  3. Bump version according to rule above.
  4. Obtain maintainer approval (≥1) — emergency fixes allow retroactive review.
- Compliance Review: PR template SHOULD reference Principles 1 (Test‑First), 2 (Configuration Boundaries), 10 (Dead Code),
  and coverage threshold. Reviewers reject if principles violated without justification.
- Backward Compatibility: Input names & placeholder semantics require MAJOR bump if changed.
- Enforcement: CI pipeline SHOULD automate black, pylint, mypy, pytest, coverage threshold; manual deterministic checks remain.

**Version**: 1.2.0 | **Ratified**: 2025-10-12 | **Last Amended**: 2025-10-14
