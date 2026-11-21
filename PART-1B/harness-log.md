# Part 1B Harness Log — Gemini Reminder Agent

## Run summary

- **Date:** 2026-11-21
- **Environment:** Windows, Python 3.14.7
- **Status:** Offline verification passed. Four combined live attempts stopped at the
  configured provider-attempt ceiling; live acceptance remains incomplete.

## Offline verification results

- **Tests:** 120 passed.
- **Core coverage:** 94.92%, above the configured 90% minimum.
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

Four combined attempts were made on 2026-11-21 with the approved 140 provider-attempt
ceiling. All exited with `CALL_BUDGET_EXHAUSTED` before the planned evaluation completed.
The first two attempts did not write reports. The third wrote
`evidence/evaluation-report.incomplete.json` with 97 of 130 planned runs. The fourth, using
safe provider-error classification, wrote
`evidence/evaluation-report-final.incomplete.json` with 111 of 130 planned runs before all 140
provider attempts were consumed.

Among the fourth attempt's 111 recorded run results, safe failure-code occurrences were
`GEMINI_RATE_LIMIT_RETRY_EXHAUSTED` (22), `GEMINI_SERVER_RETRY_EXHAUSTED` (1),
`GEMINI_TIMEOUT_RETRY_EXHAUSTED` (1), `INVALID_MODEL_ACTION` (5), and
`SEMANTIC_MISMATCH` (18). Its partial counts were 82 schema-valid, 82 property-valid, and 64
semantically correct. The report marks threshold status `NOT_EVALUATED_INCOMPLETE`; these
partial counts are not acceptance scores. It records 22,632 prompt tokens and 4,494 candidate
tokens from completed results only; these do not cover failed attempts or previous runs.

A separately authorized diagnostic request between the first and second combined attempts
succeeded in one provider attempt, and its response passed local action validation. The four
combined attempts and diagnostic used 561 provider attempts in total. The diagnostic confirms
that a single request can reach the provider; it is not part of the evaluation corpus and does
not replace the required live development/held-out metrics. The latest report identifies
rate-limit retries as the largest categorized failure group, but the incomplete run does not
establish release accuracy or threshold status.

## Outcome and remaining work

The offline tests and configured local quality/security checks passed, but no combined live
run produced complete acceptance evidence. The diagnostic was successful but does not satisfy
release criteria. Task T023 remains open until provider rate-limit failures are resolved and
the approved development and held-out evaluation completes with a privacy-safe report whose
actual metrics meet the thresholds. This log does not claim Part 1B release acceptance.