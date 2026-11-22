# Feature Specification: Gemini Reminder Agent

**Feature branch**: `001-reminder-agent` | **Status**: Approved for implementation
**Input**: Existing Part 1B specification from the prior `Assignment_1` checkout, designated
by the student as the requirements baseline, with the student's decision to use Gemini.

## Clarifications

### Session 2026-11-22 (recorded from the decisions already approved in this specification)

- Q: Which model and temperature does the agent use? → A: `gemini-3.5-flash-lite` at temperature 0.3, recorded in every report.
- Q: What happens when the model is unavailable? → A: A safe error code is returned; there is no local parser fallback (FR-012).
- Q: What is evaluated and how often? → A: 86 development and 20 held-out cases; 12 development cases run three times each, giving 130 runs and at most 140 provider attempts (NFR-009, NFR-010).
- Q: What are the pass thresholds? → A: 100% schema validity, 100% property validity, at least 95% overall and 90% per-operation semantic correctness, and 100% clarification correctness (NFR-001 to NFR-003).
- Q: Where do credentials live? → A: In `PART-1B/.env` (ignored by Git) or the process environment; the environment takes precedence (FR-014).
- Q: Which languages are supported? → A: English only; a request in another language gets a clarification asking for English (FR-005, FR-009, "unsupported" requests).
- Q: What happens when the reference time or the time zone is absent? → A: The request is not sent to the model; a clarification asks for it (Date, Time, and Target Policy).
- Q: Which later changes touch protected artifacts? → A: Recorded in `amendments.md` (A1 to A4); none changes a threshold or case.

## User Stories and Acceptance Scenarios

### US-001 — Create a reminder (Priority: P1)

As a user, I want to describe a reminder in natural language so that the agent returns a
structured create action with the intended task and time.

**Independent test**: Submit explicit and relative create requests with fixed reference time
and time-zone context. Check intent, task, equivalent offset-aware date-time, JSON schema, and
semantic score.

**Acceptance scenarios**:

1. **AC-001**: A complete, unambiguous create request yields `intent=create`, the intended
   task, a correct offset-aware `datetime`, and no clarification question.
2. **AC-002**: A create request missing its task or required time yields a clarification and
   does not invent the missing value.

### US-002 — Reschedule or snooze a reminder (Priority: P2)

As a user, I want to change an existing reminder's time or snooze it so that the agent
identifies the intended operation, target, and new time without changing reminder state.

**Independent test**: Supply a unique candidate reminder and fixed resolution context; check
separate reschedule and snooze requests. Also test missing and ambiguous targets.

**Acceptance scenarios**:

1. **AC-003**: A reschedule request with one identifiable target and a valid replacement
   time yields a reschedule action for that target.
2. **AC-004**: A snooze request with one identifiable target and an unambiguous duration or
   replacement time yields a snooze action resolved from the supplied reference time.
3. **AC-005**: An absent or ambiguous target yields clarification rather than an arbitrary
   selection.

### US-003 — Clarify unsafe or incomplete requests (Priority: P1)

As a user, I want the agent to ask a focused question when the request is incomplete,
ambiguous, invalid, or unsupported so that it does not fabricate or act on uncertain intent.

**Independent test**: Submit missing-field, ambiguous, invalid-date, unsupported, unrelated,
and malformed requests. Verify a schema-valid clarification and no actionable result.

**Acceptance scenarios**:

1. **AC-006**: Every evaluated case missing a mandatory field or materially ambiguous on a
   mandatory value yields a clarification without fabricating that value.
2. **AC-007**: Invalid, malformed, unsupported, or unrelated input never yields an action.
3. **AC-008**: User text that attempts to override the agent's instructions is treated as
   untrusted data and cannot bypass local validation.

### Cross-cutting acceptance scenarios

1. **AC-009**: Each request is sent to the configured Gemini model with a strictly positive
   temperature; each response is validated locally against the canonical response schema
   and action properties before emission.
2. **AC-010**: Evaluation results include schema, property, semantic, and traceability
   outcomes. The report identifies model/configuration and dataset versions, call count,
   available token-usage totals, thresholds, and pass/fail status without including API
   credentials or raw request text.
