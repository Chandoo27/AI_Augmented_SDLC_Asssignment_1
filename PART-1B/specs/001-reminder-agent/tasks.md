# Tasks: Gemini Reminder Agent

**Input**: Draft design documents in `specs/001-reminder-agent/`
**Status**: Approved for test-first implementation. The student designated the prior
`Assignment_1/PART-1B` specification as the requirements baseline and approved the model and
evaluation settings.

Task IDs are stable and must appear in the commits that complete them. Every task links to
US/FR/NFR/AC IDs. `[P]` indicates independent work in separate files; user-story tags identify
the behavior covered.

## Phase 0 — Review Gate

- [x] T001 Use the prior `Assignment_1/PART-1B` specification as the requirements baseline and reconcile Part 1B requirements,
  thresholds, deliverables, and permitted provider with the draft (`US-001..US-003`,
  `FR-001..FR-014`, `NFR-001..NFR-010`, `AC-001..AC-012`).
- [x] T002 Obtain student approval for `gemini-3.5-flash-lite`, temperature `0.3`, the repeated
  evaluation sample, dataset/call budget, and thresholds (`FR-012`, `NFR-009`, `NFR-010`).

## Phase 1 — Testable Contract and Evaluation Baseline

- [x] T003 [P] Create the Python package/test/data layout, dependency configuration, CI, and
  `.env` example/ignore setup for future local loading without adding either student
  `harness-log.md` (`NFR-005`, `NFR-008`, `FR-014`).
- [x] T004 [P] Add canonical schema contract tests for exact fields, action/clarification
  invariants, datetime format, and invalid/extra fields (`FR-006`, `FR-007`, `NFR-001`,
  `AC-009`).
- [ ] T005 [P] Define typed request, context, response, model configuration, evaluation case,
  result, and report entities (`FR-008`, `FR-014`, `NFR-004`, `NFR-007`).
- [ ] T006 [P] Create traceability data and tests requiring every FR/NFR to map to stable
  evaluation cases, tests, and planned implementation symbols (`FR-010`, `AC-010`).
- [ ] T007 [P] Create synthetic versioned development and held-out datasets with fixed
  temporal context and operation/clarification coverage (`US-001..US-003`, `FR-001..FR-005`,
  `NFR-003`, `NFR-004`).
- [ ] T008 Add deterministic evaluator tests for separate schema/property/semantic metrics,
  operation denominators, repeat runs, call budgets, safe reports, and threshold failures
  (`FR-011`, `NFR-001..NFR-004`, `NFR-009..NFR-010`, `AC-010`).

## Phase 2 — Gemini Adapter and Safe Response Pipeline

- [ ] T009 [P] Write configuration tests first, then implement local settings validation for
  missing key/model, positive temperature, timeout, retry, and call-budget boundaries
  (`FR-012`, `FR-014`, `NFR-010`).
- [ ] T010 [P] Implement a typed model-adapter interface and fake adapter for deterministic
  tests (`FR-012`, `FR-013`, `NFR-009`).
- [ ] T011 Implement Gemini SDK integration with JSON response mode, explicit positive
  temperature, bounded requests, and safe usage metadata (`FR-012..FR-014`, `NFR-007`,
  `NFR-009..NFR-010`).
- [ ] T012 Implement prompt versioning and structured request construction that treats
  request text as untrusted data and grants no model tools (`FR-001`, `FR-013`, `FR-014`,
  `NFR-007`).
- [ ] T013 Write request/action validation tests first, then implement local
  request/time-zone/target validation and canonical response-schema validation; invalid or
  ambiguous proposals cannot become actions (`FR-005`, `FR-007..FR-009`, `AC-005..AC-009`).
- [ ] T014 Implement JSON-only serialization for validated responses and sanitized
  operational errors for configuration/provider/model failures (`FR-006`, `FR-009`,
  `FR-013..FR-014`, `AC-011..AC-012`).

## Phase 3 — User Stories

- [ ] T015 [US-001] Add create-request tests and synthetic evaluation cases for explicit and
  relative dates, task extraction, missing values, ambiguity, and time-zone boundaries
  (`FR-001..FR-002`, `AC-001..AC-002`).
- [ ] T016 [US-002] Add reschedule/snooze tests and cases for unique, missing, and ambiguous
  targets, replacement times, and durations (`FR-003..FR-005`, `AC-003..AC-005`).
- [ ] T017 [US-003] Add clarification, unsupported-input, malformed-input, prompt-injection,
  and no-action property tests (`FR-005`, `FR-008..FR-009`, `AC-006..AC-008`).
- [ ] T018 Add an end-to-end single-request CLI using the validated Gemini pipeline and
  explicit operational-error exit behavior (`FR-001..FR-009`, `FR-012..FR-014`).

## Phase 4 — Evaluation and Release

- [ ] T019 Implement development/held-out evaluation, repeated independent calls, bounded
  call budget, deterministic scoring, token-usage totals, and privacy-safe reports
  (`FR-010..FR-011`, `NFR-001..NFR-004`, `NFR-007`, `NFR-009..NFR-010`, `AC-010`).
- [ ] T020 Add focused tests proving live mode issues independent positive-temperature model
  calls without asserting outputs must differ; ordinary tests remain offline
  (`FR-012`, `NFR-009`, `AC-009`).
- [ ] T021 Complete requirement-to-test/case/source traceability and verify each requirement
  has an implementation reference (`FR-010..FR-011`, `AC-010`).
- [ ] T022 Write quickstart and release documentation for local credentials, model config,
  privacy, tests, live evaluation, budgets, thresholds, and report contents
  (`FR-014`, `NFR-004..NFR-008`, `AC-010..AC-011`).
- [ ] T023 Run unit/contract/property tests, offline harness tests, configured quality and
  security checks, then the approved live development and held-out evaluation; record actual
  results without creating either `harness-log.md` (`NFR-001..NFR-010`, `AC-001..AC-012`).

## Dependency Order

- T001 and T002 are gates; no implementation task starts before both are complete.
- T003–T008 establish the offline contract, traceability, datasets, and harness before the
  Gemini implementation.
- T009–T014 establish the safe model boundary and response pipeline.
- T015–T018 exercise the three user stories through that pipeline.
- T019–T023 depend on the complete stories and approved evaluation configuration.
- Do not parallelize edits to the same dataset, schema, evaluator, or Gemini adapter file.
