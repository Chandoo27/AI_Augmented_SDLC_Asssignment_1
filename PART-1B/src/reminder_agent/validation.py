import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from reminder_agent.models import ReminderRequest, ResolutionContext

MAX_REQUEST_LENGTH = 4096
SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "001-reminder-agent"
    / "contracts"
    / "reminder-response.schema.json"
)
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(SCHEMA)
RESPONSE_VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


class RequestValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ActionValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def validate_request(value: object) -> ReminderRequest:
    if not isinstance(value, Mapping):
        raise RequestValidationError("INVALID_REQUEST", "Request must be a JSON object.")

    if set(value) - {"text", "context"}:
        raise RequestValidationError(
            "INVALID_REQUEST_FIELDS", "Request contains unsupported fields."
        )

    text = value.get("text")
    if not isinstance(text, str):
        raise RequestValidationError("MISSING_TEXT", "Request text must be a string.")
    if len(text) > MAX_REQUEST_LENGTH:
        raise RequestValidationError("REQUEST_TOO_LONG", "Request text exceeds 4096 characters.")
    text = text.strip()
    if not text:
        raise RequestValidationError("EMPTY_REQUEST", "Request text must not be empty.")

    context_value = value.get("context", {})
    if not isinstance(context_value, Mapping):
        raise RequestValidationError("INVALID_CONTEXT", "Context must be a JSON object.")
    if set(context_value) - {"reference_time", "timezone", "reminder_tasks"}:
        raise RequestValidationError(
            "INVALID_CONTEXT_FIELDS",
            "Context contains unsupported fields.",
        )

    reference_time = _parse_reference_time(context_value.get("reference_time"))
    timezone_name = _parse_timezone(context_value.get("timezone"))
    reminder_tasks = _parse_reminder_tasks(context_value.get("reminder_tasks", []))
    # Policy: a missing reference time or zone must be asked about, never guessed by the model.
    if reference_time is None:
        raise RequestValidationError("MISSING_REFERENCE_TIME", "Reference time is required.")
    if timezone_name is None:
        raise RequestValidationError("MISSING_TIMEZONE", "Time zone is required.")

    return ReminderRequest(
        text=text,
        context=ResolutionContext(
            reference_time=reference_time,
            timezone=timezone_name,
            reminder_tasks=reminder_tasks,
        ),
    )


def validate_response(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ActionValidationError("INVALID_RESPONSE", "Model response must be a JSON object.")
    response = dict(value)
    try:
        RESPONSE_VALIDATOR.validate(response)
    except ValidationError as error:
        raise ActionValidationError(
            "INVALID_RESPONSE_SCHEMA",
            "Model response does not satisfy the response contract.",
        ) from error
    return response


def validate_action(
    request: ReminderRequest,
    value: object,
) -> dict[str, Any]:
    response = validate_response(value)
    if response["needs_clarification"]:
        return response

    try:
        action_time = datetime.fromisoformat(response["datetime"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ActionValidationError("INVALID_DATETIME", "Action datetime is invalid.") from error
    if action_time.tzinfo is None or action_time.utcoffset() is None:
        raise ActionValidationError(
            "INVALID_DATETIME", "Action datetime must include a UTC offset."
        )

    reference_time = request.context.reference_time
    if reference_time is not None and action_time <= reference_time:
        raise ActionValidationError(
            "DATE_IN_PAST", "Action datetime must be after the reference time."
        )

    if response["intent"] in {"reschedule", "snooze"}:
        _validate_target(response["task"], request.context.reminder_tasks)

    return response


def _parse_reference_time(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RequestValidationError(
            "INVALID_REFERENCE_TIME", "Reference time must be a date-time string."
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RequestValidationError(
            "INVALID_REFERENCE_TIME",
            "Reference time must be a valid offset-aware date-time.",
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RequestValidationError(
            "INVALID_REFERENCE_TIME",
            "Reference time must include a UTC offset.",
        )
    return parsed


def _parse_timezone(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError("INVALID_TIMEZONE", "Time zone must be an IANA zone name.")
    timezone_name = value.strip()
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise RequestValidationError(
            "INVALID_TIMEZONE", "Time zone must be an IANA zone name."
        ) from error
    return timezone_name


def _parse_reminder_tasks(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise RequestValidationError(
            "INVALID_REMINDER_TASKS", "Reminder tasks must be a list of strings."
        )
    if any(not isinstance(task, str) or not task.strip() for task in value):
        raise RequestValidationError(
            "INVALID_REMINDER_TASKS", "Reminder tasks must be non-empty strings."
        )
    return tuple(task.strip() for task in value)


def _normalize_task(value: str) -> str:
    return " ".join(value.split()).casefold()


def _validate_target(task: str, candidates: tuple[str, ...]) -> None:
    target = _normalize_task(task)
    match_count = sum(_normalize_task(candidate) == target for candidate in candidates)
    if match_count == 0:
        raise ActionValidationError(
            "TARGET_NOT_FOUND", "Action target is not in the supplied reminder list."
        )
    if match_count > 1:
        raise ActionValidationError(
            "AMBIGUOUS_TARGET", "Action target does not uniquely identify a reminder."
        )
