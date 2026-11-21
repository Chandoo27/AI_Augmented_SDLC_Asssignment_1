import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from reminder_agent.models import EvaluationCase, ReminderResponse
from reminder_agent.validation import (
    SCHEMA,
    ActionValidationError,
    RequestValidationError,
    validate_request,
    validate_response,
)

SCHEMA_VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
RESPONSE_FIELDS = {
    "intent",
    "task",
    "datetime",
    "needs_clarification",
    "clarification_question",
}
VALID_OPERATIONS = {"create", "reschedule", "snooze", "clarification"}
TIME_QUESTION_TERMS = {
    "date",
    "day",
    "duration",
    "hour",
    "time",
    "when",
}
TARGET_QUESTION_TERMS = {
    "existing reminder",
    "which reminder",
    "which one",
    "which task",
    "target reminder",
}
TASK_QUESTION_TERMS = {
    "what should i remind",
    "what do you want me to remind",
    "what task should i",
    "which task should i remind",
}


class EvaluationInputError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def load_cases(path: Path, min_cases: int = 1) -> tuple[EvaluationCase, ...]:
    if min_cases < 1:
        raise EvaluationInputError("INVALID_MIN_CASES", "Minimum case count must be positive.")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise EvaluationInputError(
            "DATASET_READ_ERROR", "Could not read evaluation dataset."
        ) from error

    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    dataset_versions: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise EvaluationInputError(
                "INVALID_DATASET_JSON",
                f"Evaluation dataset line {line_number} is not valid JSON.",
            ) from error
        case = _parse_case(row, line_number)
        if case.case_id in seen_ids:
            raise EvaluationInputError(
                "DUPLICATE_CASE_ID",
                f"Evaluation dataset contains duplicate case ID {case.case_id}.",
            )
        seen_ids.add(case.case_id)
        dataset_versions.add(case.dataset_version)
        cases.append(case)

    if len(cases) < min_cases:
        raise EvaluationInputError(
            "INSUFFICIENT_CASES",
            f"Evaluation dataset has fewer than {min_cases} cases.",
        )
    if len(dataset_versions) != 1:
        raise EvaluationInputError(
            "MIXED_DATASET_VERSIONS",
            "Each evaluation dataset must contain exactly one dataset version.",
        )
    return tuple(cases)


def select_repeat_case_ids(
    cases: Sequence[EvaluationCase],
    cases_per_operation: int = 3,
) -> tuple[str, ...]:
    if cases_per_operation < 1:
        raise EvaluationInputError(
            "INVALID_REPEAT_COUNT",
            "Repeated evaluation sample size must be positive.",
        )

    selected: list[str] = []
    for operation in ("create", "reschedule", "snooze", "clarification"):
        eligible = [
            case.case_id
            for case in cases
            if case.operation == operation and _is_model_eligible(case.request_payload)
        ]
        chosen = sorted(eligible)[:cases_per_operation]
        if len(chosen) != cases_per_operation:
            raise EvaluationInputError(
                "INSUFFICIENT_REPEAT_CASES",
                f"Not enough model-eligible cases for operation {operation}.",
            )
        selected.extend(chosen)
    return tuple(selected)


