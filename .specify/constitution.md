<!--
Sync Impact Report
Version change: 1.4.0 -> 1.4.1
Modified sections: Core Principles (definitions removed, now reference single source)
Added sections: Principle index reference note
Removed sections: Inlined principle bodies (1–13 presently, truncated set previously embedded)
Change type: PATCH (structural relocation; no semantic governance change)
Templates requiring updates: None (plan/spec/tasks already reference centralized principles) ✅
Deferred TODOs: Consider CI guard to block reintroduction of principle text outside principles.md
-->

# Release Notes Scrapper Action Constitution

## 1. Project Overview

### Purpose
The Release Notes Scrapper Action automatically generates structured, human‑readable Markdown release notes for a GitHub
repository based on issues, pull requests, and commits between two release tags (or last tag and NOW). It is used by
maintainers, release managers, and CI pipelines to standardize release documentation and reduce manual effort.

### Primary Value
- Eliminates manual curation of release notes.
- Enforces consistent chapter categorization via label → chapter mapping.
- Surfaces quality gaps (missing notes, unlabeled work, orphan issues) through service/warning chapters.
- Provides a ready‑to‑publish Markdown block and changelog comparison link.

### Scope (Current Coverage)
Covered capabilities include: data mining of issues/PRs, label categorization, hierarchy expansion (parent/sub‑issues),
release window selection (by tags or published timestamps), duplicate line detection, configurable row formatting,
optional CodeRabbit summary integration, warning/service chapters, and output emission as a composite GitHub Action.

### Ecosystem Context
This is part of AbsaOSS tooling and fits into broader release management automation. It integrates with standard
GitHub Actions workflows and complements release publishing steps (e.g. softprops/action-gh-release). It does not
manage version tagging; it consumes existing tags.

## 2. Architecture Summary

### Core Modules & Boundaries
- `main.py`: Entry point for composite action execution (logging setup, input validation, orchestration).
- `action_inputs.py`: Input parsing/validation from environment (GitHub Action inputs).
- `generator.py` (`ReleaseNotesGenerator`): High-level generation pipeline coordinating mining, filtering, hierarchy,
  record construction, and final Markdown building.
- `data/` (e.g. `miner.py`, `filter.py`): Mining GitHub entities and filtering by release boundaries.
- `builder/ReleaseNotesBuilder`: Assembles final Markdown from record structures and chapters.
- `chapters/` (`custom_chapters.py`, `service_chapters.py`, `base_chapters.py`): Chapter definitions, user-configured
  and service/warning chapter logic.
- `record/` & `model/record/*`: Domain model abstractions for issues, PRs, commits, hierarchy relationships.
- `record/factory/` (`default_record_factory.py`): Translates mined/filter data into standardized record objects.
- `utils/` (logging, rate limiting, GitHub API helpers, formatting utilities).

### External Dependencies (Runtime Libraries)
- PyGithub: GitHub API client abstraction.
- PyYAML: Parsing chapter configuration input (YAML list provided as multiline string input).
- semver: Normalization of version tags.
- requests / urllib3: HTTP under PyGithub.
- Logging / stdlib (mypy, pylint, black used only in dev/CI).

### Control & Data Flow
1. `main.run()` authenticates with GitHub using token → validates inputs.
2. Constructs `CustomChapters` from YAML input.
3. Instantiates `ReleaseNotesGenerator` with GitHub client & chapters.
4. Generator: `DataMiner` mines issues, PRs, commits; `FilterByRelease` filters to release range.
5. If hierarchy enabled: additional sub-issue mining expands dataset.
6. `DefaultRecordFactory` builds normalized `Record` objects keyed by ID.
7. `ReleaseNotesBuilder` iterates chapters → collects matching records → applies row format templates / duplicity markers.
8. Final Markdown string emitted; composite action sets `release-notes` output.

### Boundary Rules (Refined)
- Action inputs boundary: all configurable behavior must pass via declared inputs (no hidden runtime switches).
- GitHub API boundary: all repository data access encapsulated within miner and rate limiter logic.
- Formatting boundary: only row format templates and chapters influence visible line structure; business logic must not
  directly embed presentation markup elsewhere.
- Error boundary: modules MUST NOT leak raw exceptions across boundaries; they must convert failures into logged events
  and structured return values (see PID:F-1). Internal exceptions MAY be raised and caught within the same module.
