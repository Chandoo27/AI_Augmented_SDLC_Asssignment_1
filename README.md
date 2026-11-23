# AI-Augmented SDLC: Assignment 1
## Spec-Driven Development and Harness Engineering

This repository contains two applications developed using the GitHub Spec Kit workflow and evaluated using harnesses that are independent of the generated code. The work demonstrates specification-driven development, traceability from requirements to implementation, automated validation, and evidence-based acceptance decisions.

| Folder | Application | Type |
|----------|------------|----------|
| `PART-1A/` | Smart Todo API (FastAPI with local JSON persistence) | Deterministic |
| `PART-1B/` | Gemini Reminder Agent (`gemini-3.5-flash-lite`) | Non-deterministic |

---

# Use of AI Assistance

This assignment was developed with the assistance of AI. Claude (through Claude Code) was used as a coding agent to draft specification artifacts, implementation code, test suites, and harness components under student direction and review.

The final acceptance decisions, harness logs, evaluation analysis, and reflection content were prepared by the student using the collected evidence generated throughout the development and evaluation process.

---

# Repository Overview

Both parts follow a specification-led workflow:

1. Constitution
2. Requirements Specification
3. Clarifications
4. Planning
5. Task Breakdown
6. Analysis
7. Implementation
8. Independent Validation
9. Evidence Collection
10. Human Acceptance Review

All requirements are traced through specifications, tests, evaluation artifacts, and implementation references.

---

# Part 1A – Smart Todo API

A REST API implemented using FastAPI with JSON-file persistence.

## Features

- Create tasks
- Retrieve tasks
- Update tasks
- Delete tasks
- Filter by status, priority, and tags
- Sort results
- Mark tasks complete
- Reopen completed tasks

## Specification Artifacts

Located in:

```text
PART-1A/specs/001-smart-todo-api/
```

This folder contains:

- `spec.md`
- `plan.md`
- `tasks.md`
- `research.md`
- `data-model.md`
- `quickstart.md`
- `analysis.md`
- `traceability.md`

## Test and Harness Configuration

Harness:

```text
PART-1A/scripts/run_harness.py
```

Validation gates:

1. Pytest (minimum 80% coverage)
2. Ruff check
3. Ruff format
4. Bandit security scan
5. pip-audit dependency audit
6. Secret scan

## Evidence

```text
PART-1A/evidence/
```

Contents:

```text
initial-generation/
final-generation/
harness-runs/
harness-log.md
```

### Final Result

- 42 automated tests passed
- 92.42% coverage achieved
- Performance requirement satisfied
- All six harness gates passed

## Running Part 1A

From the `PART-1A` directory:

```bash
python -m pip install -e ".[dev]"
python scripts/run_harness.py
```

---

# Part 1B – Gemini Reminder Agent

A natural-language reminder assistant powered by Gemini.

The application converts reminder requests into structured JSON actions while enforcing a strict validation contract and safety rules.

## Model Configuration

Model:

```text
gemini-3.5-flash-lite
```

Temperature:

```text
0.3
```

Supported intents:

- create
- reschedule
- snooze
- clarification

Response contract:

```json
{
  "intent": "",
  "task": "",
  "datetime": "",
  "needs_clarification": false,
  "clarification_question": ""
}
```

## Specification Artifacts

Located in:

```text
PART-1B/specs/001-reminder-agent/
```

Contents include:

- `spec.md`
- `plan.md`
- `tasks.md`
- `analysis.md`
- `amendments.md`
- `quickstart.md`
- `traceability.md`

## Evaluation Framework

Datasets:

```text
PART-1B/evals/
```

Dataset composition:

- 86 development cases
- 20 held-out cases
- Traceability manifest

Evaluation components:

```text
PART-1B/src/reminder_agent/evaluation.py
PART-1B/src/reminder_agent/evaluation_cli.py
```

The evaluation consists of:

1. Schema validation
2. Property validation
3. Semantic validation

No model is used as an evaluator.

## Evidence

```text
PART-1B/evidence/
```

Contents:

```text
initial-generation/
final-generation/
eval-runs/
eval-results.json
fresh-check/
harness-log.md
```

### Evaluation History

Formal evaluations:

```text
run-1
run-2
run-3
run-4
run-5
run-6
```

Final accepted evaluation:

```text
eval-results.json
```

(copy of Run 6)

### Final Result

- 138 automated tests passed
- 95.55% branch coverage
- Ruff passed
- mypy passed
- Bandit passed
- Run 6 satisfied all approved evaluation thresholds
- Fresh-check achieved 14/14 correct responses

## Credentials

Offline tests require no API key.

Live evaluation requires:

```text
GEMINI_API_KEY
```

stored in:

```text
PART-1B/.env
```

Create the file by copying:

```text
.env.example
```

The `.env` file is ignored by Git and must never be committed.

## Running Part 1B

From the `PART-1B` directory:

```bash
python -m pip install -e ".[dev]"
python -m pytest
reminder-agent-evaluate --mode combined --report evidence/eval-runs/run-N/evaluation-report.json
```

One evaluation can make up to 200 provider attempts. With a free-tier Gemini key (500 requests/day), approximately three full evaluation runs can be performed per day.

---

# Acceptance Summary

| Part | Status |
|--------|--------|
| Part 1A – Smart Todo API | ACCEPTED |
| Part 1B – Gemini Reminder Agent | ACCEPTED |

Acceptance decisions are documented in:

```text
PART-1A/evidence/harness-log.md
PART-1B/evidence/harness-log.md
```

and are supported by the associated harness results, evaluation reports, traceability evidence, and final validation artifacts contained within each project directory.