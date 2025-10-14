<!--
Sync Impact Report
Version change: 1.3.0 -> 1.4.0
Modified sections: Principle 13 expanded to include fix/, docs/, chore/; Quality Gates branch naming; Compliance Review
Added sections: Allowed prefix list & category descriptions; CI workflow enforcement `.github/workflows/branch-prefix-check.yml`
Removed sections: None
Change type: MINOR (expanded enforceable governance rule)
Templates requiring updates: plan-template.md (✅), tasks-template.md (✅), spec-template.md (✅), DEVELOPER.md (✅), CONTRIBUTING.md (✅), branch-prefix-check.yml (✅)
Deferred TODOs: None
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
  and structured return values (see Principle 9). Internal exceptions MAY be raised and caught within the same module.
- Utility boundary: functions in `utils/` MUST be demonstrably used by at least one importing module or removed (see Principle 8 & 10).

### Module Boundary Follow-Up
A scheduled audit SHALL verify:
- `utils/` contains only actively referenced functions (dead code removal list to be created).
- `generator.py` remains orchestration-only (no direct formatting or low-level API calls beyond miner invocation).
- `builder/` never performs mining; strictly transforms records to Markdown.
- `record/factory` isolates construction logic; future refactors MAY extract validation into a separate `validators/` module.
- Logging configuration centralization: confirm no duplicate ad-hoc log setup outside `main.py`.
Outcome: Produce a follow-up task list referencing each violation if found; merge only with accompanying unit tests.

## 3. Data & Integrations

### Key Inputs
- Environment variables prefixed with `INPUT_` (GitHub Action input mapping) including: tag-name, from-tag-name,
  chapters YAML, duplicity scope/icon, hierarchy flag, published-at flag, skip-release-notes-labels, row-format patterns,
  CodeRabbit toggles, verbose/debug flags.
- GitHub repository identifier (owner/name) and token.

### Key Outputs
- Single Markdown block (string) under the GitHub Action output name `release-notes`.
- Optional service/warning chapter sections (embedded within same Markdown).
- Changelog comparison URL derived from tags.

### Data Formats
- Chapters Input: YAML array string (each item `{title: str, label: str}`) supplied via multiline input.
- Row Formats: Template strings with placeholders `{number}`, `{title}`, `{developers}`, etc. Case-insensitive.
- Output: Markdown (headings + bullet/line entries).
- Tags: Semantic version strings normalized (e.g. `v1.2.3`).

### External APIs & Services
- GitHub REST (via PyGithub) for issues, pull requests, commits, release metadata.
- Optional CodeRabbit summary (if enabled) parsed from PR bodies; no direct external API calls here unless present in
  future extension (current code references textual extraction only).

### Persistence & Configuration
- No persistent external storage: all operations in-memory per invocation.
- Configuration solely via action inputs; no config file required beyond runtime `.github/workflows/*.yml` usage.

## 4. Workflows & CI/CD

### Build & Packaging
- Composite GitHub Action (no container image). Creates local virtual environment, installs `requirements.txt`.
- Python version gate: MUST be ≥ 3.11 (enforced in `action.yml` step).

### Automation
- Continuous Integration expected to run `pytest` + coverage.
- Formatting: `black` (line length 120), static typing: `mypy`, lint: `pylint`.

### Deployment
- Distributed via GitHub Marketplace release tags (e.g. `AbsaOSS/generate-release-notes@v1`).
- Consumers pin version tags for stability; internal changes require semantic release tagging.

### Environments
- Primary: GitHub-hosted runners (Ubuntu). Local development: any OS with Python 3.11+.

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
- NEW: Unit test file path MUST mirror source relative package path (Principle 12). For source file `release_notes_generator/utils/constants.py`, the test lives at `tests/unit/release_notes_generator/utils/test_constants.py`.
- Branch Naming: Feature / fix / docs / chore PRs MUST originate from correctly prefixed branch (Principle 13); CI may validate.

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
- No unused functions/methods (see Principle 10) — introduce usage or delete in same PR.
- Backward compatibility: no silent change to input names or placeholder semantics without version bump & documentation update.
- Branch naming compliance (Principle 13) — allowed prefixes: feature/, fix/, docs/, chore/; rename if violated.

