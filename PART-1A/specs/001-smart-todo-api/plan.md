# Implementation Plan: Smart Todo API

**Branch**: `001-smart-todo-api` | **Spec**: [spec.md](./spec.md)  
**Status**: Draft for student review

## Summary

Build a local REST API for creating, listing, retrieving, partially updating, deleting,
completing, reopening, filtering, and sorting todo tasks. The API uses a local JSON file and
must preserve valid data across restarts without silently replacing malformed data.

## Technical Context

- **Language/runtime**: Python 3.11 or newer.
- **API**: FastAPI with typed Pydantic request and response models.
- **Persistence**: Local JSON file, configurable outside request input; atomic replacement
  and serialized read-modify-write operations.
- **Tests**: pytest and pytest-cov; minimum 80% line coverage.
- **Quality gates**: Ruff lint and format, Bandit, pip-audit, secret scanning, unit and API
  contract tests, plus a 1,000-task performance check.
- **Platform**: Local development on Windows; CI must run from a clean checkout.

## Architecture

```text
HTTP request -> routes -> validation/models -> task service -> JSON storage
                    |             |                 |
                    +------ stable JSON errors -----+

Specification-derived tests + static/security gates -> harness report -> human review
```

- `src/models.py` owns request, response, enum, and error models.
- `src/routes.py` owns HTTP paths, query validation, and status codes.
- `src/services.py` owns task lifecycle, filtering, sorting, and serialized updates.
- `src/storage.py` owns local JSON reads/writes, locking, atomic replacement, and data errors.
- `src/main.py` creates the app, injects the configured store, and maps errors to the
  documented response shape.

## Decisions and Constraints

- Tags use case-insensitive exact matching with match-any semantics for multiple requested
  tags; priority order is High, Medium, Low. These decisions are in the approved spec and
  must not be changed in implementation without a reviewed spec amendment.
- IDs and creation timestamps are system-generated and immutable.
- No authentication, notifications, multi-user behavior, or cloud persistence is included.
- Invalid requests must not mutate task state. Malformed persistence data must remain intact
  and surface as a sanitized server error.

## Verification Strategy

1. Derive tests from `FR-*` and `AC-*`; tests must exist before their corresponding
   implementation tasks.
2. Keep tests, harness, thresholds, and evaluation data independent of application code.
   The student reviews these and creates a baseline tag before implementation.
3. Run each gate with explicit failure propagation and preserve machine-generated output.
   Do not claim a failure or repair unless it actually occurred.
4. Run all documented checks from a fresh clone before the student records ACCEPT or REJECT.

## Commit Milestones

Commits will be made when each real milestone is completed; commits will not be backdated or
constructed to imply work that did not happen.

1. `docs(part-1a): approve plan and traceable tasks [US-001..US-003, FR-001..FR-012]`
2. `test(part-1a): add independent acceptance tests and baseline [AC-001..AC-018]`
3. Incremental implementation commits referencing the affected `US-*`, `FR-*`, and `T*`.
4. `ci(part-1a): enforce quality and security gates [NFR-005, AC-018]`
5. Final validation artifacts and documentation, excluding the student-authored harness log.

## Human Checkpoints

- Student reviews and approves this plan before the task list is finalized.
- Student reviews tests and harness independence before implementation and establishes the
  baseline tag.
- Student saves the first generation, reviews genuine harness findings, and makes the final
  ACCEPT or REJECT decision.