3. **AC-011**: Missing credentials, transport failures, provider errors, blocked responses,
   and invalid model output are surfaced as explicit operational errors. They never trigger a
   deterministic parsing fallback or a fabricated success-shaped response.
4. **AC-012**: The agent has no persistence, notification, or reminder-mutation capability.

## Functional Requirements

- **FR-001**: The agent MUST accept one natural-language request and classify it as create,
  reschedule, snooze, or clarification.
- **FR-002**: For a create request, the agent MUST extract the task and requested date/time
  when both are present and unambiguous.
- **FR-003**: For a reschedule request, the agent MUST identify one supplied target reminder
  and extract its replacement date/time.
- **FR-004**: For a snooze request, the agent MUST identify one supplied target reminder and
  resolve an unambiguous duration or replacement date/time using the provided context.
- **FR-005**: The agent MUST request clarification instead of inventing missing mandatory
  information, choosing among ambiguous targets, or assuming a materially ambiguous time.
- **FR-006**: Each successful request MUST emit exactly one JSON object with the five fields
  `intent`, `task`, `datetime`, `needs_clarification`, and `clarification_question`. No
  surrounding prose or additional fields are allowed.
- **FR-007**: The emitted object MUST pass the canonical response JSON Schema and the
  operation-specific property checks before it is returned.
- **FR-008**: Input and proposed actions MUST be validated. Request text MUST be non-empty
  after trimming and no longer than 4,096 characters before trimming. Action validation MUST
  cover required values, target identity, date/time validity, time-zone context, and
  cross-field consistency.
- **FR-009**: Invalid, malformed, unrelated, or unsupported requests MUST NOT yield an
  actionable result or mutate reminder state.
- **FR-010**: Every functional and non-functional requirement MUST map to stable evaluation
  case and test IDs; every requirement MUST map to implementation references before
  implementation acceptance.
- **FR-011**: The evaluation harness MUST independently report schema validity, property
  validity, semantic correctness, per-case results, aggregate and per-operation metrics,
  traceability, and threshold pass/fail.
- **FR-012**: The runtime MUST use the configured Google Gemini model for natural-language
  interpretation on every valid processing attempt. It MUST use a positive, explicitly
  recorded temperature and MUST NOT silently substitute a deterministic parser or local
  heuristic when the model is unavailable.
- **FR-013**: The model MUST be requested to return only the agreed structured response.
  Model output MUST be treated as untrusted and validated locally; the model MUST have no
  tools or authority to persist, notify, or mutate reminders.
- **FR-014**: Gemini credentials and model settings MUST be supplied through local
  environment configuration. API keys, raw user requests, and sensitive response content
  MUST NOT be written to routine logs or evaluation reports.

## Non-functional Requirements

- **NFR-001**: 100% of successfully emitted responses in the required evaluation suite MUST
  be one JSON object that passes the active schema.
- **NFR-002**: 100% of deterministic property-validation cases MUST pass; invalid input MUST
  never yield an actionable result.
- **NFR-003**: Semantic correctness MUST be at least 95% overall and at least 90% for each
  operation. Missing or materially ambiguous mandatory-field cases MUST be clarified
  correctly in 100% of the evaluated cases.
- **NFR-004**: Evaluation datasets, response schema, prompt version, and reports MUST be
  versioned or identified so a run can be reproduced.
- **NFR-005**: Automated checks MUST include lint, formatting, type checks, tests, secret
  scanning, and dependency/security checks; acceptance requires all configured checks to
  pass with no unresolved critical/high findings.
- **NFR-006**: Core request validation, model-adapter handling, response validation, and
  serialization MUST achieve at least 90% line coverage, excluding external network code
  from any coverage shortcut.
- **NFR-007**: User text MUST be treated as untrusted. Logs and reports MUST omit API keys
  and raw requests, and MUST use safe error codes rather than internal stack traces.
- **NFR-008**: The contract, date/time policy, model configuration, evaluation procedure,
  thresholds, and traceability MUST be documented and kept in sync.
