import json
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google import genai
from google.genai import errors

from reminder_agent.config import Settings
from reminder_agent.gemini_client import RATE_LIMIT_WAIT_SECONDS, GeminiAdapter, ProviderError
from reminder_agent.validation import validate_request

VALID_RESPONSE = {
    "intent": "create",
    "task": "pay electricity bill",
    "datetime": "2026-11-20T18:00:00+05:30",
    "needs_clarification": False,
    "clarification_question": "",
}


class FakeModels:
    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeClient:
    def __init__(self, outcomes: list[Any]) -> None:
        self.models = FakeModels(outcomes)


def _settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "api_key": "test-key-not-sent",
        "model": "gemini-3.5-flash-lite",
        "temperature": 0.3,
        "timeout_seconds": 30,
        "max_attempts": 2,
        "max_calls": 140,
    }
    values.update(overrides)
    return Settings(**values)


def _model_response(
    text: str | None = json.dumps(VALID_RESPONSE),
) -> SimpleNamespace:
    return SimpleNamespace(
        text=text,
        model_version="gemini-3.5-flash-lite",
        response_id="response-id",
        usage_metadata=SimpleNamespace(
            prompt_token_count=31,
            candidates_token_count=12,
        ),
    )


def _request() -> Any:
    return validate_request(
        {
            "text": "Remind me tomorrow at 6 PM to pay electricity bill.",
            "context": {
                "reference_time": "2026-11-19T09:00:00+05:30",
                "timezone": "Asia/Kolkata",
                "reminder_tasks": [],
            },
        }
    )


def test_TEST_GEMINI_CALL_USES_JSON_SCHEMA_AND_POSITIVE_TEMPERATURE() -> None:
    client = FakeClient([_model_response()])
    adapter = GeminiAdapter(_settings(), client=client)

    result = adapter.generate(_request())

    call = client.models.calls[0]
    assert call["model"] == "gemini-3.5-flash-lite"
    assert call["config"].temperature == 0.3
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].seed is None
    assert set(call["config"].response_schema["required"]) == {
        "intent",
        "task",
        "datetime",
        "needs_clarification",
        "clarification_question",
    }
    assert call["config"].tools is None
    assert result.response == VALID_RESPONSE
    assert result.prompt_tokens == 31
    assert result.candidate_tokens == 12


