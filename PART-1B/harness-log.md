# Part 1B Harness Log — Gemini Reminder Agent

## Run summary

- **Date:** 2026-11-21
- **Environment:** Windows, Python 3.14.7
- **Status:** Offline verification passed. The Part 1B release evaluation is incomplete because
  the approved live Gemini development and held-out evaluations have not been run.

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

## Approved live-evaluation plan — not yet executed

- **Model:** `gemini-3.5-flash-lite`
- **Temperature:** `0.3`
- **Datasets:** 86 development cases and 20 held-out cases.
- **Repeat sample:** 12 selected development cases, each run three times total.
- **Planned combined runs:** 130; maximum provider attempts including retries: 140.
- **Release thresholds:** 100% schema validity; 100% deterministic property validity; at
  least 95% overall semantic accuracy; at least 90% semantic accuracy for each operation;
  and 100% clarification correctness.

No live provider calls, live evaluation report, token-usage totals, or empirical Gemini
accuracy results are available to report. The live development and held-out evaluations must
be run with a rotated credential configured locally. Do not treat the planned run counts or
thresholds above as observed results.

## Outcome and remaining work

The offline tests and configured local quality/security checks passed. Task T023 remains open
until the approved live development and held-out evaluations are completed and their actual
results are reviewed. This log records that limitation and does not claim Part 1B release
acceptance.