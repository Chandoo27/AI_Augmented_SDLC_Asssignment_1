from typing import Any

import pytest

from reminder_agent.engine import PipelineError, ReminderAgent
from reminder_agent.gemini_client import ModelGeneration, ProviderError
from reminder_agent.output import serialize_response

VALID_RESPONSE = {
    "intent": "create",
    "task": "pay electricity bill",
    "datetime": "2026-11-20T18:00:00+05:30",
    "needs_clarification": False,
    "clarification_question": "",
}


class FakeGenerator:
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


def _request(**overrides: Any) -> dict[str, Any]:
    context = {
        "reference_time": "2026-11-19T09:00:00+05:30",
        "timezone": "Asia/Kolkata",
        "reminder_tasks": ["pay electricity bill"],
    }
    context.update(overrides.pop("context", {}))
    return {
        "text": "Remind me tomorrow at 6 PM to pay electricity bill.",
        "context": context,
        **overrides,
    }


def test_TEST_PIPELINE_SENDS_VALID_REQUESTS_TO_GENERATOR_AND_VALIDATES_ACTION() -> None:
    generator = FakeGenerator(dict(VALID_RESPONSE))
    agent = ReminderAgent(generator)

    result = agent.process(_request())

    assert result.response == VALID_RESPONSE
    assert result.generation is not None
    assert result.local_error_code is None
    assert generator.calls == 1


@pytest.mark.parametrize(
    ("raw_request", "error_code", "question"),
    [
        ({"text": "   "}, "EMPTY_REQUEST", "Please provide a valid reminder request."),
        (
            _request(context={"timezone": "Mars/Nowhere"}),
            "INVALID_TIMEZONE",
            "Which supported time zone should I use?",
        ),
    ],
)
def test_TEST_PIPELINE_LOCALLY_CLARIFIES_INVALID_REQUESTS_WITHOUT_MODEL_CALL(
    raw_request: dict[str, Any],
    error_code: str,
    question: str,
) -> None:
    generator = FakeGenerator(dict(VALID_RESPONSE))
    result = ReminderAgent(generator).process(raw_request)

    assert result.response["intent"] == "clarification"
    assert result.response["clarification_question"] == question
    assert result.local_error_code == error_code
    assert result.generation is None
    assert generator.calls == 0
    assert len(serialize_response(result.response)) > 0


def test_TEST_PIPELINE_REJECTS_INVALID_MODEL_ACTION_WITH_SAFE_ERROR() -> None:
    invalid_response = {
        **VALID_RESPONSE,
        "datetime": "2026-11-18T18:00:00+05:30",
    }
    agent = ReminderAgent(FakeGenerator(invalid_response))

    with pytest.raises(PipelineError) as error:
        agent.process(_request())

    assert error.value.code == "INVALID_MODEL_ACTION"
    assert "2026-11-18" not in str(error.value)


def test_TEST_PIPELINE_SURFACES_SANITIZED_PROVIDER_ERRORS() -> None:
    generator = FakeGenerator(ProviderError("GEMINI_PROVIDER_ERROR", "Provider rejected request."))

    with pytest.raises(ProviderError) as error:
        ReminderAgent(generator).process(_request())

    assert error.value.code == "GEMINI_PROVIDER_ERROR"
    assert generator.calls == 1
