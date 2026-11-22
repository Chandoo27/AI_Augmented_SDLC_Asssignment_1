# Amendments: Gemini Reminder Agent (Part 1B)

Each amendment is recorded before the change that depends on it. None of them changes a
threshold, a dataset case or an expected result.

## A1 — Failure evidence for repair (2026-11-22)

**Reason.** FR-014 and NFR-007 keep request text and model output out of the evaluation report.
The report therefore names a failed case by ID and code only, so the coding agent receives no
generated output, which the repair step needs.

**Change.** An optional `--failure-evidence PATH` flag on `reminder-agent-evaluate` writes a
separate file with, for each failed run, the case ID, run index, failure codes, the expected
response and the response the model produced. It does not copy the request text (the case ID
finds it in the dataset). It is used only with the synthetic evaluation datasets. The report
itself is unchanged and still omits both.

**Impact.** FR-014 and NFR-007 still hold for the report and for logs. API keys are never
written to the evidence file.

## A2 — Pacing and rate-limit wait (2026-11-22)

**Reason.** Four live evaluations stopped at the 140-attempt ceiling, mostly on rate-limit
(429) errors. There was no pacing between calls, and a retry after a 429 waited one second.

**Change.** `GEMINI_MIN_INTERVAL_SECONDS` (default 5, range 0 to 60) sets a minimum time between
provider attempts, and a 429 retry waits 20 seconds. The ceiling of 140 attempts (NFR-010) and
the retry limit are unchanged.

**Impact.** A run takes longer. The retry test for a 429 now expects the 20-second wait instead
of one second; a separate test keeps the one-second wait for server errors.

## A3 — Dataset location (2026-11-22)

**Reason.** The assignment structure expects the evaluation data under `evals/`.

**Change.** `data/evaluation/` moved to `evals/`. File names and contents are unchanged, and
every reference in code, tests and documents was updated.

**Impact.** None on behaviour. The two dataset files are identical; the traceability manifest differs
only in the two dataset path strings it contains.