## 6. Constraints & Compatibility

### Platform & Language
- Python: 3.11+ ONLY (action enforces). Future expansion to newer minor versions allowed if test matrix passes.
- OS: GitHub Ubuntu runners officially supported; macOS/Linux local dev assumed; Windows not primary (should function but not guaranteed).

### Backward Compatibility
- Input names are stable; modification/removal requires MAJOR version bump.
- Row format placeholder set must not shrink without MAJOR bump; additions allowed under MINOR.
- Service chapter semantics must remain predictable; new service chapters = MINOR bump.

### Licensing & Organizational
- Apache 2.0 license; contributions MUST comply and include license headers in new Python files.
- No proprietary dependencies; all third-party libraries are OSS.

## 7. Non-Goals
- Managing or creating Git tags/releases (handled by other actions like softprops/action-gh-release).
- Multi-repository or cross-project aggregation of release notes.
- Persistent storage of historical notes beyond generated output.
- Automatic labeling, triage, or issue/PR mutation.
- Security scanning or dependency auto-updates (Dependabot recommended separately).
- Full changelog generation beyond link and categorized notes (raw diff content not embedded).

## 8. Key Risks & Assumptions

### Risks
- GitHub API rate limits may degrade performance for very large repos (mitigated by `GithubRateLimiter`).
- Invalid or malformed chapters YAML causes empty notes (input validation logs error but proceeds).
- Missing required tag (`tag-name`) leads to failure early; user workflows must create tag first.
- Hierarchy expansion could incur additional API calls increasing latency.
- Duplicate detection edge cases may confuse users if same issue intentionally spans categories.
- CodeRabbit integration features may parse unintended summary content (format variance risk).
- Dead code accumulation in `utils/` may reduce clarity if Principle 10 not enforced promptly.

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
- Review checklist MUST confirm Principle 13 prefix correctness and scope alignment.

### Release Management
- Tagging strategy external; this action consumes tags. Recommend semantic versioning for repository releases.
- Breaking changes documented in release notes + README update.

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
- Current Constitution Version: 1.4.0 (amended with new principles & test structure).
- Future amendments tracked via Sync Impact Report at top of this file.

## Core Principles

### Principle 1: Test‑First Reliability
All core logic (mining, filtering, record building, formatting) MUST have failing tests written before implementation and
passing after. New features without tests SHALL NOT merge. Refactors must preserve existing test suite green state.
Rationale: Prevent regressions & ensure deterministic behavior for CI consumers.

### Principle 2: Explicit Configuration Boundaries
All runtime behavior MUST be driven by declared GitHub Action inputs. Hidden flags or reliance on undeclared environment
variables is prohibited. Additions go through MINOR version bumps. Removals/renames require MAJOR.
Rationale: Predictable automation & backward compatibility for consumers pinning versions.

### Principle 3: Deterministic Output Formatting
Row templates and chapter ordering MUST produce repeatable output given identical repository state & inputs.
Non-deterministic ordering (e.g. unordered sets) MUST be normalized (e.g. stable sorting). Markdown headings MUST follow
established pattern for readability.
Rationale: Stable diffs and reliable downstream consumption (e.g. release publishing actions).

### Principle 4: Minimal Surface & Single Responsibility
Modules MUST remain focused (input parsing, mining, building). Introducing cross-cutting logic (e.g. tag creation,
external notifications) within this action is prohibited; such features require separate tools or integrations.
Rationale: Keeps maintenance effort low and reduces risk of feature creep obscuring core value.

### Principle 5: Transparency & Observability
Logging MUST clearly trace generation lifecycle (start, inputs validated, mining complete, build complete). Errors and
validation failures MUST be explicit. Verbose mode extends diagnostics without changing functional behavior.
Rationale: Facilitates debugging in ephemeral CI environments.

