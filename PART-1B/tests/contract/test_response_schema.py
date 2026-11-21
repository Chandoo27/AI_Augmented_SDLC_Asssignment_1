import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[2]
SCHEMA_PATH = ROOT / "specs" / "001-reminder-agent" / "contracts" / "reminder-response.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def _action_response() -> dict[str, Any]:
    return {
        "intent": "create",
        "task": "pay electricity bill",
        "datetime": "2026-11-20T18:00:00+05:30",
        "needs_clarification": False,
        "clarification_question": "",
    }


def _clarification_response() -> dict[str, Any]:
    return {
        "intent": "clarification",
        "task": "",
        "datetime": "",
        "needs_clarification": True,
        "clarification_question": "What time should I use?",
    }


def test_TEST_SCHEMA_IS_VALID() -> None:
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize(
    "response",
    [_action_response(), _clarification_response()],
    ids=["action", "clarification"],
)
def test_TEST_SCHEMA_ACCEPTS_VALID_RESPONSE_VARIANTS(response: dict[str, Any]) -> None:
    assert VALIDATOR.is_valid(response)


@pytest.mark.parametrize(
    ("mutate", "case_id"),
    [
        (lambda value: value.pop("task"), "missing-field"),
        (lambda value: value.update({"extra": "not allowed"}), "extra-field"),
        (lambda value: value.update({"needs_clarification": "false"}), "wrong-type"),
        (lambda value: value.update({"datetime": "tomorrow"}), "invalid-datetime"),
        (
            lambda value: value.update({"clarification_question": "Are you sure?"}),
            "action-question",
        ),
    ],
)
def test_TEST_SCHEMA_REJECTS_INVALID_ACTIONS(mutate: Any, case_id: str) -> None:
    response = _action_response()
    mutate(response)

    assert not VALIDATOR.is_valid(response), case_id


@pytest.mark.parametrize(
    ("mutate", "case_id"),
    [
        (lambda value: value.update({"clarification_question": ""}), "missing-question"),
        (lambda value: value.update({"intent": "create"}), "action-intent"),
        (lambda value: value.update({"needs_clarification": False}), "action-flag"),
    ],
)
def test_TEST_SCHEMA_REJECTS_INVALID_CLARIFICATIONS(mutate: Any, case_id: str) -> None:
    response = _clarification_response()
    mutate(response)

    assert not VALIDATOR.is_valid(response), case_id
