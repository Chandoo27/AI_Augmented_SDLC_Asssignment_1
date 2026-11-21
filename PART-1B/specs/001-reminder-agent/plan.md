# Implementation Plan: Gemini Reminder Agent

**Feature**: `001-reminder-agent` | **Status**: Draft; implementation is gated on student approval and reconciliation with the
authoritative assignment brief.

## Summary

Implement a Python command-line agent that sends one natural-language reminder request to a
configured Gemini model, validates the untrusted structured response locally, and emits one
five-field JSON object. The agent has no reminder persistence or side effects. Deterministic
validation is required; deterministic natural-language parsing and model-unavailable
fallbacks are explicitly prohibited.

## Proposed Technical Choices

- Python 3.11+ with a typed `src/reminder_agent/` package.
- Google GenAI Python SDK using the Gemini content-generation API and JSON response mode.
- A simple provider-facing response schema to constrain generation, followed by independent
  validation against the canonical Draft 2020-12 schema and application property rules.
- `GEMINI_API_KEY`, `GEMINI_MODEL`, and `GEMINI_TEMPERATURE` supplied only via the local
  process environment. Never commit a key or require a `.env` file.
- Configurable positive temperature; provisional draft value `0.3`. Exact model and
  temperature are open student decisions, not implementation defaults until approved.
- `jsonschema` with an explicit format checker, Python `datetime`/`zoneinfo` for offset and
  zone validation, pytest/Hypothesis for deterministic tests, and Ruff/mypy/Bandit/pip-audit/
  secret scanning for quality gates.
- Requests use only synthetic, versioned evaluation data. Reports store safe identifiers
  and provider usage metadata, not request text or model response content.

Current official Gemini documentation describes JSON-schema-constrained structured output
and the content-generation endpoint:

- <https://ai.google.dev/gemini-api/docs/structured-output>
- <https://ai.google.dev/api/generate-content>
- <https://ai.google.dev/gemini-api/docs/models>

The selected SDK method and model ID must be confirmed against the live official API
documentation before implementation.

## Architecture

```text
CLI / evaluation runner
  -> input and configuration validation
  -> Gemini adapter (one request; bounded timeout/retries; positive temperature)
  -> parse provider response
  -> local task/date/property validation
  -> canonical response-schema validation
  -> JSON output or explicit operational error
```

The model adapter is injected behind a typed interface. Unit, contract, property, and
ordinary CI tests use a fake adapter and never need a network or credential. Only the
explicit live evaluation command calls Gemini. The adapter exposes safe metadata (model
version and available token counts), while discarding raw request/response data from routine
logs and reports.

## Proposed Project Layout

```text
PART-1B/
  src/reminder_agent/
    config.py          # environment parsing and bounded settings
    models.py          # typed request/response/evaluation entities
    prompt.py          # versioned system and request prompt construction
    gemini_client.py   # provider interface and real/fake adapters
    validation.py      # input, task, timezone, action, and schema checks
    output.py          # validated JSON serialization
    evaluation.py      # dataset runner, metrics, budgets, safe reports
    cli.py             # single-request and explicit live-evaluation commands
  tests/
    unit/
    contract/
    property/
    integration/
  data/evaluation/
    v1.jsonl
    heldout-v1.jsonl
    traceability.json
  specs/001-reminder-agent/
    contracts/reminder-response.schema.json
    spec.md
    plan.md
    tasks.md
    data-model.md
    traceability.md
    quickstart.md
```

## Evaluation Design

1. Keep schema, action-property, and semantic scores independent.
2. Use a development dataset and a separately versioned held-out dataset. Every synthetic
   case has fixed reference time and zone, a gold semantic expectation, stable requirement
   IDs, and a stable evaluation ID.
3. Run each case once; for a stratified subset of 12 cases, make two additional independent
   calls so each has three total runs at positive temperature. Record run counts, not output
   diversity.
4. Use code-based scoring against gold intent, task/target, clarification state, and
   equivalent aware datetime. Do not rely on an LLM judge.
5. Apply a configurable maximum-call budget before starting and stop visibly at the limit.
   The proposal is 140 actual calls maximum: 106 baseline cases, 24 additional repeated
   calls, and at most 10 transient retries. Capture provider token counts when supplied,
   without assuming that token counts are cost.
6. Emit JSON reports containing case IDs, safe error codes, configuration and dataset
   versions, metrics, token totals when available, and pass/fail; never request text,
   response text, or credentials.
7. Fail the live release evaluation on schema/property errors, incomplete traceability,
   unmet semantic/clarification thresholds, missing repeated runs, or exhausted call budget.

The legacy Part 1B documentation uses 86 development cases and 20 held-out cases. The
proposed live run therefore has 130 planned calls and a 140-call ceiling. These values are
provisional until checked against the assignment brief and student approval.

## Error Handling and Safety

- Validate configuration before any network call. Missing key/model or non-positive
  temperature is an explicit configuration error.
- Set a finite request timeout and a small documented retry limit for transient transport or
  rate-limit failures only. Do not retry invalid credentials, blocked prompts, or invalid
  model output as if successful.
- Never log the API key, prompt, raw request, raw response, or provider exception body.
- Never convert provider failure or invalid model output into a clarification or deterministic
  fallback. Return a non-zero command status with a sanitized error code.
- Do not enable tools/function calling. Perform no persistence, notifications, or external
  reminder updates.

## Testing Strategy

- **Unit**: request/config validation, prompt separation, response properties, task identity,
  timezone handling, bounded retries, error redaction, and JSON serialization.
- **Contract**: canonical schema validity, exact five-field output, conditional invariants,
  invalid formats, and no extra properties.
- **Property-based**: malformed/missing values never produce actionable responses; all
  emitted action/clarification variants satisfy cross-field invariants.
- **Adapter integration**: fake provider responses for success, malformed output, safety
  blocks, missing candidates, transient errors, and token metadata.
- **Live evaluation**: explicit, credentialed command over synthetic development and
  held-out data; not part of ordinary CI.
- **Quality/security**: configured test and coverage gate, lint/format/type checks,
  Bandit, pip-audit, and secret scan.

## Approval Decisions Before Implementation

1. Confirm this specification against the original assignment brief.
2. Approve an available Gemini model ID and SDK/API surface.
3. Approve positive temperature (proposed `0.3`) and repeated subset size (proposed 12
   cases with three total calls per selected case).
4. Approve dataset sizes/call budget (proposed 86 development + 20 held-out, 130 planned
   calls and a 140-call ceiling including retries).
5. Confirm the existing 100% schema/property, 95% overall semantic, 90% per-operation, and
   100% clarification thresholds.

## Risks

| Risk | Mitigation |
|---|---|
| Model/API versions change | Configurable model; capture actual model version; verify official docs before coding |
| Nondeterministic output varies | Independent repeated scoring; fixed context; report per-run outcomes |
| Prompt injection or fabricated values | No tools or side effects; local schema/property/target checks; clarification thresholds |
| Network or quota failure | Explicit bounded timeout/retry/call budget; no deterministic fallback |
| Evaluation cost or exposed user text | Synthetic-only corpus, no default live call in CI, safe reports, explicit budget |
| Structured-output schema limitations | Use a basic provider schema, then enforce the full canonical contract locally |
