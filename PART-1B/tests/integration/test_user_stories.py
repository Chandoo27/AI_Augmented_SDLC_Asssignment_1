import json
from pathlib import Path
from typing import Any

import pytest

from reminder_agent.engine import ReminderAgent
from reminder_agent.evaluation import load_cases, semantic_correct
from reminder_agent.gemini_client import ModelGeneration
from reminder_agent.models import EvaluationCase, ReminderResponse
from reminder_agent.prompt import SYSTEM_INSTRUCTION, build_user_content
from reminder_agent.validation import validate_request

ROOT = Path(__file__).parents[2]
DEVELOPMENT_DATASET = ROOT / "evals" / "v1.jsonl"


class FakeGenerator:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls = 0

    def generate(self, request: Any) -> ModelGeneration:
        self.calls += 1
        return ModelGeneration(
            response=self.response,
            model_version="fake-model",
            response_id="fake-response",
            prompt_tokens=10,
            candidate_tokens=5,
            attempts=1,
        )


@pytest.mark.parametrize(
    "case_id",
    [
        "EV-CREATE-001",
        "EV-CREATE-003",
        "EV-CREATE-018",
        "EV-RESCHEDULE-001",
        "EV-RESCHEDULE-008",
        "EV-RESCHEDULE-010",
        "EV-SNOOZE-001",
        "EV-SNOOZE-010",
        "EV-SNOOZE-012",
        "EV-CLARIFY-005",
        "EV-CLARIFY-003",
        "EV-CLARIFY-008",
        "EV-CLARIFY-019",
    ],
)
def test_TEST_USER_STORIES_RETURN_EXPECTED_VALIDATED_ACTION_OR_CLARIFICATION(
    case_id: str,
) -> None:
    case = _case(case_id)
    generator = FakeGenerator(_response_dict(case.expected))

    result = ReminderAgent(generator).process(case.request_payload)

    assert semantic_correct(
        result.response,
        case.expected,
        clarification_topic=case.clarification_topic,
    )
    assert generator.calls == 1


@pytest.mark.parametrize(
    "case_id",
    ["EV-CLARIFY-001", "EV-CLARIFY-002", "EV-CLARIFY-014"],
)
def test_TEST_USER_STORIES_LOCALLY_REJECT_MALFORMED_OR_OVERSIZED_INPUT(
    case_id: str,
) -> None:
    case = _case(case_id)
    generator = FakeGenerator(_response_dict(case.expected))

    result = ReminderAgent(generator).process(case.request_payload)

    assert result.response["needs_clarification"] is True
    assert result.generation is None
    assert result.local_error_code is not None
    assert generator.calls == 0
    assert semantic_correct(
        result.response,
        case.expected,
        clarification_topic=case.clarification_topic,
    )


def test_TEST_PROMPT_INJECTION_CASE_REMAINS_UNTRUSTED_DATA() -> None:
    case = _case("EV-CLARIFY-019")
    request = validate_request(case.request_payload)
    serialized = json.loads(build_user_content(request))

    assert case.category == "prompt-injection"
    assert "FR-013" in case.requirement_ids
    assert serialized["request"] == case.request_payload["text"]
    assert "untrusted data" in SYSTEM_INSTRUCTION.casefold()


def _case(case_id: str) -> EvaluationCase:
    return next(case for case in load_cases(DEVELOPMENT_DATASET) if case.case_id == case_id)


def _response_dict(response: ReminderResponse) -> dict[str, Any]:
    return {
        "intent": response.intent,
        "task": response.task,
        "datetime": response.datetime,
        "needs_clarification": response.needs_clarification,
        "clarification_question": response.clarification_question,
    }
