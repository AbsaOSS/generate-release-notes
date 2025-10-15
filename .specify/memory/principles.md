# Core Principles

> Source of truth for all governance principles. Referenced by `constitution.md`.
> 
> Categories introduced to enable reuse across multi-language projects while preserving existing principle numbering history (historical global numbers removed from headings for clarity; see optional legacy reference appendix if reintroduced later).

- [A. Testing & Quality](#a-testing--quality)
- [B. Configuration & Determinism](#b-configuration--determinism)
- [C. Architecture & Extensibility](#c-architecture--extensibility)
- [D. Observability & Diagnostics](#d-observability--diagnostics)
- [E. Performance & Resource Efficiency](#e-performance--resource-efficiency)
- [F. Error Handling & Resilience](#f-error-handling--resilience)
- [G. Code Hygiene & Technical Debt](#g-code-hygiene--technical-debt)
- [H. Workflow & Version Control](#h-workflow--version-control)
- [I. Security & Compliance](#i-security--compliance)
- [J. Documentation & Knowledge Management](#j-documentation--knowledge-management)
- [K. Python Specific](#k-python-specific)

---

## A. Testing & Quality

### Principle 1: Test‑First Reliability [PID:A-1]
All core logic (mining, filtering, record building, formatting) MUST have failing unit tests written before implementation
and passing after. Refactors MUST preserve existing green tests. No feature merges without unit tests.
Rationale: Prevent regressions & maintain deterministic behavior for CI consumers.

### Principle 2: Test Path Mirroring [PID:A-2]
Unit tests MUST mirror source file paths inside `tests/unit/`:
- `release_notes_generator/<subdirs>/file.py` -> `tests/unit/release_notes_generator/<subdirs>/test_file.py`.

Rules:
- New tests follow mirroring immediately.
- Grouping multiple source files in one test file requires justification (shared invariant or helper pattern).
- Legacy categorized folders (`tests/release_notes`, `tests/data`, `tests/model`, `tests/utils`) are transitional; migrate gradually without lowering coverage.
Rationale: Streamlines navigation, encourages focused tests, reduces ambiguity in ownership.

### Principle 3: Minimal Narrative in Test Code [PID:A-3]
Unit test files MUST NOT include narrative or changelog-style comments describing the “latest change”, PR summary, or
revision history. Tests SHOULD communicate intent purely through:
- Descriptive test function / fixture names
- Clear given/when/then structure in code (optionally via blank line grouping)
- Focused inline comments ONLY for non-obvious setup or domain invariants
Rules:
- Prohibited: headers like `# Added in PR #123 to fix bug`, `# Latest changes`, or date-stamped change notes.
- Historical rationale belongs in commit messages / PR description, not test bodies.
- If a complex regression scenario requires context, use a concise comment referencing the issue/PR ID: `# Regression for issue #456: ensures empty label list handled`.
- Reviewers MUST remove or request removal of narrative/changelog comments during PR review.
Rationale: Keeps tests evergreen, avoids obsolete commentary, and relies on version control for history.

### Principle 4: No Ephemeral Change Comments in Tests [PID:A-4]
Unit tests MUST NOT contain comments that describe recent changes, temporary states, or migration notes (e.g., “updated after refactor”, “temporary workaround”); tests express enduring behavior only.
Rules:
- Allowed comments: clarify domain intent, non-obvious fixture setup rationale, edge-case justification.
- Prohibited markers: dates, “recent”, “new”, “temporary”, “after fix”, commit hashes unless part of a reproducible fixture.
- Historical context belongs in PR descriptions or issue threads.
Rationale: Ensures tests stay evergreen specifications (complements PID:A-3 with explicit examples of banned phrasing).
Anti‑Patterns:
- `# Latest change: adjusted threshold from 3 to 2` → rename test or assert logic; rely on VCS for history.
- `# Temporary until bug #123 fixed` (without failing test representing bug) → encode expectation or open issue.

---

## B. Configuration & Determinism

### Principle 1: Explicit Configuration Boundaries [PID:B-1]
Runtime behavior MUST be controlled only via declared GitHub Action inputs. Hidden flags or undeclared env vars prohibited.
Add inputs → MINOR version bump; rename/remove → MAJOR bump.
Rationale: Ensures predictability & backward compatibility for workflows pinning versions.

### Principle 2: Deterministic Output Formatting [PID:B-2]
Given identical repository state & inputs, release notes MUST be identical. Ordering MUST be stable (sorted where needed).
Row template placeholders MUST remain consistent (additions allowed; removals require MAJOR bump).
Rationale: Stable diffs & reliable downstream automation (publishing, auditing).

---

## C. Architecture & Extensibility

### Principle 1: Minimal Surface & Single Responsibility [PID:C-1]
Modules stay focused (inputs parsing, mining, building, logging). Cross-cutting concerns (tag creation, external alerts)
are excluded; implement in separate tools/actions. Avoid feature creep.
Rationale: Low maintenance cost & clear mental model.

### Principle 2: Safe Extensibility [PID:C-2]
New placeholders, chapters, or hierarchy features MUST default to non-breaking behavior. Provide opt-in flags if impact
uncertain. Document additions in README + release notes.
Rationale: Incremental evolution without destabilizing existing users.

---

## D. Observability & Diagnostics

### Principle 1: Transparency & Observability [PID:D-1]
Structured logging MUST trace lifecycle: start → inputs validated → mining done → build done → finish. Errors logged with
context; verbose flag unlocks extra diagnostics without altering behavior.
Rationale: Fast debugging in ephemeral CI environments.

---

## E. Performance & Resource Efficiency

### Principle 1: Resource-Conscious GitHub API Usage & Performance Budgeting [PID:E-1]
All mining MUST route through rate limiter abstractions and remain within a documented soft performance budget.
Rules:
- Disable hierarchy expansion when feature off to avoid unnecessary calls.
- Avoid redundant fetches (cache IDs once retrieved).
- Verbose runs SHOULD (and CI MAY) log: total API requests, elapsed wall-clock seconds, issues processed, PRs processed, remaining rate limit.
- Soft API call target: ≤ 3 * (issues + PRs) for typical release windows; overages require justification & follow-up optimization task.
- If remaining core rate limit <10% before optional hierarchy expansion, skip hierarchy mining with a warning (do not fail build).
- Performance baselines MUST be periodically (at least once per quarter) captured for representative repositories.
Rationale: Preserves rate limits, ensures predictably fast runtime, and prevents hidden performance regressions.

---

## F. Error Handling & Resilience

### Principle 1: Localized Error Handling & Non-Exceptional Flow [PID:F-1]
Do NOT raise raw exceptions across module boundaries. Catch internally → log → return structured result (empty/partial).
Only unrecoverable initialization failures (e.g., missing auth token) may exit early at entry point.
Rationale: Predictable action completion and clear diagnostics.

---

## G. Code Hygiene & Technical Debt

### Principle 1: Dead Code Prohibition [PID:G-1]
Unused functions/methods (except properties or required inherited methods) MUST be removed in same PR that obsoletes them.
Utility files contain ONLY invoked logic. CI or review MUST flag new unused code.
Rationale: Prevents confusion & keeps coverage meaningful.

### Principle 2: Focused & Informative Comments [PID:G-2]
Comments MUST succinctly explain non-obvious logic, constraints, or workaround rationale. Prohibited: stale, narrative,
speculative, or redundant comments. Maintain or delete on change; never leave outdated intent.
Rationale: Enhances clarity without noise.

### Principle 3: TODO Debt Governance [PID:G-3]
Inline `TODO` (or `FIXME`) MUST include an issue reference (`#<id>`). Format: `# TODO(<issue-id>|<tracking-tag>): <action>`.
Rules:
- Missing issue link blocks merge (unless converted immediately to issue during review).
- TODO lifetime max: 2 MINOR releases; aged TODOs trigger escalation issue.
- Deprecated TODO replaced by comment removal OR fixed code in same PR.
Rationale: Prevents silent entropy & ensures planned remediation of technical debt.

### Principle 4: Comment Retention & Context Preservation [PID:G-4]
Do NOT remove a still-valid explanatory comment (design rationale, workaround explanation, domain constraint) unless:
1. The underlying code it clarifies is removed or refactored so the comment is no longer accurate; OR
2. The comment’s information has been relocated to a more canonical place (e.g., module docstring or README section) and an inline pointer is left if needed.
Rules:
- Deleting a comment that explains a non-obvious algorithm / tradeoff MUST be justified in the PR description if the logic remains.
- Transformational refactors SHOULD migrate still-relevant rationale comments alongside the code.
- “Noise” comments (restating the obvious) MAY still be removed per PID:G-2; this principle protects only semantically valuable context.
- When replacing a complex comment with clearer code, add a short note in the PR: “Obsoleted prior rationale comment by simplification.”
Rationale: Prevents loss of institutional knowledge & avoids archaeology in old commits for active logic.

### Principle 5: Supportive Comment Retention [PID:G-5]
Supportive (context-carrying) inline comments MUST remain in the codebase until their rationale expires (logic removed, constraint obsolete, or superseded docstring). This extends PID:G-4 with explicit retention guidance for rationale-bearing transient workaround notes.
Rules:
- Before removing, confirm comment content is either (a) obsolete, (b) migrated to a more canonical location, or (c) superseded by clearer code.
- PRs removing such comments SHOULD mention the replacement context (e.g., “Replaced with clearer function name”).
- Retain comments explaining external API quirks, domain invariants, or historical edge cases still enforced by tests.
Rationale: Prevents reintroduction of previously solved issues and preserves institutional knowledge.
Anti‑Patterns:
- Deleting a comment solely to reduce line count.
- Replacing a specific rationale with a vague commit message lacking detail.

---

## H. Workflow & Version Control

### Principle 1: Branch Naming Consistency [PID:H-1]
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

---

## I. Security & Compliance

### Principle 1: Security & Token Handling [PID:I-1]
No secrets or token fragments MAY be logged (even at DEBUG). Environment access limited to documented inputs.
Rules:
- Mask potentially sensitive substrings when logging dynamic user inputs.
- Dependencies updated under `chore/` branches; review for supply chain risk (pin versions in requirements files).
- Introduce new external services ONLY with explicit README threat notes (data sent, retention, opt-in flag).
Rationale: Protects consumers using default GITHUB_TOKEN and mitigates leakage risk.

---

## J. Documentation & Knowledge Management

### Principle 1: Documentation‑Derived Rule Synchronization [PID:J-1]
Normative statements (MUST/SHOULD/SHALL/REQUIRED) introduced or changed in project Markdown docs (e.g., `README.md`,
`CONTRIBUTING.md`, `DEVELOPER.md`, any `docs/**/*.md`) MUST be reconciled with this constitution & templates.
Rules:
- Every PR modifying *.md files that adds/changes normative language MUST include one of:
  1. “Aligns with existing Principle X” (explicit reference), OR
  2. A Constitution amendment (new/updated principle), OR
  3. Justification that wording is purely explanatory (no new rule) using phrase: `NON-NORMATIVE` in PR description.
- If conflict between doc text and a principle arises, the constitution prevails until amended; PR MUST either patch docs or amends principles in same PR.
- Introduced process steps (e.g., “run script X before commit”) MUST appear in: (a) constitution governance or quality gates section, OR (b) tasks template if feature-scoped.
- A Doc Rule Scan Script (planned) parses changed Markdown lines for regex: `\b(MUST|SHOULD|SHALL|REQUIRED)\b` and fails CI unless reconciliation note present.
- Template Propagation: When new normative doc rule is adopted, update: plan-template Constitution Check, spec-template alignment bullets, tasks-template path/quality gates.
- Quarterly Audit: Run scan across repo; produce report listing normative statements without principle references; open issues for each orphan.
Rationale: Prevents silent drift between contributor docs and enforceable governance; ensures single source of truth & predictable automation.

### Principle 2: Example Reuse & Location Discipline [PID:J-2]
When illustrating configuration or feature usage, contributors MUST update or extend the most relevant existing example
block instead of introducing a new, redundant example elsewhere in the README or docs. Duplicate examples (same concept
presented in multiple places) are prohibited unless each instance serves a clearly distinct audience or scope, which
MUST be justified in the PR description with the keyword `NON-DUPLICATIVE-JUSTIFICATION`.
Rules:
- Prefer amending the primary example in Quick Start / dedicated feature doc sections.
- If adding a variant (e.g., multi-label vs single-label), integrate it inline with an existing block using minimal
  incremental lines rather than new isolated blocks at document tail.
- Remove or consolidate superseded examples in the same PR.
- CI/Review MUST block PRs that add an example covering already documented behavior without justification.
- Refactors that relocate examples MUST preserve prior anchors or add a short redirect note if anchors change.
Rationale: Prevents documentation drift, reduces maintenance overhead, and keeps authoritative usage patterns obvious.

---

## K. Python Specific

Principles in this category apply only to Python implementations of the project; non-Python ports MAY omit this section.

### Principle 1: Static Typing Discipline [PID:K-1]
All production modules MUST be fully type-checked with `mypy` (no silent exclusion beyond legacy transitional areas explicitly documented).
Rules:
- New code MAY NOT introduce `# type: ignore` without inline justification.
- Broad `Any` disallowed unless interacting with third-party library lacking stubs (justify in PR).
- Progressive enforcement: expand mypy coverage to tests by 2025-11-01 (create issue if deadline adjustment needed).
Rationale: Early defect detection, self-documenting APIs, safer refactors.

### Principle 2: Lean Python Design [PID:K-2]
Prefer pure functions; introduce classes ONLY when stateful behavior or polymorphism required. Avoid deep inheritance;
favor composition. Utility modules keep narrow surface.
Rationale: Improves readability, testability, and reduces accidental complexity.

### Principle 3: Structured Python Docstrings [PID:K-3]
All public Python functions, methods, and class constructors MUST provide a structured docstring. Class docstrings follow a different structure than callable docstrings; classes do NOT list `Parameters:` or `Returns:` sections (those belong to the `__init__` method if not documented at class-level under Attributes).

Scope Separation:
- Class Docstrings: describe purpose, and responsibilities.
- Function / Method / __init__ Docstrings: describe behavior, parameters, return value, and raised exceptions.

Preferred (Canonical) Function / Method Template (RECOMMENDED):
"""
<One-sentence imperative summary.>

Parameters:
- <name>: <concise description>
- ...

Returns:
- <Description of value semantics.>

Raises: (optional)
- <ExceptionType>: <condition>
"""

Canonical Class Template:
"""
<Class purpose in one sentence (declarative is acceptable).>
"""

Rules:
- Triple double quotes; summary starts on first line (PEP 257).
- For canonical functions/methods: section headers exactly `Parameters:`, `Returns:`, `Raises:` (omit unused). Order: Parameters → Returns → Raises.
- For classes: keep concise; add `Attributes:` block ONLY if exposing public state; avoid `Parameters:` / `Returns:`.
- Either document init semantics in class docstring OR in `__init__` docstring, not both.
- Generators: describe yielded semantics under `Returns:` (may include the word “Yields:” inline).
- Update docstrings when signatures / attributes change in same PR.
- Avoid repeating obvious type info already declared; emphasize meaning, constraints, invariants.

Rationale: Provides a single, consistent modern structure and removes ambiguity introduced by legacy tagged formats.

### Principle 4: Import Placement & Ordering [PID:K-4]
All import statements MUST reside in the top contiguous import block(s) of a Python file, grouped logically and free of
inline business logic.
Rules:
- Group order (separated by single blank lines):
  1. Standard library
  2. Third-party packages
  3. Local project modules (relative or absolute)
- Within each group, alphabetical (case-insensitive) ascending order preferred; multi-line `from x import (...)` allowed for readability.
- New imports MUST be inserted into their correct group/location—never appended mid-file or at usage site.
- Prohibited: late/function-scope imports except for (a) optional heavy deps behind feature flags, or (b) circular import mitigation (must add inline justification comment `# Late import: circular dependency with <module>`).
- Remove unused imports in same PR that renders them unused.
- Wildcard imports (`from x import *`) forbidden.
Rationale: Improves clarity, reduces merge conflicts, enables deterministic isort enforcement, and surfaces dependency scope early.

### Principle 6: Import Insertion Discipline [PID:K-6]
When adding a new import, it MUST be placed into the existing top-of-file grouped import block (see PID:K-4) without creating duplicate group separators or resorting the entire file unnecessarily.
Rules:
- Insert minimal diff: add the line in correct alphabetical spot inside its group only.
- Do not reorder untouched neighboring imports unless strictly required (avoid churn-only diffs).
- If introducing first member of a new group (e.g., first third-party import in file), create the group with a single blank line separation consistent with PID:K-4.
- Late imports inside functions require an inline justification comment (performance or circular dependency) and SHOULD reference PID:K-6.
Rationale: Reduces diff noise, minimizes merge conflicts, and reinforces predictable structure.
Anti‑Patterns:
- Re-sorting entire import block for a single addition.
- Adding import adjacent to usage site mid-file.

---

(End of Appendix)
