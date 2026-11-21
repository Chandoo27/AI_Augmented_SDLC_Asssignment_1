# Data Model: Gemini Reminder Agent

## Request

One untrusted natural-language instruction and its resolution context.

| Field | Type | Constraints |
|---|---|---|
| `text` | string | 1–4,096 raw characters; non-empty after trimming; never silently truncated |
| `context.reference_time` | RFC 3339 datetime | Required for relative date/time resolution; must include an offset |
| `context.timezone` | IANA zone name | Required when no unambiguous zone/offset is in the request |
| `context.reminder_tasks` | list of strings | Optional; caller-supplied candidate labels only |

## Agent Response

The public response is exactly the five-field object in
[`contracts/reminder-response.schema.json`](./contracts/reminder-response.schema.json).
Actionable responses require a valid intent, uniquely identified task/target, offset-aware
date-time, `needs_clarification=false`, and an empty clarification question. Clarification
responses require `intent=clarification`, `needs_clarification=true`, and a non-empty question.

## Model Configuration

| Field | Type | Constraints |
|---|---|---|
| `api_key` | secret string | Read from local environment; never serialized, logged, or included in errors |
| `model` | string | Explicit Gemini model identifier; included in safe evaluation metadata |
| `temperature` | number | Greater than zero; included in run metadata |
| `timeout_seconds` | positive number | Bounded network timeout |
| `max_attempts` | positive integer | Explicitly bounded retry policy |

Configuration is loaded from `PART-1B/.env` when present, then overlaid by process
environment variables. The `.env` file is local-only and ignored by Git.

## Evaluation Case and Report

An immutable, versioned evaluation case has a stable case ID, linked FR/NFR IDs, operation,
synthetic request, fixed context, expected response/properties, and dataset version. A report
contains only case IDs, run indexes, safe failure codes, metrics, thresholds, provider and
configuration metadata, available token counts, and the final pass/fail result. It excludes
raw request text, response text, API keys, and stack traces.

Each independently executed case/run produces one result with schema, property, semantic,
and traceability outcomes. A repeated model response is a distinct result; repeated outputs
are allowed and do not by themselves imply deterministic execution.

## Processing Lifecycle

`validated input -> Gemini request -> untrusted model response -> local property checks ->
canonical schema validation -> one JSON response`

Missing/ambiguous information is represented as a schema-valid clarification. Configuration,
transport, provider, or invalid-model-output failures are explicit operational errors; they
are not converted into clarification or successful actions.

The agent has no persistent reminder state and makes no reminder mutations.