- Utility boundary: functions in `utils/` MUST be demonstrably used by at least one importing module or removed (see PID:K-2 & PID:G-1).

### Module Boundary Follow-Up
A scheduled audit SHALL verify:
- `utils/` contains only actively referenced functions (dead code removal list to be created).
- `generator.py` remains orchestration-only (no direct formatting or low-level API calls beyond miner invocation).
- `builder/` never performs mining; strictly transforms records to Markdown.
- `record/factory` isolates construction logic; future refactors MAY extract validation into a separate `validators/` module.
- Logging configuration centralization: confirm no duplicate ad-hoc log setup outside `main.py`.
Outcome: Produce a follow-up task list referencing each violation if found; merge only with accompanying unit tests.

## 5. Quality & Testing

### Test Types
- Unit tests for pure utility, transformation, formatting, and record construction functions.
- Integration tests (e.g. `integration_test.py`) covering end-to-end generation using mocked or controlled data.
- Future: contract/snapshot tests MAY be introduced for chapter output stability (not mandatory yet).

### Test Directory Structure (New)
```
tests/
  unit/                # All Python unit tests (test_<module>.py) - REQUIRED location
  integration/         # Future integration tests (current single file may migrate here)
  fixtures/            # Shared static test data & factories (optional)
  helpers/             # Helper utilities used only by tests (must be imported by tests/*)
  release_notes/       # Domain-specific sample data (review for possible move under fixtures/)
  utils/               # Test-only utility functions (rename to helpers/ or remove if redundant)
```
Rules:
- All unit tests MUST reside under `tests/unit/` (root-level `test_*.py` files SHALL be relocated).
- Naming: `test_<target>.py`; multiple related small targets MAY share one file if cohesive.
- Test style: uses ONLY `pytest` (no unittest classes). Prefer functions + fixtures.
- Fixtures: define shared objects in `tests/conftest.py` or per-file fixtures; keep scope minimal.
- Parametrization: use `@pytest.mark.parametrize` for input matrix instead of loops.
- Coverage: new logic MUST raise overall coverage or keep it steady; dropping coverage requires explicit justification.
- NEW: Unit test file path MUST mirror source relative package path (PID:A-2). For source file `release_notes_generator/utils/constants.py`, the test lives at `tests/unit/release_notes_generator/utils/test_constants.py`.
- Branch Naming: Feature / fix / docs / chore PRs MUST originate from correctly prefixed branch (PID:H-1); CI may validate.

### Organization & Integration
- Integration tests MUST import public interfaces only (`main`, `ReleaseNotesGenerator`) not internal private helpers.
- Unit tests MUST avoid real network calls; use mocking or local sample data.
- Cross-test independence: tests MUST NOT rely on execution order; no shared mutation outside fixture scope.
- Relocation of existing root-level unit tests into `tests/unit/` SHALL be part of first compliance PR post-amendment.

### Coverage
- `pytest-cov` integrated; HTML coverage artifacts under `htmlcov/`. Baseline maintained or improved. New core logic MUST
  include tests before implementation (Test‑First Principle).

### Static Analysis & Review
- `pylint`, `mypy` required to pass (configuration present).
- `black` formatting mandatory (line length 120). No manual deviations unless formatter limitations.
- Peer review via GitHub PR required for all non-trivial changes (records, miner, builder, chapter logic).

### Quality Gates (Minimum Acceptance)
- Tests: ALL must pass.
- Lint + type: zero blocking errors.
- No unused functions/methods (see PID:G-1) — introduce usage or delete in same PR.
- Branch naming compliance (PID:H-1) — allowed prefixes: feature/, fix/, docs/, chore/; rename if violated.

## 8. Key Risks & Assumptions

### Risks
- GitHub API rate limits may degrade performance for very large repos (mitigated by `GithubRateLimiter`).
- Invalid or malformed chapters YAML causes empty notes (input validation logs error but proceeds).
- Missing required tag (`tag-name`) leads to failure early; user workflows must create tag first.
- Hierarchy expansion could incur additional API calls increasing latency.
- Duplicate detection edge cases may confuse users if same issue intentionally spans categories.
- CodeRabbit integration features may parse unintended summary content (format variance risk).
- Dead code accumulation in `utils/` may reduce clarity if PID:G-1 not enforced promptly.

