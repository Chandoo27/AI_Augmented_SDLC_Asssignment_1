from datetime import datetime
from typing import Any

import pytest

from reminder_agent.validation import (
    ActionValidationError,
    RequestValidationError,
    validate_action,
    validate_request,
    validate_response,
)


def _raw_request(
    text: str = "Remind me tomorrow at 6 PM to pay electricity bill.",
    **context: Any,
) -> dict[str, Any]:
    return {
        "text": text,
        "context": {
            "reference_time": "2026-11-19T09:00:00+05:30",
            "timezone": "Asia/Kolkata",
            "reminder_tasks": ["pay electricity bill", "attend project review"],
            **context,
        },
    }


def _action_response(
    intent: str = "create",
    task: str = "pay electricity bill",
    datetime_value: str = "2026-11-20T18:00:00+05:30",
) -> dict[str, Any]:
    return {
        "intent": intent,
        "task": task,
        "datetime": datetime_value,
        "needs_clarification": False,
        "clarification_question": "",
    }


def test_TEST_REQUEST_VALIDATION_NORMALIZES_AWARE_CONTEXT() -> None:
    request = validate_request(_raw_request())

    assert request.text.startswith("Remind me")
    assert isinstance(request.context.reference_time, datetime)
    assert request.context.reference_time.utcoffset() is not None
    assert request.context.timezone == "Asia/Kolkata"
    assert request.context.reminder_tasks == (
        "pay electricity bill",
        "attend project review",
    )


@pytest.mark.parametrize(
    ("raw", "error_code"),
    [
        ("not-an-object", "INVALID_REQUEST"),
        ({}, "MISSING_TEXT"),
        ({"text": None}, "MISSING_TEXT"),
        ({"text": "valid", "unexpected": True}, "INVALID_REQUEST_FIELDS"),
        ({"text": "   "}, "EMPTY_REQUEST"),
        ({"text": "x" * 4097}, "REQUEST_TOO_LONG"),
        ({"text": "valid", "context": []}, "INVALID_CONTEXT"),
        ({"text": "valid", "context": {"timezone": ""}}, "INVALID_TIMEZONE"),
        (_raw_request(timezone="Invalid/Zone"), "INVALID_TIMEZONE"),
        (_raw_request(reference_time="2026-11-19T09:00:00"), "INVALID_REFERENCE_TIME"),
        (
            {"text": "valid", "context": {"reminder_tasks": "not-a-list"}},
            "INVALID_REMINDER_TASKS",
        ),
        (
            {"text": "valid", "context": {"reminder_tasks": [42]}},
            "INVALID_REMINDER_TASKS",
        ),
    ],
)
def test_TEST_REQUEST_VALIDATION_REJECTS_INVALID_INPUT(
    raw: object,
    error_code: str,
) -> None:
    with pytest.raises(RequestValidationError) as error:
        validate_request(raw)

    assert error.value.code == error_code


def test_TEST_REQUEST_VALIDATION_ASKS_FOR_ABSENT_REFERENCE_TIME_OR_TIMEZONE() -> None:
    with pytest.raises(RequestValidationError) as no_context:
        validate_request({"text": "Remind me at 6 PM to call the dentist."})
    with pytest.raises(RequestValidationError) as no_zone:
        validate_request(
            {
                "text": "Remind me at 6 PM to call the dentist.",
                "context": {"reference_time": "2026-11-19T09:00:00+05:30"},
            }
        )

    assert no_context.value.code == "MISSING_REFERENCE_TIME"
    assert no_zone.value.code == "MISSING_TIMEZONE"


def test_TEST_REQUEST_VALIDATION_DEFAULTS_ABSENT_REMINDER_TASKS_TO_EMPTY() -> None:
    raw = _raw_request()
    del raw["context"]["reminder_tasks"]

    assert validate_request(raw).context.reminder_tasks == ()


def test_TEST_RESPONSE_VALIDATION_RETURNS_SCHEMA_VALID_OBJECT() -> None:
    response = _action_response()

    assert validate_response(response) == response


def test_TEST_RESPONSE_VALIDATION_REJECTS_NON_OBJECT_OUTPUT() -> None:
    with pytest.raises(ActionValidationError) as error:
        validate_response(None)

    assert error.value.code == "INVALID_RESPONSE"


def test_TEST_ACTION_VALIDATION_REJECTS_NAIVE_ACTION_DATETIME() -> None:
    request = validate_request(_raw_request())
    response = _action_response(datetime_value="2026-11-20T18:00:00")

    with pytest.raises(ActionValidationError) as error:
        validate_action(request, response)

    assert error.value.code == "INVALID_RESPONSE_SCHEMA"


def test_TEST_ACTION_VALIDATION_REQUIRES_UNIQUE_EXISTING_TARGET() -> None:
    request = validate_request(
        _raw_request(
            "Reschedule the electricity reminder to tomorrow at 8 PM.",
            reminder_tasks=["pay electricity bill", "pay electricity bill"],
        )
    )
    response = _action_response("reschedule", "pay electricity bill")

    with pytest.raises(ActionValidationError) as error:
        validate_action(request, response)

    assert error.value.code == "AMBIGUOUS_TARGET"


def test_TEST_ACTION_VALIDATION_REJECTS_TARGET_NOT_IN_CONTEXT() -> None:
    request = validate_request(_raw_request("Snooze my dentist reminder by 30 minutes."))
    response = _action_response("snooze", "call the dentist")

    with pytest.raises(ActionValidationError) as error:
        validate_action(request, response)

    assert error.value.code == "TARGET_NOT_FOUND"


def test_TEST_ACTION_VALIDATION_REJECTS_PAST_DATE() -> None:
    request = validate_request(_raw_request())
    response = _action_response(datetime_value="2026-11-18T18:00:00+05:30")

    with pytest.raises(ActionValidationError) as error:
        validate_action(request, response)

    assert error.value.code == "DATE_IN_PAST"
