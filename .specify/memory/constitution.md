<!--
Sync Impact Report
Version change: 1.7.0 -> 1.7.1
Modified principles: (relocated only)
Added sections: Externalized principles to principles.md
Removed sections: Inlined Core Principles body
Templates requiring updates: None (references still valid)
Follow-up TODOs: Optional CI check to ensure edits go to principles.md not constitution.md
-->

# Generate Release Notes Action Constitution

## Core Principles

The full, authoritative list of principles has been MOVED to `principles.md` in the same directory
(`.specify/memory/principles.md`). This constitution now references them instead of embedding the full text to:
- Reduce duplication during amendments
- Simplify diff review for governance-only changes
- Enable future automated validation tooling (scan principles independently)

Editing Rules:
- Add / modify / remove a principle ONLY in `principles.md`.
- Bump the constitution version (MINOR or MAJOR per governance rules) here referencing the relocation.
- If a principle is materially redefined, update Sync Impact Report and any affected templates.

Principle Index (see `principles.md` for full text):
1. Test-First Reliability (PID:A-1)
2. Explicit Configuration Boundaries (PID:B-1)
3. Deterministic Output Formatting (PID:B-2)
4. Minimal Surface & Single Responsibility (PID:C-1)
5. Transparency & Observability (PID:D-1)
6. Safe Extensibility (PID:C-2)
7. Resource-Conscious API Usage & Performance Budgeting (PID:E-1)
8. Lean Python Design (PID:K-2)
9. Localized Error Handling & Non-Exceptional Flow (PID:F-1)
10. Dead Code Prohibition (PID:G-1)
11. Focused & Informative Comments (PID:G-2)
12. Test Path Mirroring (PID:A-2)
13. Branch Naming Consistency (PID:H-1)
14. Static Typing Discipline (PID:K-1)
15. TODO Debt Governance (PID:G-3)
16. Security & Token Handling (PID:I-1)
17. Documentation-Derived Rule Synchronization (PID:J-1)
18. Example Reuse & Location Discipline (PID:J-2)

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
- Failing tests are written first (PID:A-1) for new core logic.
- Path mirroring (PID:A-2) enforced for all new/changed modules.
- Branch naming check enforced (PID:H-1).
- Typing coverage gate (PID:K-1).
- TODO audit gate (PID:G-3).
- Performance summary logged in verbose mode (PID:E-1) when enabled.
- Documentation rule sync: PR review checklist confirms PID:J-1 compliance for any *.md normative additions.
- Example reuse discipline: PRs adding/modifying examples MUST cite PID:J-2 (or mark justified variant).

## Workflow & Quality Gates

Pre-merge mandatory local (and CI) gates:
1. Formatting: black --check (line length 120).
2. Linting: pylint global score ≥9.5 (no fatal errors).
3. Typing: mypy (0 blocking errors); justify new ignores (PID:K-1).
4. Tests: pytest all green.
5. Coverage: ≥80% overall; justify any temporary dip (PID:A-1 context).
6. Dead Code: remove or justify (PID:G-1).
7. Determinism: repeat test run yields identical sample output (PID:B-2).
8. Branch Naming: enforced allowed prefix (PID:H-1).
9. TODO Governance: all TODOs issue-linked & within lifetime window (PID:G-3).
10. Performance Budget (when verbose/perf job active): API call soft target evaluation (PID:E-1).
11. Documentation Rule Sync: normative doc changes reconciled (PID:J-1).
12. Example Reuse Discipline (PID:J-2).

Quality Gate Failure Handling:
- Minor failures (formatting, lint) → immediate fix; no waivers unless urgent hotfix.
- Coverage dip → explicit justification + recovery issue.
- Non-deterministic output → BLOCKING (PID:B-2).
- Branch naming violation → BLOCKING until renamed (PID:H-1).
- TODO governance failure → BLOCKING (PID:G-3).
- Performance overrun → CONDITIONAL (document + follow-up optimization task) unless causing timeouts → BLOCKING (PID:E-1).
- Documentation rule sync failure → BLOCKING until reconciliation (PID:J-1).
- Example duplication violation → BLOCKING (PID:J-2).

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
- Compliance Review: PR template SHOULD reference key PIDs (A-1, B-1, B-2, E-1, G-1, A-2, H-1, K-1, G-3, J-1, J-2 + coverage threshold).
- Backward Compatibility: Input names & placeholder semantics require MAJOR bump if changed.
- Enforcement: CI automates formatting, lint, typing, tests, coverage, branch prefix, TODO lint, and optional performance logging.

**Version**: 1.7.1 | **Ratified**: 2025-10-12 | **Last Amended**: 2025-10-15
