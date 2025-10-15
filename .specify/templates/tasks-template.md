---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Core logic unit tests are MANDATORY (Constitution Principle 1). Additional integration or snapshot tests OPTIONAL unless specified.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Single project: `release_notes_generator/` for source, `tests/` for tests
- Tests MUST go under `tests/unit/` (unit) or `tests/integration/` (integration)
- Mirrored paths: For `release_notes_generator/x/y.py` create `tests/unit/release_notes_generator/x/test_y.py`.
- Branch naming: Branch MUST start with allowed prefix (feature|fix|docs|chore) + kebab-case descriptor.
- Typing: New or changed public functions MUST include full type annotations (Principle 14).
- TODOs: Any introduced TODO must include issue reference per `TODO(<issue-id>):` pattern (Principle 15).
- Performance: If feature affects mining/data fetch loops, add measurement & API budget validation task (Principle 7).

<!-- SAMPLE TASKS BELOW (REPLACE) -->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create any new module directories in `release_notes_generator/`
- [ ] T002 [P] Ensure mirrored test path structure for new/relocated tests (Principle 12)
- [ ] T003 Verify branch prefix matches regex `^(feature|fix|docs|chore)/` (Principle 13) or rename before proceeding
- [ ] T004 [P] Add initial failing unit tests in `tests/unit/` for new logic (Test‑First gate)
- [ ] T005 [P] Configure/verify linting, typing (mypy) and formatting tools (Principles 1, 14)
- [ ] T006 [P] Add TODO pattern linter or script (Principle 15)
- [ ] T007 [P] Add performance baseline/measurement scaffold if feature impacts API calls (Principle 7)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Implement feature configuration parsing (test: `tests/unit/test_action_inputs.py` extended)
- [ ] T009 [P] Add utilities (if needed) with tests (`tests/unit/test_utils_<name>.py`)
- [ ] T010 Setup error handling pattern (log & return) — no cross-module exception leakage
- [ ] T011 Dead code removal (list obsolete functions) + tests ensuring replacement paths
- [ ] T012 Security review: confirm no sensitive logging added (Principle 16)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description]

**Independent Test**: [How to verify]

### Mandatory Tests for User Story 1

- [ ] T013 [P] [US1] Unit tests for new pure functions in `tests/unit/test_<name>.py` (start failing)
- [ ] T014 [US1] Update integration test (if scope touched) in `tests/integration/test_generation.py` (optional creation)

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement function(s) in `release_notes_generator/<module>.py` (full typing - P14)
- [ ] T016 [US1] Logging additions (INFO lifecycle, DEBUG details) without secrets (P5, P16)
- [ ] T017 [US1] Ensure deterministic ordering adjustments (P3)
- [ ] T018 [US1] Capture performance metrics (API calls & elapsed) if applicable (P7)

**Checkpoint**: User Story 1 fully functional & independently testable

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description]

**Independent Test**: [How to verify]

### Mandatory Tests for User Story 2

- [ ] T019 [P] [US2] Unit tests for added logic

### Implementation for User Story 2

- [ ] T020 [US2] Implement logic in existing module (maintain typing - P14)
- [ ] T021 [US2] Update records builder ensuring no cross-module exceptions (P9)
- [ ] T022 [US2] Update/extend performance measurement if scope affects API usage (P7)

**Checkpoint**: User Stories 1 & 2 independently functional

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description]

**Independent Test**: [How to verify]

### Mandatory Tests for User Story 3

- [ ] T023 [P] [US3] Unit tests for added logic

### Implementation for User Story 3

- [ ] T024 [US3] Implement functionality
- [ ] T025 [US3] Update documentation/comments (concise, logic-focused) (P11)
- [ ] T026 [US3] Add/adjust TODOs with issue references (P15)
- [ ] T027 [US3] Re-run performance snapshot if affected (P7)

**Checkpoint**: All user stories functional; tests green

---

## Phase N: Polish & Cross-Cutting Concerns

- [ ] TXXX [P] Documentation updates in `README.md`, `docs/`
- [ ] TXXX Code cleanup (remove any newly unused code)
- [ ] TXXX Performance optimization / confirm within budget (P7)
- [ ] TXXX [P] Additional unit tests (edge cases) in `tests/unit/`
- [ ] TXXX Security/robustness improvements (P16)
- [ ] TXXX TODO sweep: ensure all TODOs have current issue links and none expired (P15)

---

## Dependencies & Execution Order

- Setup → Foundational → User Stories (can parallelize after Foundational) → Polish
- Failing unit tests precede implementation per story
- No story proceeds without its mandatory unit tests

## Parallel Opportunities

- All tasks marked [P] can run in parallel
- Different user stories can be developed concurrently once Foundational completes

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Setup & Foundational
2. User Story 1 tests → implementation → validation
3. Demo/merge if stable

### Incremental Delivery
Add each story with its own failing tests → implementation → validation cycle.

## Notes

- Avoid unused functions (delete immediately if obsoleted) (P10)
- Prefer functions over classes unless state/polymorphism required (P8)
- Handle errors locally; log & return (P9)
- Comments concise & logic-focused (P11)
- Test Path Mirroring required for new tests (P12)
- Enforce full typing & minimal ignores (P14)
- TODOs require issue linkage (P15)
- No sensitive output in logs (P16)
- Monitor API calls & elapsed runtime (P7)
