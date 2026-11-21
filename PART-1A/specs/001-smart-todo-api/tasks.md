# Tasks: Smart Todo API

**Input**: Approved planning input in this directory (`spec.md`, `plan.md`)  
**Status**: T001–T010 are complete, including student approval and the protected baseline.
Application implementation is starting.
**Rule**: Additions or changes to requirements must be approved in `spec.md` before
implementation. Tests and harness rules are protected once the student approves the baseline.

## Phase 1: Setup

- [x] T001 Create the Python package, `pyproject.toml`, lint/security configuration, CI workflow,
  and dependency installation instructions (NFR-005, AC-018).
- [x] T002 Create the source/test directory skeleton and isolated test fixtures, including an
  injectable temporary JSON data path (FR-009, NFR-003, AC-011, AC-013).

## Phase 2: Independent Tests and Harness Baseline

- [x] T003 Add model/validation tests for defaults, trimming, boundary lengths, priorities,
  tags, immutable fields, and empty updates (US-001, FR-001–FR-004, FR-010; AC-001–AC-005).
- [x] T004 Add JSON persistence tests for missing, valid, malformed, unreadable, atomic-write,
  and serialized-update behavior (US-001, US-003, FR-004, FR-009, FR-011; AC-011, AC-013,
  AC-017).
- [x] T005 Add API error-contract tests for stable JSON errors, HTTP status codes, and sanitized
  persistence failures (US-001, FR-010–FR-011; AC-006–AC-007, AC-012–AC-013).
- [x] T006 Add CRUD contract tests for create/list/get/update/delete, defaults, input limits,
  immutable values, and rejected-request state preservation (US-001, FR-001–FR-005,
  FR-010–FR-011; AC-001–AC-007, AC-012).
- [x] T007 Add filter and ordering tests for exact case-insensitive match-any tags, empty
  results, priority order, deterministic ties, and combined query options (US-002,
  FR-003, FR-007–FR-008; AC-009–AC-010).
- [x] T008 Add complete/reopen idempotency and restart-persistence tests (US-003, FR-006,
  FR-009–FR-011; AC-006, AC-008, AC-011, AC-013, AC-016).
- [x] T009 Add a repeatable 1,000-task performance check with a recorded test-machine
  description (US-002, FR-008, NFR-002; AC-015).
- [x] T010 Review the specification-derived tests and fail-closed harness, record approval,
  and create the protected student baseline before implementation. The runner is prepared;
  its focused tests pass. (NFR-005; AC-018).

## Phase 3: Implement US-001 — Manage Tasks

- [x] T011 Implement typed task/request/response/error models and validation from the approved
  contract (US-001, FR-001–FR-004, FR-010–FR-011; AC-001–AC-005).
- [x] T012 Implement local JSON persistence with atomic writes, safe error handling, and
  serialized read-modify-write updates (US-001, US-003, FR-004, FR-009, FR-011;
  AC-011–AC-013, AC-017).
- [x] T013 Implement app construction and common HTTP error handling without exposing internal
  paths or stack traces (US-001, FR-010–FR-011; AC-006, AC-012–AC-013).
- [x] T014 Implement CRUD service operations and REST routes, preserving partial-update and
  not-found behavior (US-001, FR-001–FR-005, FR-010–FR-011; AC-001–AC-007, AC-012).

## Phase 4: Implement US-002 — Organize and Find Tasks

- [ ] T015 Implement match-any tag filtering and deterministic priority/date/ID ordering,
  including combined filters and sort (US-002, FR-003, FR-007–FR-008, FR-010;
  AC-009–AC-010).

## Phase 5: Implement US-003 — Complete Tasks and Keep Their Data

- [ ] T016 Implement idempotent complete/reopen operations and verify all task fields survive
  app recreation (US-003, FR-006, FR-009–FR-011; AC-006, AC-008, AC-011, AC-013, AC-016).

## Phase 6: Release Verification

- [ ] T017 Document setup, API contract, test/harness commands, performance test machine, and
  limitations; ensure commands are reproducible from a clean checkout (FR-010–FR-012,
  NFR-001–NFR-005; AC-014–AC-018).
- [ ] T018 Run all baseline-protected tests and quality/security gates, resolve genuine
  findings without weakening requirements, and prepare evidence for the student's final
  review (FR-001–FR-012, NFR-001–NFR-005; AC-001–AC-018).

## Requirement-to-Task Traceability

See [traceability.md](./traceability.md) for the requirement-to-acceptance-criterion-to-test
node mapping.

| Requirement | Tasks |
|---|---|
| FR-001 | T003, T006, T011, T014 |
| FR-002 | T003, T004, T006, T011, T014 |
| FR-003 | T006, T007, T014–T015 |
| FR-004 | T003–T004, T006, T011–T012, T014 |
| FR-005 | T006, T014 |
| FR-006 | T008, T016 |
| FR-007 | T007, T015 |
| FR-008 | T007, T009, T015 |
| FR-009 | T002, T004, T008, T012, T016 |
| FR-010 | T003, T005–T008, T011, T013–T018 |
| FR-011 | T004–T006, T008, T011–T014, T016–T018 |
| FR-012 | T017 |
| NFR-001 | T004, T012, T017 |
| NFR-002 | T009, T017 |
| NFR-003 | T002, T004, T006, T008, T012 |
| NFR-004 | T004, T008, T012, T016 |
| NFR-005 | T001, T010, T018 |

## Dependencies and Checkpoints

- T001–T002 precede test and implementation work.
- T003–T009 are specification-derived tests and must be reviewed before T010 is completed.
- T010 and the reviewed tests precede the student's baseline tag and all implementation tasks.
- T011–T014 establish the shared model, persistence, error, and CRUD foundation.
- T015 depends on the list service and route from T014.
- T016 depends on the shared store and task service.
- T017–T018 depend on all selected stories.
- Each task is marked complete only after its changes and focused verification are reviewed.
