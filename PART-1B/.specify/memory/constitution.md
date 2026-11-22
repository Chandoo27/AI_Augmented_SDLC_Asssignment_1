# Gemini Reminder Agent Constitution

## Core Principles

### I. The Model Decides, Local Code Verifies
Natural-language interpretation MUST use the configured Google Gemini model on every valid
request. The application MUST NOT fall back to a deterministic parser or local heuristic when
the model is unavailable. Model output is untrusted: it MUST be parsed and validated locally
(schema, required values, target identity, date and time validity, cross-field consistency)
before it is returned. The model MUST NOT have any tool, authority or path to save, send or
change a reminder. A reply that fails validation MUST be reported as a safe error code and
never shown as an answer.

### II. A Testable Response Contract
Every successful request MUST produce exactly one JSON object with the five fields `intent`,
`task`, `datetime`, `needs_clarification` and `clarification_question`, with no extra fields
and no surrounding text. The canonical JSON Schema in the specification is the single source of
truth. Missing, ambiguous, unsupported or unresolvable input MUST lead to one focused
clarification question, never to an invented task, target, date, time or time zone.

### III. Secure by Default
API keys and model settings MUST come from the local environment or an ignored `.env` file and
MUST NOT appear in source, commits, logs, evaluation reports, evidence or chat. User text is
data, never instructions. Logs and reports MUST use safe error codes, not stack traces, and
MUST NOT contain keys. The evaluation uses synthetic requests only.

### IV. Independent Evaluation of a Non-Deterministic System
The evaluation harness, the datasets, the response schema and the thresholds MUST be
independent of the generated application code and MUST be fixed before the final evaluation.
They MUST NOT be weakened during repair: no case is removed or relabelled, no expected result
is changed without a recorded specification amendment, no threshold is lowered and no guardrail
is disabled. The harness MUST report schema validity, property validity and semantic
correctness separately, and an aggregate score MUST NOT hide a failing layer. Live results MUST
come from real, independent model calls at a positive, recorded temperature. Failures caused
by the provider (rate limits, timeouts, server errors) MUST be reported separately from
failures of the application or the prompt. The initial generation MUST be preserved before
the first repair, and genuine run results MUST be retained as produced.

### V. Bounded, Automated Quality
Unit, contract, property and harness tests MUST use a fake model adapter and MUST NOT need a key
or the network. A separate, explicit command runs the live evaluation. Timeouts, retries and
the number of provider calls MUST be bounded and documented, and a run that exhausts its
budget MUST stop with a visible failure. Before a change is accepted, lint, format, type
check, tests with at least 90% line coverage of the core modules, Bandit, pip-audit and a
secret scan MUST pass.

### VI. Traceability and Simplicity
Every requirement MUST map to stable evaluation cases, tests and implementation references.
Changes MUST implement only approved requirements, and abstractions, dependencies and
configuration MUST be added only to solve a stated need.

## Governance

This constitution governs the specification, plan, tasks, implementation and review of Part 1B.
Amendments MUST record the reason and the date and update the version (MAJOR for incompatible
governance changes, MINOR for new or expanded principles, PATCH for clarifications). Any change
to a protected artifact (spec, datasets, schema, thresholds, harness) MUST first be recorded as
a dated amendment. Exceptions MUST be explicit, justified and time-bounded.

**Version**: 0.1.0 | **Status**: Draft; ratification pending student review | **Drafted**: 2026-11-22
