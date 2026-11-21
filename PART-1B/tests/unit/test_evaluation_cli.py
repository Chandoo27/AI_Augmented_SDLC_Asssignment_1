import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from reminder_agent import evaluation_cli
from reminder_agent.config import Settings
from reminder_agent.evaluation import (
    EvaluationInputError,
    EvaluationProgress,
    load_cases,
)
from reminder_agent.models import EvaluationResult


def _settings() -> Settings:
    return Settings(
        api_key="test-key-not-sent",
        model="gemini-3.5-flash-lite",
        temperature=0.3,
        timeout_seconds=30,
        max_attempts=2,
        max_calls=140,
    )


def test_TEST_EVALUATION_CLI_COMBINED_MODE_USES_APPROVED_REPEAT_SAMPLE(
    monkeypatch: Any,
    capsys: Any,
    tmp_path: Path,
) -> None:
    captured: dict[str, Any] = {}
    report = SimpleNamespace(
        passed=True,
        failed_thresholds=(),
        call_count=123,
        total_runs=130,
    )
    monkeypatch.setattr(evaluation_cli, "load_settings", _settings)
    monkeypatch.setattr(evaluation_cli, "GeminiAdapter", lambda _: object())
    monkeypatch.setattr(evaluation_cli, "ReminderAgent", lambda _: object())

    def fake_run_evaluation(cases: Any, agent: Any, **kwargs: Any) -> Any:
        captured["case_count"] = len(cases)
        captured.update(kwargs)
        return report

    monkeypatch.setattr(evaluation_cli, "run_evaluation", fake_run_evaluation)
    monkeypatch.setattr(
        evaluation_cli,
        "write_report",
        lambda value, path: captured.update({"written_report": value, "path": path}),
    )
    report_path = tmp_path / "evaluation.json"

    exit_code = evaluation_cli.main(["--mode", "combined", "--report", str(report_path)])

    captured_output = capsys.readouterr()
    summary = json.loads(captured_output.out)
    assert exit_code == 0
    assert captured["case_count"] == 106
    assert len(captured["repeated_case_ids"]) == 12
    assert captured["command"] == "combined"
    assert captured["max_calls"] == 140
    assert captured["written_report"] is report
    assert captured["path"] == report_path
    assert summary["provider_attempts"] == 123
    assert captured_output.err == ""


def test_TEST_EVALUATION_CLI_WRITES_SAFE_INCOMPLETE_REPORT_ON_BUDGET_EXHAUSTION(
    monkeypatch: Any,
    capsys: Any,
    tmp_path: Path,
) -> None:
    cases = load_cases(evaluation_cli.DEVELOPMENT_DATASET)
    completed = EvaluationResult(
        case_id=cases[0].case_id,
        run_index=0,
        operation=cases[0].operation,
        category=cases[0].category,
        schema_valid=True,
        property_valid=True,
        semantic_correct=True,
        model_version="gemini-test-version",
        prompt_tokens=10,
        candidate_tokens=5,
    )
    progress = EvaluationProgress(
        planned_runs=130,
        completed_runs=1,
        provider_attempts=140,
        results=(completed,),
        stopped_case_id=cases[1].case_id,
        stopped_run_index=0,
    )
    error = EvaluationInputError(
        "CALL_BUDGET_EXHAUSTED",
        "Evaluation stopped because the provider-attempt budget was exhausted.",
        attempts=140,
        progress=progress,
    )
    monkeypatch.setattr(evaluation_cli, "load_settings", _settings)
    monkeypatch.setattr(evaluation_cli, "GeminiAdapter", lambda _: object())
    monkeypatch.setattr(evaluation_cli, "ReminderAgent", lambda _: object())

    def fail_evaluation(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(evaluation_cli, "run_evaluation", fail_evaluation)
    report_path = tmp_path / "evaluation.json"

    exit_code = evaluation_cli.main(["--mode", "combined", "--report", str(report_path)])

    captured_output = capsys.readouterr()
    incomplete_path = report_path.with_name("evaluation.incomplete.json")
    serialized = incomplete_path.read_text(encoding="utf-8")
    failure_report = json.loads(serialized)
    assert exit_code == 2
    assert "ERROR: CALL_BUDGET_EXHAUSTED" in captured_output.err
    assert str(incomplete_path) in captured_output.err
    assert failure_report["status"] == "incomplete"
    assert failure_report["passed"] is False
    assert failure_report["total_cases"] == 106
    assert failure_report["planned_runs"] == 130
    assert failure_report["completed_runs"] == 1
    assert failure_report["provider_attempts"] == 140
    assert failure_report["threshold_status"] == "NOT_EVALUATED_INCOMPLETE"
    assert cases[0].request_payload["text"] not in serialized
    assert _settings().api_key not in serialized