### Principle 6: Safe Extensibility
New placeholders, service chapters, or hierarchy expansions MUST not break existing users. Provide default values/flags
for new features (opt-in unless clearly safe). Document changes in README and release notes.
Rationale: Encourages evolution without destabilizing automation pipelines.

### Principle 7: Resource-Conscious GitHub API Usage
Mining MUST use rate limiter abstraction; avoid redundant API calls (e.g. re-fetching unchanged issues). Hierarchy fetches
MUST short-circuit when disabled. Performance considerations addressed before accepting features that multiply API calls.
Rationale: Preserves quota & improves speed on large repositories.

### Principle 8: Lean Python Design
Prefer simple functions and modules over unnecessary classes. A class MUST only be introduced when stateful behavior or
polymorphism is required. Utility modules SHOULD expose pure functions. Avoid deep inheritance; favor composition.
Rationale: Reduces complexity and improves readability & testability.

### Principle 9: Localized Error Handling & Non-Exceptional Flow
Modules MUST catch internal exceptions and convert them into structured return values plus logged messages. Cross-module
exception propagation (raising raw exceptions across boundaries) is prohibited except for truly unrecoverable setup
failures at the entry point (`main`). Return either a valid result or a clearly logged empty/partial result.
Rationale: Ensures predictable action behavior and prevents silent termination in CI pipelines.

### Principle 10: Dead Code Prohibition
No unused methods/functions SHALL remain in the codebase (properties or inherited abstract/interface methods excepted).
Utility files MUST contain only actively invoked functions. Removal of unused code MUST occur in the same PR that
introduces its obsolescence.
Rationale: Prevents confusion, reduces maintenance overhead, and keeps coverage meaningful.

### Principle 11: Focused & Informative Comments
Comments MUST explain non-obvious logic, constraints, or reasoning succinctly. Prohibited: narrative, outdated, or
speculative comments. Allowed: brief context before complex loops, rationale for workaround, links to issue references.
Comments SHOULD be maintained or updated alongside code changes; stale comments MUST be removed.
Rationale: Enhances clarity without adding noise.

### Principle 12: Test Path Mirroring
Each unit test file MUST reside under `tests/unit/` mirroring the source package path and file name: `tests/unit/<source_root_relative_path>/test_<original_file_name>.py`.
Mandatory Rules:
- One test file per source file unless tightly coupled logic demands grouping (justify in PR).
- Legacy non-mirrored category folders are deprecated; migrate incrementally without reducing coverage.
- New or refactored modules require mirrored test path in same PR.
Rationale: Ensures predictable test discovery, simplifies navigation between code and tests, and supports scalable refactors.

### Principle 13: Branch Naming Consistency
All new branches for work MUST start with one of the approved prefixes followed by a concise kebab-case descriptor (optional numeric ID).
Approved prefixes:
- `feature/` – new features & enhancements
- `fix/` – bug fixes / defect resolutions
- `docs/` – documentation-only updates
- `chore/` – maintenance, dependency bumps, CI, non-behavioral refactors
Examples:
`feature/add-hierarchy-support`, `fix/567-handle-empty-chapters`, `docs/improve-readme-start`, `chore/upgrade-semver-lib`
Rules:
- Prefix REQUIRED and MUST be in approved set; rename non-compliant branches prior to PR.
- Descriptor: lowercase kebab-case; hyphen separators; no spaces/underscores/trailing slash.
- Optional numeric ID may precede description (`fix/987-null-title`).
- Category alignment: branch prefix MUST match primary scope of PR contents.
- Avoid vague descriptors (`update`, `changes`). Prefer action or subject (`improve-logging`, `remove-dead-code`).
Rationale: Standardizes history, enables automated governance checks, clarifies intent for reviewers & tooling.

## Governance Metadata
**Version**: 1.4.0 | **Ratified**: 2025-10-12 | **Last Amended**: 2025-10-14
