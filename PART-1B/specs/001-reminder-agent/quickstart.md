# Part 1B Quickstart

## Install

Use Python 3.11 or newer. From `PART-1B`, create/activate a virtual environment and install
the project with its development tools:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Ordinary tests and quality checks are offline and do not require a Gemini key:

```powershell
python -m pytest
python -m pytest --cov --cov-branch --cov-report=term-missing
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src\reminder_agent
python -m bandit -q -r src\reminder_agent
detect-secrets scan -n
python -m pip_audit
```

## Configure Gemini locally

The credential previously pasted into chat must be rotated. Configure its replacement only
on the local machine, either in the ignored `PART-1B\.env` file or in process environment
variables. The process environment takes precedence.

```dotenv
GEMINI_API_KEY=replace-with-a-rotated-key
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TEMPERATURE=0.3
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_ATTEMPTS=2
GEMINI_MAX_CALLS=140
```

Never commit `.env`, paste credentials into source, or put raw requests/responses in a report.
The adapter logs neither request text nor credentials; generated evaluation reports contain
case IDs, safe error codes, configuration metadata, metrics, and available token totals.

## Process one request

The command prints one JSON response on success. Candidate reminders are supplied explicitly
when rescheduling or snoozing:

```powershell
reminder-agent --text "Remind me tomorrow at 6 PM to pay electricity bill." `
  --reference-time "2026-11-19T09:00:00+05:30" --timezone "Asia/Kolkata"
```

Repeat `--reminder-task` for each candidate target. The agent has no persistence,
notification, or reminder-mutation tools. Invalid local request context returns a
schema-valid clarification without calling Gemini. Configuration, provider, and invalid
model-output failures exit non-zero with a safe error code rather than a fabricated action.

## Run the evaluation

The versioned synthetic corpus contains 86 development cases and 20 held-out cases. Combined
evaluation makes 130 planned runs: all 106 cases once, plus 12 model-eligible development
cases run three times total. The provider-attempt ceiling is 140 including retries; locally
rejected inputs do not consume provider attempts.

```powershell
reminder-agent-evaluate --mode combined --report evidence\evaluation-report.json
```

`--mode development` evaluates the development set and its repeated sample; `--mode held-out`
evaluates the held-out set once. If the provider-attempt budget is exhausted, the command
returns a non-zero status and writes a privacy-safe partial report alongside the requested
report path with the suffix `.incomplete`. Partial reports include only completed case IDs,
safe failure codes, and available metrics; they do not claim threshold results.

The thresholds are 100% schema validity, 100% deterministic property validity, at least 95%
overall semantic accuracy, at least 90% semantic accuracy for each operation, and 100%
clarification correctness. Schema, property, semantic, and per-operation metrics are kept
separate; outputs are not averaged into one score. The JSON report records dataset/schema/
prompt versions, model and temperature, run and provider-attempt counts, available token
usage, per-case safe codes, traceability coverage, thresholds, and pass/fail. It never writes
raw request text, response content, or API credentials.

See [spec.md](./spec.md) for the response contract, date/time and target rules, approved
configuration, and acceptance criteria. See [traceability.md](./traceability.md) and
[`data/evaluation/traceability.json`](../../data/evaluation/traceability.json) for the
requirement-to-case/test/source mapping.
