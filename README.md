# AI-Augmented SDLC: Assignment 1 (Spec-Driven Development and Harness Engineering)

Two small applications built with the GitHub Spec Kit workflow and checked by a harness that is
independent of the generated code.

| Folder | Application | Kind |
|---|---|---|
| `PART-1A/` | Smart Todo API (FastAPI, local JSON storage) | Deterministic |
| `PART-1B/` | Gemini Reminder Agent (natural-language reminders, model `gemini-3.5-flash-lite`) | Non-deterministic |

## Use of AI assistance

This assignment was developed with help from AI. Claude (through Claude Code) was used as a
coding agent to draft the Spec Kit artifacts and to write implementation, test and harness code,
under the student's direction and review. The harness logs and the reflection answers are
written by the student from the real evidence, as the assignment requires.

## Part 1A

- Spec, plan, tasks, analysis and traceability: `PART-1A/specs/001-smart-todo-api/`
- Harness: `PART-1A/scripts/run_harness.py` runs six gates (pytest with 80% coverage, Ruff
  check, Ruff format, Bandit, pip-audit, secret scan). Results are kept in
  `PART-1A/evidence/harness-runs/`.
- Evidence: `PART-1A/evidence/initial-generation/` (last committed source before the first
  harness run), `final-generation/`, and the log `PART-1A/evidence/harness-log.md`.
- Run (from `PART-1A`): `python -m pip install -e ".[dev]"` then `python scripts/run_harness.py`.

## Part 1B

- Spec (response contract, invariants, guardrails, thresholds), plan, tasks, analysis,
  amendments: `PART-1B/specs/001-reminder-agent/`
- Datasets: `PART-1B/evals/` (86 development and 20 held-out cases, plus the traceability
  manifest). Evaluators and the runner: `PART-1B/src/reminder_agent/evaluation.py` and
  `evaluation_cli.py` (schema, property and semantic layers; no model as judge).
- Evidence: `PART-1B/evidence/eval-runs/run-1` to `run-6`, `eval-results.json` (the passing
  report, a copy of run 6), `fresh-check/`, `initial-generation/`, `final-generation/`, and the
  log `PART-1B/evidence/harness-log.md`.
- Offline tests need no key. The live evaluation needs `GEMINI_API_KEY` in `PART-1B/.env`
  (copy `.env.example`; the file is ignored by Git and must never be committed).
- Run (from `PART-1B`): `python -m pip install -e ".[dev]"`, `python -m pytest`, then
  `reminder-agent-evaluate --mode combined --report evidence/eval-runs/run-N/evaluation-report.json`.
  One evaluation makes up to 200 provider attempts, so a free-tier key (500 requests a day)
  allows about three runs a day.
