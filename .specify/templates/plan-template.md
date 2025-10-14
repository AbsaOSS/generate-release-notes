# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
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

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Mandatory alignment items:
- Test‑First Reliability: Provide failing unit test list BEFORE implementation.
- Explicit Configuration Boundaries: All new behavior exposed via action inputs (list any new inputs needed).
- Deterministic Output Formatting: Confirm ordering & placeholders remain stable.
- Lean Python Design: Justify each new class; prefer functions for stateless logic.
- Localized Error Handling: Define how errors are logged instead of cross-module exceptions.
- Dead Code Prohibition: Identify any code to delete made obsolete by this feature.
- Test Path Mirroring: Confirm new unit tests placed in `tests/unit/<source-relative-path>/test_<file>.py`.

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
