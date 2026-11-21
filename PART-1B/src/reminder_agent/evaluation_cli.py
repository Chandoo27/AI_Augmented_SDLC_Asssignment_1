import argparse
import json
import sys
from pathlib import Path
from typing import Any

from reminder_agent.config import ConfigurationError, Settings, load_settings
from reminder_agent.engine import ReminderAgent
from reminder_agent.evaluation import (
    DEFAULT_THRESHOLDS,
    EvaluationInputError,
    load_cases,
    run_evaluation,
    select_repeat_case_ids,
    write_incomplete_report,
    write_report,
)
from reminder_agent.gemini_client import GeminiAdapter
from reminder_agent.models import EvaluationCase
from reminder_agent.prompt import PROMPT_VERSION

ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT_DATASET = ROOT / "data" / "evaluation" / "v1.jsonl"
HELDOUT_DATASET = ROOT / "data" / "evaluation" / "heldout-v1.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reminder-agent-evaluate")
    parser.add_argument(
        "--mode",
        choices=("development", "held-out", "combined"),
        default="combined",
        help="Evaluation dataset selection.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("evidence/evaluation-report.json"),
        help="Path for the privacy-safe JSON report.",
    )
    args = parser.parse_args(argv)

    settings: Settings | None = None
    cases: tuple[EvaluationCase, ...] = ()
    incomplete_path: Path | None = None
    try:
        settings = load_settings()
        development = (
            load_cases(DEVELOPMENT_DATASET) if args.mode in {"development", "combined"} else ()
        )
        heldout = load_cases(HELDOUT_DATASET) if args.mode in {"held-out", "combined"} else ()
        cases = (*development, *heldout)
        repeat_ids = (
            select_repeat_case_ids(development) if args.mode in {"development", "combined"} else ()
        )
        report = run_evaluation(
            cases,
            ReminderAgent(GeminiAdapter(settings)),
            model=settings.model,
            temperature=settings.temperature,
            prompt_version=PROMPT_VERSION,
            max_calls=settings.max_calls,
            repeated_case_ids=repeat_ids,
            command=args.mode,
            thresholds=DEFAULT_THRESHOLDS,
        )
        write_report(report, args.report)
    except ConfigurationError as error:
        _write_error(error.code)
        return 2
    except EvaluationInputError as error:
        if error.progress is not None and settings is not None:
            incomplete_path = args.report.with_name(
                f"{args.report.stem}.incomplete{args.report.suffix}"
            )
            try:
                write_incomplete_report(
                    error,
                    incomplete_path,
                    cases=cases,
                    model=settings.model,
                    temperature=settings.temperature,
                    prompt_version=PROMPT_VERSION,
                    command=args.mode,
                    max_calls=settings.max_calls,
                    thresholds=DEFAULT_THRESHOLDS,
                )
            except (EvaluationInputError, OSError):
                _write_error("INCOMPLETE_REPORT_WRITE_ERROR")
                return 2
        _write_error(error.code)
        if incomplete_path is not None:
            sys.stderr.write(f"PARTIAL_REPORT: {incomplete_path}\n")
        return 2
    except OSError:
        _write_error("REPORT_WRITE_ERROR")
        return 2

    summary: dict[str, Any] = {
        "passed": report.passed,
        "report": str(args.report),
        "failed_thresholds": list(report.failed_thresholds),
        "provider_attempts": report.call_count,
        "evaluation_runs": report.total_runs,
    }
    print(json.dumps(summary, separators=(",", ":"), sort_keys=True))
    return 0 if report.passed else 1


def _write_error(code: str) -> None:
    safe_code = code if code.isascii() and code.replace("_", "").isalnum() else "EVALUATION_ERROR"
    sys.stderr.write(f"ERROR: {safe_code}\n")


if __name__ == "__main__":
    raise SystemExit(main())
