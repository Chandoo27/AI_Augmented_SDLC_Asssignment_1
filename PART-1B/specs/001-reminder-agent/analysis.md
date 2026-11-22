# Specification Analysis: Gemini Reminder Agent (Part 1B)

Run on 2026-11-22 as a read-only consistency check of `spec.md`, `plan.md`, `tasks.md`,
`traceability.md`, the datasets and the constitution. This stage was added after implementation
and after four failed live evaluations. It records what the check finds; the repairs it leads to
are listed below and committed separately.

## Findings

| ID | Severity | Where | Finding | Action |
|----|----------|-------|---------|--------|
| B1 | HIGH | `gemini_client.py` | There was no pacing between provider calls, and a rate-limit retry waited only 1 second. With the 140-attempt ceiling (NFR-010) this made a full run exhaust its budget on 429 errors. | Repaired: a minimum interval between calls and a 20 s wait after a 429 (commit `89c960e`). |
| B2 | HIGH | FR-014 / NFR-007 against the assignment's repair rule | Reports omit request text and model output. A failed case is therefore reported only by ID and code, with no generated output to give the coding agent. | Amendment A1 in `amendments.md`: a separate local failure-evidence file for synthetic cases only. |
| B3 | MEDIUM | repository | The constitution for Part 1B was missing and Spec Kit was not initialised. | Added on 2026-11-22; still pending the student's ratification. |
| B4 | MEDIUM | `data/evaluation/` | The assignment expects the dataset under `evals/`. | Moved to `evals/` with all references updated. |
| B5 | MEDIUM | `spec.md` | There is no clarification record for Part 1B. The "Approved Decisions" section holds the decisions. | Recorded in the Clarifications section of `spec.md`. |
| B6 | LOW | NFR-010 | The ceiling of 140 attempts leaves only 10 retries over 130 planned runs. | Keep the ceiling. Pacing makes retries rare. A raise would need an amendment. |
| B7 | LOW | `tasks.md` | T023 (live release evaluation) is open. | Closed only when a complete run produces a report that meets the thresholds, or the failure is recorded as the final outcome. |

## Coverage

All FR-001 to FR-014 and NFR-001 to NFR-010 map to evaluation cases and tests in
`evals/traceability.json` (formerly `data/evaluation/traceability.json`), which a test checks. There are no conflicts between the spec
and the plan. The thresholds were fixed before the first live run (commit `0c05ed4`) and are not
changed by any repair.
