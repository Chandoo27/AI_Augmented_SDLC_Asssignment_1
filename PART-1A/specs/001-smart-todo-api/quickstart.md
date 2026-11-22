# Quickstart

## Prerequisites

- Python 3.11 or newer
- A virtual environment
- A writable local JSON file location

## Setup

```powershell
cd PART-1A
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:SMART_TODO_DATA_FILE = Join-Path (Get-Location) "data\tasks.json"
```

`SMART_TODO_DATA_FILE` is optional; when unset, the API uses `data/tasks.json` relative to the
Part 1A working directory. The file path is application configuration and is never read from
request input. Run one server worker at a time; JSON mutation locking is process-local.

## Run

```powershell
python -m uvicorn src.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for generated OpenAPI documentation.

## API Contract

The checked-in [OpenAPI contract](./contracts/tasks.openapi.yaml) defines the v1 request and
response shapes. The generated FastAPI schema is available at `/openapi.json`.

| Operation | Route | Success |
|---|---|---|
| Create | `POST /tasks` | `201` with the created task |
| List | `GET /tasks` | `200` with all tasks or filtered results |
| Retrieve | `GET /tasks/{task_id}` | `200` with the task |
| Partial update | `PATCH /tasks/{task_id}` | `200` with the updated task |
| Delete | `DELETE /tasks/{task_id}` | `204` with no body |
| Complete | `POST /tasks/{task_id}/complete` | `200` with `Completed` status |
| Reopen | `POST /tasks/{task_id}/reopen` | `200` with `Pending` status |

Task IDs are UUIDs. Titles, descriptions, priorities, and tags are validated before storage;
status changes only through the complete/reopen operations. List filters accept repeated
`tags` parameters or comma-separated tags and use case-insensitive exact match-any semantics.
`sort=priority` orders High, Medium, Low, with creation time and UUID as deterministic tie
breakers. Validation errors use HTTP `422`, unknown tasks use `404`, and local data failures
use `500`; each error has `code`, `message`, and `details`.

## Validation Scenarios

Create a task:

```powershell
$body = @{title="Ship release"; description="Prepare notes"; priority="High"; tags=@("work","release")} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/tasks" -ContentType "application/json" -Body $body
```

Expected: HTTP 201 with a UUID, UTC `createdAt`, `Pending` status, and normalized tags.

Update and retrieve:

```powershell
$body = @{title="Ship release today"} | ConvertTo-Json
Invoke-RestMethod -Method Patch -Uri "http://127.0.0.1:8000/tasks/<task-id>" -ContentType "application/json" -Body $body
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/tasks/<task-id>"
```

Expected: HTTP 200; only the supplied editable field changes.

Filter and sort:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/tasks?tags=work,release&sort=priority"
```

Expected: tasks matching at least one tag, ordered High then Medium then Low.

Complete and reopen:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/tasks/<task-id>/complete"
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/tasks/<task-id>/reopen"
```

Expected: HTTP 200 with `Completed`, then HTTP 200 with `Pending`.

Delete and verify:

```powershell
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/tasks/<task-id>"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/tasks/<task-id>"
```

Expected: HTTP 204, then HTTP 404 with the stable error shape.

## Automated Checks

```powershell
python scripts/run_harness.py
```

On Windows, the same runner is available through
`.\.harness\run_harness.ps1`.

The runner executes every gate even if an earlier gate fails, stores each command and its
stdout/stderr under `evidence/harness-runs/`, and exits non-zero if any gate fails. Do not edit
generated reports. The runner includes pytest with an 80% coverage floor, Ruff lint and
format checks, Bandit, pip-audit, and secret scanning.

Run only the performance acceptance test and preserve its properties:

```powershell
New-Item -ItemType Directory -Path "evidence\performance" -Force | Out-Null
python -m pytest -o addopts='' -o junit_family=legacy -p no:cov -m performance --junitxml=evidence/performance/part-1a-performance.xml
```

The baseline measurement on this machine was **100 of 100 requests under one second** for a
1,000-task collection. Machine: Microsoft Windows 11 Home Single Language, Intel(R) Core(TM)
Ultra 5 225H, Python 3.14.7. The full harness evaluates the threshold again on the machine that
runs it.

## Scope and Limitations

This is a local, single-user, file-backed API. It does not provide authentication, notifications,
multi-user support, or cloud persistence. File mutation locks are process-local, so run one
server worker per data file.

## Fresh Checkout

From the repository root, create a clean checkout and install the Part 1A package using the
commands in this quickstart. Then run `python scripts/run_harness.py` from `PART-1A`. The
generated report is evidence; the student-authored log is `evidence/harness-log.md`.
