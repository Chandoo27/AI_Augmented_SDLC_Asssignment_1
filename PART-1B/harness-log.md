# Part 1B Harness Log — Gemini Reminder Agent

## Run summary

- **Date:** 2026-11-21
- **Environment:** Windows, Python 3.14.7
- **Status:** Offline verification passed. A combined live evaluation was attempted but stopped
  at the configured provider-attempt ceiling; live acceptance remains incomplete.

## Offline verification results

- **Tests:** 115 passed.
- **Core coverage:** 95.54%, above the configured 90% minimum.
- **Ruff formatting:** Passed.
- **Ruff lint:** Passed.
- **mypy:** Passed.
- **Bandit:** Passed.
- **Secret scan:** Passed with zero findings on tracked project files.
- **pip-audit:** No known vulnerabilities reported. The local `gemini-reminder-agent` package
  was skipped because it is not published on PyPI.
- **CLI checks:** Both the single-request and evaluation commands displayed their help
  successfully.

The offline suite and configured quality/security checks were rerun on 2026-11-21 and passed
again. Pytest emitted one upstream `google-genai` deprecation warning under Python 3.14; it
did not cause a test or quality gate to fail.

The offline integration tests exercise the evaluation workflow with deterministic fake model
responses, including the planned 106-case, 130-run combined evaluation. This verifies the
evaluation implementation; it is not a live Gemini evaluation and does not establish model
accuracy.

## Live evaluation attempt — incomplete

- **Model:** `gemini-3.5-flash-lite`
- **Temperature:** `0.3`
- **Datasets:** 86 development cases and 20 held-out cases.
- **Repeat sample:** 12 selected development cases, each run three times total.
- **Planned combined runs:** 130; maximum provider attempts including retries: 140.
- **Release thresholds:** 100% schema validity; 100% deterministic property validity; at
  least 95% overall semantic accuracy; at least 90% semantic accuracy for each operation;
  and 100% clarification correctness.

Two combined attempts were made on 2026-11-21, each with the approved 140 provider-attempt
ceiling. Both exited with `CALL_BUDGET_EXHAUSTED` before all planned evaluation runs
completed. Neither run wrote an evaluation report, so there are no valid aggregate metrics,
token totals, or empirical Gemini accuracy results to report. The CLI exposed only the safe
budget-exhaustion code; it did not retain per-case details that would explain why the attempt
budget was consumed or whether individual responses were usable. Do not treat the planned run
counts or thresholds above as observed results.

A separately authorized diagnostic request between the two runs succeeded in one provider
attempt, and its response passed local action validation. The two combined attempts and the
diagnostic used 281 provider attempts in total. The diagnostic confirms that a single request
can reach the provider; it is not part of the evaluation corpus and does not replace the
required live development/held-out metrics or identify why both combined runs exhausted
their budgets.

## Outcome and remaining work

The offline tests and configured local quality/security checks passed, but neither live run
produced acceptance evidence. The diagnostic was successful but does not satisfy release
criteria. Task T023 remains open until the repeated attempt-budget failure is diagnosed and
the approved development and held-out evaluation completes with a privacy-safe report whose
actual metrics meet the thresholds. This log does not claim Part 1B release acceptance.