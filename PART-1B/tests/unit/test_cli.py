import json
from typing import Any

from reminder_agent import cli
from reminder_agent.config import ConfigurationError, Settings
from reminder_agent.gemini_client import ModelGeneration

VALID_RESPONSE = {
    "intent": "create",
    "task": "pay electricity bill",
    "datetime": "2026-11-20T18:00:00+05:30",
    "needs_clarification": False,
    "clarification_question": "",
}


class FakeAdapter:
    def __init__(self, response: dict[str, Any] | Exception) -> None:
        self.response = response
        self.calls = 0

    def generate(self, request: Any) -> ModelGeneration:
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return ModelGeneration(
            response=self.response,
            model_version="fake-model",
            response_id="fake-response",
            prompt_tokens=10,
            candidate_tokens=5,
            attempts=1,
        )


def _settings() -> Settings:
    return Settings(
        api_key="test-key-not-sent",
        model="gemini-3.5-flash-lite",
        temperature=0.3,
        timeout_seconds=30,
        max_attempts=2,
        max_calls=140,
    )


def test_TEST_CLI_PRINTS_ONE_JSON_RESPONSE(
    monkeypatch: Any,
    capsys: Any,
) -> None:
    adapter = FakeAdapter(dict(VALID_RESPONSE))
    monkeypatch.setattr(cli, "load_settings", _settings)
    monkeypatch.setattr(cli, "GeminiAdapter", lambda _: adapter)

    exit_code = cli.main(
        [
            "--text",
            "Remind me tomorrow at 6 PM to pay electricity bill.",
            "--reference-time",
            "2026-11-19T09:00:00+05:30",
            "--timezone",
            "Asia/Kolkata",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == VALID_RESPONSE
    assert captured.err == ""
    assert adapter.calls == 1


def test_TEST_CLI_SURFACES_CONFIGURATION_ERRORS_WITHOUT_REQUEST_TEXT(
    monkeypatch: Any,
    capsys: Any,
) -> None:
    secret_request = "private request text"

    def fail_settings() -> Settings:
        raise ConfigurationError("MISSING_API_KEY", "GEMINI_API_KEY is required.")

    monkeypatch.setattr(cli, "load_settings", fail_settings)

    exit_code = cli.main(["--text", secret_request])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "MISSING_API_KEY" in captured.err
    assert secret_request not in captured.err
    assert "Traceback" not in captured.err