def validate_traceability(
    manifest_path: Path,
    specification_path: Path,
) -> dict[str, tuple[str, ...]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        specification = specification_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as error:
        raise EvaluationInputError(
            "TRACEABILITY_READ_ERROR",
            "Could not read the traceability manifest or specification.",
        ) from error
    if not isinstance(manifest, Mapping):
        raise EvaluationInputError(
            "INVALID_TRACEABILITY",
            "Traceability manifest must be a JSON object.",
        )

    expected_ids = set(re.findall(r"\*\*((?:FR|NFR)-\d{3})\*\*", specification))
    requirement_records = manifest.get("requirements")
    dataset_links = manifest.get("dataset_links")
    harness_cases = manifest.get("harness_evaluation_cases")
    if (
        not isinstance(requirement_records, Mapping)
        or not isinstance(dataset_links, Mapping)
        or not isinstance(harness_cases, Mapping)
        or set(requirement_records) != expected_ids
    ):
        raise EvaluationInputError(
            "INVALID_TRACEABILITY",
            "Traceability requirements must exactly match the specification.",
        )

    case_requirements: dict[str, set[str]] = {}
    seen_case_ids: set[str] = set()
    project_root = manifest_path.resolve().parents[2]
    for link in dataset_links.values():
        if not isinstance(link, Mapping) or not isinstance(link.get("path"), str):
            raise EvaluationInputError(
                "INVALID_TRACEABILITY",
                "Each traceability dataset link must include a relative path.",
            )
        dataset_path = project_root / link["path"]
        for case in load_cases(dataset_path):
            if case.case_id in seen_case_ids:
                raise EvaluationInputError(
                    "DUPLICATE_CASE_ID",
                    f"Evaluation case ID {case.case_id} appears in multiple datasets.",
                )
            seen_case_ids.add(case.case_id)
            for requirement_id in case.requirement_ids:
                if requirement_id not in expected_ids:
                    raise EvaluationInputError(
                        "UNKNOWN_REQUIREMENT_ID",
                        f"Case {case.case_id} references unknown requirement {requirement_id}.",
                    )
                case_requirements.setdefault(requirement_id, set()).add(case.case_id)

    for harness_case_id, record in harness_cases.items():
        if (
            not isinstance(harness_case_id, str)
            or not harness_case_id.startswith("EV-HARNESS-")
            or not isinstance(record, Mapping)
        ):
            raise EvaluationInputError(
                "INVALID_TRACEABILITY",
                "Harness evaluation cases must use stable EV-HARNESS IDs and object records.",
            )
        requirement_ids = record.get("requirement_ids")
        if not isinstance(requirement_ids, list) or not requirement_ids:
            raise EvaluationInputError(
                "INVALID_TRACEABILITY",
                f"Harness case {harness_case_id} must link to requirement IDs.",
            )
        for requirement_id in requirement_ids:
            if requirement_id not in expected_ids:
                raise EvaluationInputError(
                    "UNKNOWN_REQUIREMENT_ID",
                    f"Harness case {harness_case_id} references unknown requirement.",
                )
            case_requirements.setdefault(requirement_id, set()).add(harness_case_id)
        _validate_traceability_record(record, harness_case_id)
        seen_case_ids.add(harness_case_id)

    for requirement_id, record in requirement_records.items():
        _validate_traceability_record(record, requirement_id)
        explicit_case_ids = record.get("evaluation_case_ids", [])
        if not isinstance(explicit_case_ids, list) or any(
            not isinstance(case_id, str) or case_id not in seen_case_ids
            for case_id in explicit_case_ids
        ):
            raise EvaluationInputError(
                "UNKNOWN_EVALUATION_CASE",
                f"Requirement {requirement_id} references an unknown evaluation case.",
            )
        case_requirements.setdefault(requirement_id, set()).update(explicit_case_ids)
        if not case_requirements.get(requirement_id):
            raise EvaluationInputError(
                "MISSING_EVALUATION_CASE",
                f"Requirement {requirement_id} has no linked evaluation case.",
            )

    return {
        requirement_id: tuple(sorted(case_ids))
        for requirement_id, case_ids in sorted(case_requirements.items())
    }


def semantic_correct(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any] | ReminderResponse,
    clarification_topic: str | None = None,
) -> bool:
    expected_values = _response_values(expected)
    if set(actual) != RESPONSE_FIELDS or set(expected_values) != RESPONSE_FIELDS:
        return False
    try:
        validate_response(actual)
    except ActionValidationError:
        return False

    for field in ("intent", "needs_clarification"):
        if actual[field] != expected_values[field]:
            return False

    if actual["needs_clarification"]:
        actual_question = _normalize_text(actual["clarification_question"])
        if not actual_question:
            return False
        if clarification_topic is not None and not _matches_clarification_topic(
            actual_question,
            clarification_topic,
        ):
            return False
        return True

    if _normalize_text(actual["task"]) != _normalize_text(expected_values["task"]):
        return False
    return _same_instant(actual["datetime"], expected_values["datetime"])


