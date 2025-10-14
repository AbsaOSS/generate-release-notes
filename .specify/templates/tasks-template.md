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

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  Replace with generated tasks.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create any new module directories in `release_notes_generator/`
- [ ] T002 [P] Add initial failing unit tests in `tests/unit/` for new logic (Test‑First gate)
- [ ] T003 [P] Configure/verify linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement feature configuration parsing (test: `tests/unit/test_action_inputs.py` extended)
- [ ] T005 [P] Add utilities (if needed) with tests (`tests/unit/test_utils_<name>.py`)
- [ ] T006 Setup error handling pattern (log & return) — no cross-module exception leakage
- [ ] T007 Dead code removal (list obsolete functions) + tests ensuring replacement paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description]

**Independent Test**: [How to verify]

### Mandatory Tests for User Story 1

- [ ] T010 [P] [US1] Unit tests for new pure functions in `tests/unit/test_<name>.py` (start failing)
- [ ] T011 [US1] Update integration test (if scope touched) in `tests/integration/test_generation.py` (optional creation)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement function(s) in `release_notes_generator/<module>.py`
- [ ] T013 [US1] Logging additions (INFO lifecycle, DEBUG details)
- [ ] T014 [US1] Ensure deterministic ordering adjustments

**Checkpoint**: User Story 1 fully functional & independently testable

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description]

**Independent Test**: [How to verify]

### Mandatory Tests for User Story 2

- [ ] T015 [P] [US2] Unit tests for added logic

### Implementation for User Story 2

- [ ] T016 [US2] Implement logic in existing module
- [ ] T017 [US2] Update records builder ensuring no cross-module exceptions

**Checkpoint**: User Stories 1 & 2 independently functional

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description]

**Independent Test**: [How to verify]

### Mandatory Tests for User Story 3

- [ ] T018 [P] [US3] Unit tests for added logic

### Implementation for User Story 3

- [ ] T019 [US3] Implement functionality
- [ ] T020 [US3] Update documentation/comments (concise, logic-focused)

**Checkpoint**: All user stories functional; tests green

---

## Phase N: Polish & Cross-Cutting Concerns

- [ ] TXXX [P] Documentation updates in `README.md`, `docs/`
- [ ] TXXX Code cleanup (remove any newly unused code)
- [ ] TXXX Performance optimization
- [ ] TXXX [P] Additional unit tests (edge cases) in `tests/unit/`
- [ ] TXXX Security/robustness improvements

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

- Avoid unused functions (delete immediately if obsoleted)
- Prefer functions over classes unless state/polymorphism required
- Handle errors locally; log & return
- Comments concise & logic-focused
