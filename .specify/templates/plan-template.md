# Implementation Plan: [FEATURE]

<!-- Principles: authoritative text lives in .specify/memory/principles.md; do not copy full definitions here. -->

**Branch**: `<prefix>/[###-descriptor]` (prefix ∈ {feature, fix, docs, chore}) | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., PyGithub, PyYAML, semver or NEEDS CLARIFICATION]  
**Testing**: pytest ONLY (per Constitution)  
**Target Platform**: GitHub Action runners (Ubuntu) or NEEDS CLARIFICATION  
**Performance Goals**: [domain-specific, e.g., <5s generation time for 500 issues]  
**Constraints**: [e.g., rate limit adherence, stable deterministic output]  
**Scale/Scope**: [e.g., repos up to 10k issues in release window]

## Constitution Check

*Consult full principle definitions in `.specify/memory/principles.md` (single source of truth).* 

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Mandatory alignment items:
- Test‑First Reliability (P1): Provide failing unit test list BEFORE implementation.
- Explicit Configuration Boundaries (P2): All new behavior exposed via action inputs (list any new inputs needed).
- Deterministic Output Formatting (P3): Confirm ordering & placeholders remain stable.
- Performance Budget & API Usage (P7): Estimate added API calls (target ≤3*(issues+PRs)), define logging/measurement plan, and fallback behavior if rate limit low.
- Lean Python Design (P8): Justify each new class; prefer functions for stateless logic.
- Localized Error Handling (P9): Define how errors are logged instead of cross-module exceptions.
- Dead Code Prohibition (P10): Identify any code to delete made obsolete by this feature.
- Test Path Mirroring (P12): Confirm new unit tests placed in `tests/unit/<source-relative-path>/test_<file>.py`.
- Branch Naming Consistency (P13): Confirm current branch uses allowed prefix (feature|fix|docs|chore):
  `git rev-parse --abbrev-ref HEAD | grep -E '^(feature|fix|docs|chore)/'`.
- Static Typing Discipline (P14): Public APIs fully typed; list any unavoidable `Any` / `type: ignore` with justification.
- TODO Debt Governance (P15): Any introduced TODO lines MUST carry issue reference; list initial issues here.
- Security & Token Handling (P16): No logging of secrets; describe any new external API interactions & masking strategy.
- Documentation‑Derived Rule Sync (P17): Any new/changed normative doc statements reconciled (reference principle / amendment / NON-NORMATIVE justification).

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
release_notes_generator/
  ...existing modules...

tests/
  unit/          # All unit tests (REQUIRED)
  integration/   # End-to-end tests (if any new ones added by feature)
  fixtures/      # Static data samples (optional)
  helpers/       # Test helper utilities
```

**Structure Decision**: [Document any new modules or directories added]

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., new class] | [current need] | [function approach insufficient due to state] |
| [e.g., added input] | [feature toggle] | [implicit behavior would break determinism] |