def _parse_case(value: object, line_number: int) -> EvaluationCase:
    if not isinstance(value, Mapping):
        raise EvaluationInputError(
            "INVALID_CASE",
            f"Evaluation dataset line {line_number} must be a JSON object.",
        )
    case_id = value.get("case_id")
    dataset_version = value.get("dataset_version")
    operation = value.get("operation")
    category = value.get("category")
    request_payload = value.get("request")
    context = value.get("context", {})
    requirement_ids = value.get("requirement_ids")
    expected = value.get("expected")

    if not isinstance(case_id, str) or not case_id.strip():
        raise EvaluationInputError("INVALID_CASE_ID", "Each case must have a non-empty case ID.")
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        raise EvaluationInputError(
            "INVALID_DATASET_VERSION",
            f"Case {case_id} must have a dataset version.",
        )
    if operation not in VALID_OPERATIONS:
        raise EvaluationInputError(
            "INVALID_OPERATION",
            f"Case {case_id} has an unsupported operation.",
        )
    if not isinstance(category, str) or not category.strip():
        raise EvaluationInputError("INVALID_CATEGORY", f"Case {case_id} must have a category.")
    if not isinstance(request_payload, str):
        raise EvaluationInputError("INVALID_REQUEST", f"Case {case_id} must have request text.")
    if not isinstance(context, Mapping):
        raise EvaluationInputError("INVALID_CONTEXT", f"Case {case_id} context must be an object.")
    if (
        not isinstance(requirement_ids, list)
        or not requirement_ids
        or any(not isinstance(item, str) or not item.strip() for item in requirement_ids)
    ):
        raise EvaluationInputError(
            "INVALID_REQUIREMENT_IDS",
            f"Case {case_id} must map to one or more requirement IDs.",
        )
    if not isinstance(expected, Mapping) or set(expected) != RESPONSE_FIELDS:
        raise EvaluationInputError(
            "INVALID_EXPECTED_RESPONSE",
            f"Case {case_id} must define the exact response contract.",
        )
    try:
        SCHEMA_VALIDATOR.validate(dict(expected))
    except ValidationError as error:
        raise EvaluationInputError(
            "INVALID_EXPECTED_RESPONSE",
            f"Case {case_id} expected response does not satisfy the response schema.",
        ) from error

    try:
        expected_response = ReminderResponse(**expected)
    except TypeError as error:
        raise EvaluationInputError(
            "INVALID_EXPECTED_RESPONSE",
            f"Case {case_id} expected response is invalid.",
        ) from error
    if expected_response.intent not in {operation, "clarification"}:
        raise EvaluationInputError(
            "OPERATION_MISMATCH",
            f"Case {case_id} operation does not match its expected response.",
        )

    clarification_topic = value.get("clarification_topic")
    if clarification_topic is not None and clarification_topic not in {
        "task",
        "time",
        "target",
        "request",
    }:
        raise EvaluationInputError(
            "INVALID_CLARIFICATION_TOPIC",
            f"Case {case_id} has an unsupported clarification topic.",
        )

    return EvaluationCase(
        case_id=case_id,
        dataset_version=dataset_version,
        requirement_ids=tuple(requirement_ids),
        operation=operation,
        category=category,
        request_payload={"text": request_payload, "context": dict(context)},
        expected=expected_response,
        clarification_topic=clarification_topic,
    )


def _validate_traceability_record(value: object, record_id: str) -> None:
    if not isinstance(value, Mapping):
        raise EvaluationInputError(
            "INVALID_TRACEABILITY",
            f"Traceability record {record_id} must be an object.",
        )
    for field in ("test_ids", "implementation_refs"):
        entries = value.get(field)
        if (
            not isinstance(entries, list)
            or not entries
            or any(not isinstance(item, str) or not item.strip() for item in entries)
        ):
            raise EvaluationInputError(
                "INCOMPLETE_TRACEABILITY",
                f"Traceability record {record_id} must include {field}.",
            )
    if any("::" not in item for item in value["implementation_refs"]):
        raise EvaluationInputError(
            "INVALID_IMPLEMENTATION_REFERENCE",
            f"Traceability record {record_id} has a malformed implementation reference.",
        )


def _response_values(value: Mapping[str, Any] | ReminderResponse) -> dict[str, Any]:
    if isinstance(value, ReminderResponse):
        return {
            "intent": value.intent,
            "task": value.task,
            "datetime": value.datetime,
            "needs_clarification": value.needs_clarification,
            "clarification_question": value.clarification_question,
        }
    return dict(value)


def _is_model_eligible(request_payload: Mapping[str, Any]) -> bool:
    try:
        validate_request(request_payload)
    except RequestValidationError:
        return False
    return True


def _matches_clarification_topic(question: str, topic: str) -> bool:
    if topic == "time":
        return bool(TIME_QUESTION_TERMS & set(re.findall(r"[a-z]+", question)))
    if topic == "target":
        return any(term in question for term in TARGET_QUESTION_TERMS)
    if topic == "task":
        return any(term in question for term in TASK_QUESTION_TERMS)
    return bool(question.strip())


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def _same_instant(actual: str, expected: str) -> bool:
    try:
        actual_time = datetime.fromisoformat(actual.replace("Z", "+00:00"))
        expected_time = datetime.fromisoformat(expected.replace("Z", "+00:00"))
    except ValueError:
        return False
    if actual_time.tzinfo is None or expected_time.tzinfo is None:
        return False
    return actual_time == expected_time
