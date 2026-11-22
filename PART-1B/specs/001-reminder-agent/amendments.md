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
provider attempts, a 429 retry waits 20 seconds, and a retry after a server error or timeout waits 5 seconds. The ceiling of 140 attempts (NFR-010) and
the retry limit are unchanged.

**Impact.** A run takes longer. The retry tests now expect 20 seconds for a 429 and 5 seconds for server errors (before: 1 second).

## A3 — Dataset location (2026-11-22)

**Reason.** The assignment structure expects the evaluation data under `evals/`.

**Change.** `data/evaluation/` moved to `evals/`. File names and contents are unchanged, and
every reference in code, tests and documents was updated.

**Impact.** None on behaviour. The two dataset files are identical; the traceability manifest differs
only in the two dataset path strings it contains.

## A4 — Clarification-topic vocabulary (2026-11-22)

**Reason.** Run 1 (`evidence/eval-runs/run-1/`) marked 30 runs `SEMANTIC_MISMATCH`. Reading the
saved expected-versus-actual evidence showed that 14 of them were correct clarifications with
the right intent and the right topic, rejected only because the keyword list was too narrow.
Examples: "What task would you like me to remind you about?" (task), "How long would you like to
snooze it?" (time), "Which appointment would you like to reschedule?" and "Did you mean A or B?"
(target).

**Change.** The word lists for the `task`, `time` and `target` topics accept those phrasings.
A question about the wrong topic, and a statement that is not a question about the topic, are
still rejected; tests cover both directions. No case, expected response, threshold or
guardrail is changed, and the intent must still match exactly.

**Impact.** The matcher is more accurate, not more lenient about content. Run 1's report stays
as produced; its failure evidence is the record of the difference.

## A5 — Absent reference time or time zone (2026-11-22)

**Reason.** The Date, Time, and Target Policy says that a missing reference time or zone must be
asked about. Case EV-CLARIFY-011 (no time zone) failed in run 1 because the application sent
the request to the model, which invented an answer. This is an application defect, not a
dataset problem.

**Change.** Request validation now rejects an absent reference time or zone with a local
clarification, and the model is not called. The older test that allowed an absent context
contradicted the policy and was replaced.

**Impact.** The CLI without `--reference-time` or `--timezone` now returns a clarification.

## Open decision — EV-SNOOZE-014

The case "Snooze pay electricity bill for one hour." expects a clarification, while "for 1 hour"
(EV-SNOOZE-002) and "for 15 minutes" (EV-SNOOZE-007) expect a snooze. FR-004 accepts an
unambiguous duration. The label looks inconsistent, but the dataset is a protected artifact and
this repair does not change it. The student must decide whether to amend the label; until then
the case is counted as written.
