import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from reminder_agent.engine import PipelineError, ReminderAgent
from reminder_agent.gemini_client import ProviderError
from reminder_agent.models import (
    EvaluationCase,
    EvaluationReport,
    EvaluationResult,
    ReminderResponse,
)
from reminder_agent.validation import (
    SCHEMA,
    ActionValidationError,
    RequestValidationError,
    validate_action,
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
    "timezone",
    "when",
    "zone",
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
DEFAULT_THRESHOLDS = {
    "schema_validity": 1.0,
    "property_validity": 1.0,
    "overall_semantic_accuracy": 0.95,
    "per_operation_semantic_accuracy": 0.9,
    "clarification_accuracy": 1.0,
}
DEFAULT_TRACEABILITY_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "evaluation" / "traceability.json"
)
DEFAULT_SPECIFICATION_PATH = (
    Path(__file__).resolve().parents[2] / "specs" / "001-reminder-agent" / "spec.md"
)


class EvaluationInputError(ValueError):
    def __init__(self, code: str, message: str, attempts: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.attempts = attempts


@dataclass(frozen=True)
class EvaluationMetrics:
    total_cases: int
    total_runs: int
    schema_valid_rate: float
    property_valid_rate: float
    semantic_accuracy: float
    operation_metrics: Mapping[str, Mapping[str, float]]
    clarification_required_count: int
    clarification_correct_count: int
    clarification_accuracy: float


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


def plan_runs(
    cases: Sequence[EvaluationCase],
    repeated_case_ids: Sequence[str] = (),
    runs_per_repeated_case: int = 3,
    max_runs: int = 130,
) -> tuple[tuple[str, int], ...]:
    if max_runs < 1:
        raise EvaluationInputError("INVALID_RUN_BUDGET", "Maximum run count must be positive.")
    if runs_per_repeated_case < 2:
        raise EvaluationInputError(
            "INVALID_REPEAT_COUNT",
            "Repeated cases must have at least two total runs.",
        )
    case_ids = [case.case_id for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise EvaluationInputError("DUPLICATE_CASE_ID", "Evaluation cases must have unique IDs.")
    repeated_ids = tuple(repeated_case_ids)
    if len(set(repeated_ids)) != len(repeated_ids) or not set(repeated_ids) <= set(case_ids):
        raise EvaluationInputError(
            "INVALID_REPEAT_SELECTION",
            "Repeated case IDs must be unique and present in the evaluation cases.",
        )

    planned = tuple(
        (case.case_id, run_index)
        for case in cases
        for run_index in range(
            1,
            runs_per_repeated_case + 1 if case.case_id in repeated_ids else 2,
        )
    )
    if len(planned) > max_runs:
        raise EvaluationInputError(
            "RUN_BUDGET_EXCEEDED",
            "Planned evaluation runs exceed the configured run budget.",
        )
    return planned


def compute_metrics(
    results: Sequence[EvaluationResult],
    cases: Sequence[EvaluationCase],
) -> EvaluationMetrics:
    if not results or not cases:
        raise EvaluationInputError(
            "EMPTY_EVALUATION",
            "Evaluation metrics require at least one case and one result.",
        )
    cases_by_id = {case.case_id: case for case in cases}
    if len(cases_by_id) != len(cases):
        raise EvaluationInputError("DUPLICATE_CASE_ID", "Evaluation cases must have unique IDs.")
    results_by_operation: dict[str, list[EvaluationResult]] = {}
    clarification_results: list[EvaluationResult] = []
    seen_runs: set[tuple[str, int]] = set()
    for result in results:
        case = cases_by_id.get(result.case_id)
        if case is None:
            raise EvaluationInputError(
                "UNKNOWN_RESULT_CASE",
                f"Result references unknown case {result.case_id}.",
            )
        if result.operation != case.operation or result.category != case.category:
            raise EvaluationInputError(
                "RESULT_CASE_MISMATCH",
                f"Result metadata does not match case {result.case_id}.",
            )
        if result.run_index < 1 or (result.case_id, result.run_index) in seen_runs:
            raise EvaluationInputError(
                "DUPLICATE_RUN",
                f"Case {result.case_id} has an invalid or duplicate run index.",
            )
        seen_runs.add((result.case_id, result.run_index))
        results_by_operation.setdefault(case.operation, []).append(result)
        if case.expected.needs_clarification:
            clarification_results.append(result)

    total_runs = len(results)
    schema_valid_rate = sum(result.schema_valid for result in results) / total_runs
    property_valid_rate = sum(result.property_valid for result in results) / total_runs
    semantic_accuracy = sum(result.semantic_correct for result in results) / total_runs
    operation_metrics = {
        operation: {
            "run_count": float(len(operation_results)),
            "schema_valid_rate": sum(item.schema_valid for item in operation_results)
            / len(operation_results),
            "property_valid_rate": sum(item.property_valid for item in operation_results)
            / len(operation_results),
            "semantic_accuracy": sum(item.semantic_correct for item in operation_results)
            / len(operation_results),
        }
        for operation, operation_results in sorted(results_by_operation.items())
    }
    clarification_required_count = len(clarification_results)
    clarification_correct_count = sum(item.semantic_correct for item in clarification_results)
    clarification_accuracy = (
        clarification_correct_count / clarification_required_count
        if clarification_required_count
        else 0.0
    )
    return EvaluationMetrics(
        total_cases=len(cases),
        total_runs=total_runs,
        schema_valid_rate=schema_valid_rate,
        property_valid_rate=property_valid_rate,
        semantic_accuracy=semantic_accuracy,
        operation_metrics=operation_metrics,
        clarification_required_count=clarification_required_count,
        clarification_correct_count=clarification_correct_count,
        clarification_accuracy=clarification_accuracy,
    )


def threshold_failures(
    metrics: EvaluationMetrics,
    thresholds: Mapping[str, float] = DEFAULT_THRESHOLDS,
) -> tuple[str, ...]:
    observed = {
        "schema_validity": metrics.schema_valid_rate,
        "property_validity": metrics.property_valid_rate,
        "overall_semantic_accuracy": metrics.semantic_accuracy,
        "clarification_accuracy": metrics.clarification_accuracy,
    }
    failures: list[str] = []
    for name, value in observed.items():
        threshold = thresholds.get(name)
        if threshold is None or value < threshold:
            failures.append(name)
    operation_threshold = thresholds.get("per_operation_semantic_accuracy")
    if operation_threshold is None:
        failures.append("per_operation_semantic_accuracy")
    elif any(
        operation not in metrics.operation_metrics
        or metrics.operation_metrics[operation]["semantic_accuracy"] < operation_threshold
        for operation in VALID_OPERATIONS
    ):
        failures.append("per_operation_semantic_accuracy")
    return tuple(sorted(set(failures)))


def run_evaluation(
    cases: Sequence[EvaluationCase],
    agent: ReminderAgent,
    *,
    model: str,
    temperature: float,
    prompt_version: str,
    max_calls: int,
    repeated_case_ids: Sequence[str] = (),
    runs_per_repeated_case: int = 3,
    max_runs: int = 130,
    thresholds: Mapping[str, float] = DEFAULT_THRESHOLDS,
    traceability_manifest: Path = DEFAULT_TRACEABILITY_PATH,
    specification_path: Path = DEFAULT_SPECIFICATION_PATH,
    created_at: datetime | None = None,
    command: str = "combined",
) -> EvaluationReport:
    if not cases:
        raise EvaluationInputError("EMPTY_EVALUATION", "Evaluation requires at least one case.")
    if not 1 <= max_calls <= 140:
        raise EvaluationInputError(
            "INVALID_CALL_BUDGET",
            "Provider-attempt budget must be between 1 and 140.",
        )
    if (
        not model.strip()
        or not prompt_version.strip()
        or not math.isfinite(temperature)
        or not 0 < temperature <= 2
    ):
        raise EvaluationInputError(
            "INVALID_EVALUATION_CONFIG",
            "Model, prompt version, and a temperature in (0, 2] are required.",
        )
    if command not in {"development", "held-out", "combined"}:
        raise EvaluationInputError(
            "INVALID_EVALUATION_COMMAND",
            "Evaluation command must be a recognized mode.",
        )

    run_plan = plan_runs(
        cases,
        repeated_case_ids=repeated_case_ids,
        runs_per_repeated_case=runs_per_repeated_case,
        max_runs=max_runs,
    )
    cases_by_id = {case.case_id: case for case in cases}
    if command == "combined":
        development_cases = tuple(case for case in cases if case.dataset_version == "v1")
        expected_repeats = select_repeat_case_ids(development_cases)
        if set(repeated_case_ids) != set(expected_repeats):
            raise EvaluationInputError(
                "INVALID_REPEAT_SELECTION",
                "Combined evaluation must repeat the approved development sample.",
            )
    traceability = validate_traceability(traceability_manifest, specification_path)
    results: list[EvaluationResult] = []
    provider_attempts = 0
    prompt_token_counts: list[int] = []
    candidate_token_counts: list[int] = []

    for case_id, run_index in run_plan:
        case = cases_by_id[case_id]
        try:
            processed = agent.process(case.request_payload)
        except ProviderError as error:
            provider_attempts += error.attempts
            if error.code == "CALL_BUDGET_EXHAUSTED" or provider_attempts > max_calls:
                raise EvaluationInputError(
                    "CALL_BUDGET_EXHAUSTED",
                    "Evaluation stopped because the provider-attempt budget was exhausted.",
                    attempts=provider_attempts,
                ) from error
            results.append(_failed_result(case, run_index, error.code))
            continue
        except PipelineError as error:
            provider_attempts += error.attempts
            if provider_attempts > max_calls:
                raise EvaluationInputError(
                    "CALL_BUDGET_EXHAUSTED",
                    "Evaluation stopped because the provider-attempt budget was exhausted.",
                    attempts=provider_attempts,
                ) from error
            results.append(_failed_result(case, run_index, error.code))
            continue

        generation = processed.generation
        if generation is not None:
            provider_attempts += generation.attempts
            if provider_attempts > max_calls:
                raise EvaluationInputError(
                    "CALL_BUDGET_EXHAUSTED",
                    "Evaluation stopped because the provider-attempt budget was exhausted.",
                    attempts=provider_attempts,
                )
            if generation.prompt_tokens is not None:
                prompt_token_counts.append(generation.prompt_tokens)
            if generation.candidate_tokens is not None:
                candidate_token_counts.append(generation.candidate_tokens)

        schema_valid = _is_schema_valid(processed.response)
        property_valid = _is_property_valid(case, processed.response, processed.local_error_code)
        semantic_is_correct = semantic_correct(
            processed.response,
            case.expected,
            clarification_topic=case.clarification_topic,
        )
        failure_codes: list[str] = []
        if not schema_valid:
            failure_codes.append("INVALID_RESPONSE_SCHEMA")
        if not property_valid:
            failure_codes.append("INVALID_ACTION_PROPERTIES")
        if not semantic_is_correct:
            failure_codes.append("SEMANTIC_MISMATCH")
        results.append(
            EvaluationResult(
                case_id=case.case_id,
                run_index=run_index,
                operation=case.operation,
                category=case.category,
                schema_valid=schema_valid,
                property_valid=property_valid,
                semantic_correct=semantic_is_correct,
                failure_codes=tuple(failure_codes),
                model_version=None if generation is None else generation.model_version,
                prompt_tokens=None if generation is None else generation.prompt_tokens,
                candidate_tokens=None if generation is None else generation.candidate_tokens,
            )
        )

    metrics = compute_metrics(results, cases)
    failed_thresholds = threshold_failures(metrics, thresholds)
    traceability_coverage = {
        requirement_id: len(case_ids) for requirement_id, case_ids in traceability.items()
    }
    dataset_versions = sorted({case.dataset_version for case in cases})
    model_versions = sorted(
        {result.model_version for result in results if result.model_version is not None}
    )
    report = EvaluationReport(
        schema_version="1.0.0",
        dataset_version="+".join(dataset_versions),
        prompt_version=prompt_version,
        model=model,
        model_version=(
            model_versions[0]
            if len(model_versions) == 1
            else "multiple"
            if model_versions
            else None
        ),
        temperature=temperature,
        command=command,
        created_at=created_at or datetime.now(UTC),
        total_cases=len(cases),
        total_runs=len(run_plan),
        call_count=provider_attempts,
        prompt_tokens=sum(prompt_token_counts) if prompt_token_counts else None,
        candidate_tokens=sum(candidate_token_counts) if candidate_token_counts else None,
        schema_valid_count=sum(result.schema_valid for result in results),
        property_valid_count=sum(result.property_valid for result in results),
        semantic_correct_count=sum(result.semantic_correct for result in results),
        clarification_required_count=metrics.clarification_required_count,
        clarification_correct_count=metrics.clarification_correct_count,
        operation_metrics=metrics.operation_metrics,
        traceability_coverage=traceability_coverage,
        thresholds=dict(thresholds),
        failed_thresholds=failed_thresholds,
        results=tuple(results),
        passed=not failed_thresholds
        and not any(
            code not in {"SEMANTIC_MISMATCH"} for result in results for code in result.failure_codes
        ),
    )
    return report


def write_report(report: EvaluationReport, path: Path) -> None:
    if report.command not in {"development", "held-out", "combined"}:
        raise EvaluationInputError(
            "UNSAFE_REPORT_COMMAND",
            "Report command must be a recognized evaluation mode.",
        )
    for result in report.results:
        if not re.fullmatch(r"EV-[A-Z0-9-]+", result.case_id) or any(
            not re.fullmatch(r"[A-Z0-9_]+", code) for code in result.failure_codes
        ):
            raise EvaluationInputError(
                "UNSAFE_REPORT_RESULT",
                "Report results must contain only stable case IDs and safe error codes.",
            )
    payload = asdict(report)
    payload["created_at"] = report.created_at.isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
        SCHEMA_VALIDATOR.validate(expected_values)
    except ValidationError:
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


def _failed_result(
    case: EvaluationCase,
    run_index: int,
    error_code: str,
) -> EvaluationResult:
    return EvaluationResult(
        case_id=case.case_id,
        run_index=run_index,
        operation=case.operation,
        category=case.category,
        schema_valid=False,
        property_valid=False,
        semantic_correct=False,
        failure_codes=(error_code,),
    )


def _is_schema_valid(response: Mapping[str, Any]) -> bool:
    try:
        validate_response(response)
    except ActionValidationError:
        return False
    return True


def _is_property_valid(
    case: EvaluationCase,
    response: Mapping[str, Any],
    local_error_code: str | None,
) -> bool:
    if local_error_code is not None:
        return (
            _is_schema_valid(response)
            and response.get("intent") == "clarification"
            and response.get("needs_clarification") is True
        )
    try:
        request = validate_request(case.request_payload)
        validate_action(request, response)
    except (ActionValidationError, RequestValidationError):
        return False
    return True


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