### Assumptions
- Repository uses semantic version tags (prefixed optionally by `v`).
- Labels consistently applied to categorize issues/PRs.
- Provided GitHub token has read access to issues/PRs and release metadata.
- Network connectivity stable; transient failures are rare.
- Users supply chapters list or accept service chapters as fallback warnings.

## 9. Governance & Ownership

### Maintainers
- Organization: AbsaOSS.
- Core maintainer: @miroslavpojer (primary).
- Additional maintainers: (pending listing / open for contributors).

### Decision Process
- Minor enhancements (new placeholders, service chapter refinements): require PR approval by ≥1 maintainer.
- Major changes (input rename/removal, architectural refactor) require PR approval by ≥1 maintainer.
- Emergency fixes (critical bug blocking releases) may merge with expedited single maintainer approval + retroactive review.

### Amendment & Versioning Policy
- Constitution changes:
  - MAJOR: Remove or redefine principle; backward incompatible process change.
  - MINOR: Add new principle or expand governance scope materially.
  - PATCH: Clarifications, wording, examples; no semantic change.
- Each amendment updates `Last Amended` date (ISO format) and increments version accordingly.
- All governance PRs MUST reference change rationale and expected impact.

### Compliance Review
- PR template or automated check SHOULD reference Constitution principles (especially Test‑First & Stability) before merge.
- Violations require explicit justification section in PR description.
- Review checklist MUST confirm PID:H-1 prefix correctness and scope alignment.

## 10. Next Steps / Specification Flow

The `/specify → /plan → /tasks` flow documents and plans new enhancements or refactors.

### Workflow
1. Define high-level feature intent (spec) using `.specify/templates/spec-template.md`.
2. Generate implementation plan (fills architecture/context & Constitution Check gates).
3. Derive task list grouped by user story, respecting independence and test-first requirements.
4. Execute tasks; ensure each story provides an independently testable increment.

### Example Commands (conceptual)
```bash
# Generate/refresh feature specification (arguments describe feature)
# speckit.spec "Add GitHub Enterprise domain support"

# Create implementation plan from spec
# speckit.plan specs/001-ghe-domain-support/spec.md

# Generate task list from plan + spec
# speckit.tasks specs/001-ghe-domain-support/
```

Ensure Constitution Check section in `plan.md` passes before advancing to detailed tasks.

## Metrics & Observability
- Logging: Structured Python logging (INFO for lifecycle, DEBUG for detailed records). Verbose mode toggled via input.
- Quality Metrics: Test coverage (HTML artifact), lint/type error count (must be zero blocking), release note generation success rate.
- Operational Metrics (Future): Potential addition of execution time and API call counts for large repositories.

## Change Log / Versioning
- Project releases follow Git tags; this constitution uses semantic versioning independent of code releases.
- Current Constitution Version: 1.4.1 (amended with new principles & test structure).
- Future amendments tracked via Sync Impact Report at top of this file.

## Core Principles

The authoritative principle definitions have been externalized to a single source file:
`/.specify/memory/principles.md`.

Principle PID Index (see `principles.md` for full text):
- PID:A-1 Test‑First Reliability
- PID:B-1 Explicit Configuration Boundaries
- PID:B-2 Deterministic Output Formatting
- PID:C-1 Minimal Surface & Single Responsibility
- PID:C-2 Safe Extensibility
- PID:D-1 Transparency & Observability
- PID:E-1 Resource‑Conscious API Usage & Performance Budgeting
- PID:K-2 Lean Python Design
- PID:F-1 Localized Error Handling & Non‑Exceptional Flow
- PID:G-1 Dead Code Prohibition
- PID:G-2 Focused & Informative Comments
- PID:A-2 Test Path Mirroring
- PID:H-1 Branch Naming Consistency
- PID:K-1 Static Typing Discipline
- PID:G-3 TODO Debt Governance
- PID:I-1 Security & Token Handling
- PID:J-1 Documentation‑Derived Rule Synchronization
- PID:J-2 Example Reuse & Location Discipline

Refer to `principles.md` for full text, rationale, and rule bullets.

## Governance Metadata
**Version**: 1.4.1 | **Ratified**: 2025-10-12 | **Last Amended**: 2025-10-15
