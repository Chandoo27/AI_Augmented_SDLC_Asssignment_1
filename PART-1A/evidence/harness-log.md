# Part 1A Harness Log — Smart Todo API

## Run summary

- **Date:** 2026-11-21
- **Environment:** Windows 11 Home Single Language, Intel Core Ultra 5 225H, Python 3.14.7
- **Command:** `python scripts/run_harness.py` from `PART-1A`
- **Final status:** Passed. All six configured harness gates passed in each of the final three runs.

## Final verification results

- **Tests and coverage:** 42 tests passed; 92.42% line coverage, above the configured 80% minimum.
- **Ruff lint:** Passed.
- **Ruff format:** Passed.
- **Bandit:** Passed.
- **pip-audit:** Passed with no known vulnerabilities reported. The local editable `smart-todo-api` package was skipped by pip-audit.
- **Secret scan:** Passed; no secrets detected.

The first two harness runs exposed gate failures during the verification process. After those
issues were addressed, the following three complete runs passed all gates:

- `evidence/harness-runs/20261121T084843454725Z/results.json`
- `evidence/harness-runs/20261121T085120441932Z/results.json`
- `evidence/harness-runs/20261121T120154015745Z/results.json` (latest recorded run)

## Performance acceptance

The documented baseline measured 100 of 100 requests under one second against a 1,000-task
collection on the machine listed above. The performance acceptance criterion is at least 95
of 100 measured requests under one second. See `specs/001-smart-todo-api/quickstart.md` for
the dedicated performance-test command and machine details.

## Outcome

The recorded final harness run satisfies the configured automated test, coverage, quality,
and security gates for Part 1A.