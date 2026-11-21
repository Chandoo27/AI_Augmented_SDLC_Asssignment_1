from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 300
GATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pytest", ("-m", "pytest")),
    ("ruff-check", ("-m", "ruff", "check", "src", "tests", "scripts")),
    ("ruff-format", ("-m", "ruff", "format", "--check", "src", "tests", "scripts")),
    ("bandit", ("-m", "bandit", "-q", "-r", "src")),
    ("pip-audit", ("-m", "pip_audit", "--skip-editable")),
    ("secret-scan", (sys.executable, "scripts/check_secrets.py")),
)


@dataclass(frozen=True)
class GateResult:
    name: str
    command: tuple[str, ...]
    status: Literal["PASS", "FAIL"]
    return_code: int | None
    stdout: str
    stderr: str
    error: str | None = None


def _as_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def execute_gate(
    name: str,
    command: tuple[str, ...],
    cwd: Path = ROOT,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> GateResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        return GateResult(
            name=name,
            command=command,
            status="FAIL",
            return_code=None,
            stdout=_as_text(error.stdout),
            stderr=_as_text(error.stderr),
            error=f"TIMEOUT after {timeout_seconds} seconds",
        )
    except FileNotFoundError as error:
        return GateResult(
            name=name,
            command=command,
            status="FAIL",
            return_code=127,
            stdout="",
            stderr="",
            error=f"COMMAND_NOT_FOUND: {error}",
        )

    return GateResult(
        name=name,
        command=command,
        status="PASS" if completed.returncode == 0 else "FAIL",
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def write_report(results: list[GateResult], output_directory: Path) -> Path:
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_directory = output_directory / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    report_path = run_directory / "results.json"
    report = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "created_utc": datetime.now(UTC).isoformat(),
        "passed": all(result.status == "PASS" for result in results),
        "gates": [asdict(result) for result in results],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    results = [execute_gate(name, (sys.executable, *arguments)) for name, arguments in GATES]
    for result in results:
        print(f"{result.name}: {result.status}")

    report_path = write_report(results, ROOT / "evidence" / "harness-runs")
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0 if all(result.status == "PASS" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
