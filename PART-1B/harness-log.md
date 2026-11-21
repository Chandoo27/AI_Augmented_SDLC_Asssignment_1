# Part 1B Harness Log — Gemini Reminder Agent

## Run summary

- **Date:** 2026-11-21
- **Environment:** Windows, Python 3.14.7
- **Status:** Offline verification passed. Three combined live attempts stopped at the
  configured provider-attempt ceiling; live acceptance remains incomplete.

## Offline verification results

- **Tests:** 116 passed.
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

Three combined attempts were made on 2026-11-21 with the approved 140 provider-attempt
ceiling. All exited with `CALL_BUDGET_EXHAUSTED` before the planned evaluation completed.
The first two attempts did not write reports. The third, using the instrumented runner, wrote
`evidence/evaluation-report.incomplete.json`: 97 of 130 planned runs were recorded before 140
provider attempts were consumed. The run stopped at `EV-SNOOZE-011`, run index 1.

Among the 97 recorded run results, safe failure-code occurrences were `GEMINI_RETRY_EXHAUSTED`
(42), `INVALID_MODEL_ACTION` (3), and `SEMANTIC_MISMATCH` (9). The partial counts were 52
schema-valid, 52 property-valid, and 43 semantically correct. The report marks threshold
status `NOT_EVALUATED_INCOMPLETE`; these partial counts are not acceptance scores. It records
13,807 prompt tokens and 2,820 candidate tokens from completed results only; these totals do
not cover failed attempts or the two earlier runs. The safe retry code does not distinguish
HTTP rate limits, server errors, or transport timeouts, so the precise cause remains unknown.
Do not treat the planned run counts or thresholds above as observed results.

A separately authorized diagnostic request between the first and second combined attempts
succeeded in one provider attempt, and its response passed local action validation. The three
combined attempts and the diagnostic used 421 provider attempts in total. The diagnostic
confirms that a single request can reach the provider; it is not part of the evaluation corpus
and does not replace the required live development/held-out metrics or identify why the
combined runs exhausted their budgets.

## Outcome and remaining work

The offline tests and configured local quality/security checks passed, but no combined live
run produced complete acceptance evidence. The diagnostic was successful but does not satisfy
release criteria. Task T023 remains open until the retry failures are diagnosed and the
approved development and held-out evaluation completes with a privacy-safe report whose
actual metrics meet the thresholds. This log does not claim Part 1B release acceptance.