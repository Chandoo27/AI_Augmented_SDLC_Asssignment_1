from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

ReminderIntent = Literal["create", "reschedule", "snooze", "clarification"]


@dataclass(frozen=True)
class ResolutionContext:
    reference_time: datetime | None = None
    timezone: str | None = None
    reminder_tasks: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReminderRequest:
    text: str
    context: ResolutionContext


@dataclass(frozen=True)
class ReminderResponse:
    intent: ReminderIntent
    task: str
    datetime: str
    needs_clarification: bool
    clarification_question: str


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    dataset_version: str
    requirement_ids: tuple[str, ...]
    operation: ReminderIntent
    category: str
    request_payload: Mapping[str, Any]
    expected: ReminderResponse
    clarification_topic: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    run_index: int
    operation: ReminderIntent
    category: str
    schema_valid: bool
    property_valid: bool
    semantic_correct: bool
    failure_codes: tuple[str, ...] = ()
    model_version: str | None = None
    prompt_tokens: int | None = None
    candidate_tokens: int | None = None


@dataclass(frozen=True)
class EvaluationReport:
    schema_version: str
    dataset_version: str
    prompt_version: str
    model: str
    model_version: str | None
    temperature: float
    command: str
    created_at: datetime
    total_cases: int
    total_runs: int
    call_count: int
    prompt_tokens: int | None
    candidate_tokens: int | None
    schema_valid_count: int
    property_valid_count: int
    semantic_correct_count: int
    clarification_required_count: int
    clarification_correct_count: int
    operation_metrics: Mapping[str, Mapping[str, float]]
    traceability_coverage: Mapping[str, int]
    thresholds: Mapping[str, float]
    failed_thresholds: tuple[str, ...]
    results: tuple[EvaluationResult, ...]
    passed: bool
