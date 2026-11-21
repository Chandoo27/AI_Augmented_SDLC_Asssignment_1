import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from reminder_agent import evaluation_cli
from reminder_agent.config import Settings


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