def test_TEST_GEMINI_CLIENT_USES_SETTINGS_WITHOUT_MAKING_A_REQUEST(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class ClientFactory:
        def __init__(self, *, api_key: str, http_options: Any) -> None:
            captured["api_key"] = api_key
            captured["http_options"] = http_options
            self.models = FakeModels([])

    monkeypatch.setattr(genai, "Client", ClientFactory)

    GeminiAdapter(_settings(api_key="local-test-key", timeout_seconds=1.5))

    assert captured["api_key"] == "local-test-key"
    assert captured["http_options"].timeout == 1500


def test_TEST_GEMINI_RETRIES_TRANSIENT_PROVIDER_FAILURES_ONLY() -> None:
    client = FakeClient([errors.APIError(429, {}), _model_response()])
    sleeps: list[float] = []
    adapter = GeminiAdapter(_settings(), client=client, sleep=sleeps.append)

    result = adapter.generate(_request())

    assert result.response == VALID_RESPONSE
    assert len(client.models.calls) == 2
    assert sleeps == [RATE_LIMIT_WAIT_SECONDS]


def test_TEST_GEMINI_SERVER_ERROR_RETRY_STAYS_SHORT() -> None:
    client = FakeClient([errors.APIError(503, {}), _model_response()])
    sleeps: list[float] = []
    adapter = GeminiAdapter(_settings(), client=client, sleep=sleeps.append)

    adapter.generate(_request())

    assert sleeps == [1]


def test_TEST_GEMINI_PACES_CALLS_TO_THE_CONFIGURED_MINIMUM_INTERVAL() -> None:
    client = FakeClient([_model_response(), _model_response(), _model_response()])
    sleeps: list[float] = []
    clock = iter([100.0, 101.0, 101.0, 110.0])
    adapter = GeminiAdapter(
        _settings(min_interval_seconds=5.0),
        client=client,
        sleep=sleeps.append,
        monotonic=lambda: next(clock),
    )

    for _ in range(3):
        adapter.generate(_request())

    # First call is immediate, second waits for the 4 s remaining, third is already late enough.
    assert sleeps == [4.0]
    assert len(client.models.calls) == 3


@pytest.mark.parametrize(
    ("status_code", "error_code"),
    [
        (408, "GEMINI_TIMEOUT_RETRY_EXHAUSTED"),
        (429, "GEMINI_RATE_LIMIT_RETRY_EXHAUSTED"),
        (503, "GEMINI_SERVER_RETRY_EXHAUSTED"),
    ],
)
def test_TEST_GEMINI_CLASSIFIES_RETRYABLE_HTTP_FAILURES_SAFELY(
    status_code: int,
    error_code: str,
) -> None:
    client = FakeClient([errors.APIError(status_code, {}) for _ in range(2)])
    adapter = GeminiAdapter(_settings(), client=client, sleep=lambda _: None)

    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == error_code
    assert error.value.attempts == 2
    assert len(client.models.calls) == 2


def test_TEST_GEMINI_REPEATED_CALLS_ARE_INDEPENDENT_AND_POSITIVE_TEMPERATURE() -> None:
    client = FakeClient([_model_response(), _model_response(), _model_response()])
    adapter = GeminiAdapter(_settings(), client=client)

    results = [adapter.generate(_request()) for _ in range(3)]

    assert len(results) == 3
    assert len(client.models.calls) == 3
    assert adapter.provider_attempts == 3
    assert all(call["config"].temperature > 0 for call in client.models.calls)
    assert all(call["config"].seed is None for call in client.models.calls)


def test_TEST_GEMINI_RETRIES_CANNOT_EXCEED_PROVIDER_ATTEMPT_BUDGET() -> None:
    client = FakeClient([errors.APIError(429, {}), _model_response()])
    adapter = GeminiAdapter(_settings(max_calls=1), client=client, sleep=lambda _: None)

    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == "CALL_BUDGET_EXHAUSTED"
    assert adapter.provider_attempts == 1
    assert len(client.models.calls) == 1


def test_TEST_GEMINI_CALLS_SHARE_PROVIDER_ATTEMPT_BUDGET() -> None:
    client = FakeClient([_model_response(), _model_response()])
    adapter = GeminiAdapter(_settings(max_calls=1), client=client)

    adapter.generate(_request())
    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == "CALL_BUDGET_EXHAUSTED"
    assert adapter.provider_attempts == 1
    assert len(client.models.calls) == 1


def test_TEST_GEMINI_DOES_NOT_RETRY_AUTHORIZATION_FAILURES() -> None:
    client = FakeClient([errors.APIError(403, {})])
    adapter = GeminiAdapter(_settings(), client=client, sleep=lambda _: None)

    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == "GEMINI_PROVIDER_ERROR"
    assert len(client.models.calls) == 1


def test_TEST_GEMINI_REDACTS_EXHAUSTED_TRANSPORT_FAILURES() -> None:
    client = FakeClient([httpx.TimeoutException("secret request details")] * 2)
    adapter = GeminiAdapter(_settings(), client=client, sleep=lambda _: None)

    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == "GEMINI_TIMEOUT_RETRY_EXHAUSTED"
    assert "secret request details" not in str(error.value)
    assert len(client.models.calls) == 2


def test_TEST_GEMINI_CLASSIFIES_NON_TIMEOUT_TRANSPORT_FAILURES() -> None:
    request = httpx.Request("GET", "https://example.com")
    client = FakeClient(
        [httpx.ConnectError("private transport details", request=request) for _ in range(2)]
    )
    adapter = GeminiAdapter(_settings(), client=client, sleep=lambda _: None)

    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == "GEMINI_TRANSPORT_RETRY_EXHAUSTED"
    assert "private transport details" not in str(error.value)
    assert len(client.models.calls) == 2


@pytest.mark.parametrize(
    ("text", "error_code"),
    [
        (None, "EMPTY_MODEL_RESPONSE"),
        ("not-json", "INVALID_MODEL_JSON"),
        ("[]", "INVALID_MODEL_JSON"),
    ],
)
def test_TEST_GEMINI_REJECTS_EMPTY_OR_NON_OBJECT_OUTPUT(
    text: str | None,
    error_code: str,
) -> None:
    adapter = GeminiAdapter(_settings(), client=FakeClient([_model_response(text)]))

    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == error_code


def test_TEST_GEMINI_SANITIZES_RESPONSE_TEXT_ACCESS_ERRORS() -> None:
    class BrokenResponse:
        @property
        def text(self) -> str:
            raise ValueError("private response details")

    adapter = GeminiAdapter(_settings(), client=FakeClient([BrokenResponse()]))

    with pytest.raises(ProviderError) as error:
        adapter.generate(_request())

    assert error.value.code == "EMPTY_MODEL_RESPONSE"
    assert error.value.attempts == 1
    assert "private response details" not in str(error.value)