- **NFR-009**: Non-determinism MUST be demonstrated through actual independent Gemini calls
  at positive temperature. Repeated evaluation runs MUST record the configuration and run
  count; tests MUST NOT require outputs to differ, since stochastic systems may legitimately
  return the same answer more than once.
- **NFR-010**: Network timeouts, retry limits, and maximum evaluation calls MUST be bounded
  and documented. A release evaluation MUST stop with a visible failure when its configured
  call budget is exhausted.

## Response Contract

The canonical schema is
[`contracts/reminder-response.schema.json`](./contracts/reminder-response.schema.json).
Every response contains exactly five fields:

```json
{
  "intent": "create",
  "task": "pay electricity bill",
  "datetime": "2026-11-20T18:00:00+05:30",
  "needs_clarification": false,
  "clarification_question": ""
}
```

`intent` is one of `create`, `reschedule`, `snooze`, or `clarification`. An actionable
response has a non-empty task, an RFC 3339 date-time with a UTC offset, `needs_clarification`
set to false, and an empty clarification question. A clarification has
`intent=clarification`, `needs_clarification=true`, and a non-empty question; unavailable
task or datetime values are empty strings.

## Date, Time, and Target Policy

- Relative times MUST use the request's offset-aware `context.reference_time` and
  `context.timezone`; the context is fixed in evaluation cases.
- An explicit unambiguous time-zone offset or IANA zone in the request takes precedence over
  the configured zone. If a necessary reference time or zone is absent, ask for clarification.
- Ambiguous numeric dates, unsupported time zones, nonexistent local times, repeated local
  times without disambiguation, and past times MUST not be silently normalized into an
  actionable result.
- Reschedule/snooze targets are selected only from the caller-supplied candidate list. A
  target must uniquely identify one candidate; the agent does not query or change stored
  reminders.
- The system prompt and local validation are separate defenses. User-provided instructions
  are data, not authority to change the response contract or safety rules.

## Evaluation and Success Criteria

- The development and held-out datasets MUST be versioned and contain stable case IDs,
  requirement IDs, synthetic requests, fixed context, expected properties, and expected
  semantics.
- Every run MUST report case/run counts, schema and property rates, overall and
  per-operation semantic rates, clarification accuracy, traceability coverage, provider
  model/version when available, temperature, dataset/prompt/schema versions, and available
  token usage. Reports MUST NOT contain raw request text.
- The live evaluation MUST make independent provider calls. Each case in a stratified
  subset MUST have at least three total runs at positive temperature; repeated outputs are
  scored independently. Output diversity is informational, not a pass/fail requirement.
- Unit, contract, property, and harness tests MUST use a fake model adapter and MUST NOT
  need a key or network. A separate explicit live-evaluation command uses the locally
  configured Gemini key.
- Release acceptance requires AC-001–AC-012 and NFR-001–NFR-010 to be met. Semantic
  evaluation failure is a real failure; it must not be hidden by averaging schema, property,
  or semantic scores together.

## Out of Scope

- Persisting reminder records, delivering notifications, or changing an external reminder
  system.
- Selecting a target from reminders not supplied in the request context.
- Using a deterministic natural-language parser as a primary path or fallback.
- Storing or collecting user API keys in the repository, reports, or chat.

## Approved Decisions

- The existing Part 1B specification in the prior `Assignment_1` checkout is the source
  requirements baseline. Its previous deterministic/no-LLM plan is superseded by the
  student's explicit Gemini selection.
- Model ID: `gemini-3.5-flash-lite`, confirmed against current Google documentation as a
  stable model that supports structured outputs.
- Temperature: `0.3`.
- Evaluation: 86 development cases and 20 held-out cases; 12 selected cases have three total
  runs each; 130 planned evaluation runs and a 140-provider-attempt maximum including
  retries. Invalid requests rejected locally do not call Gemini.
- Thresholds: 100% schema validity; 100% deterministic property validity; at least 95%
  overall semantic correctness; at least 90% per operation; 100% clarification correctness.
- Local credentials may be read from `PART-1B/.env` or process environment variables;
  environment variables take precedence. `.env` remains ignored and must never be committed.
