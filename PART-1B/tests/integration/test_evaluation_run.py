import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from reminder_agent.engine import ReminderAgent
from reminder_agent.evaluation import (
    EvaluationInputError,
    load_cases,
    run_evaluation,
    select_repeat_case_ids,
    write_report,
)
from reminder_agent.gemini_client import ModelGeneration, ProviderError
from reminder_agent.models import EvaluationCase, ReminderRequest, ReminderResponse
from reminder_agent.validation import RequestValidationError, validate_request

ROOT = Path(__file__).parents[2]
DEVELOPMENT_DATASET = ROOT / "evals" / "v1.jsonl"
HELDOUT_DATASET = ROOT / "evals" / "heldout-v1.jsonl"


class DatasetGenerator:
    def __init__(self, cases: tuple[EvaluationCase, ...]) -> None:
        self.responses: dict[tuple[Any, ...], dict[str, Any]] = {}
        self.calls = 0
        for case in cases:
            try:
                request = validate_request(case.request_payload)
            except RequestValidationError:
                continue
            key = _request_key(request)
            response = _response_dict(case.expected)
            existing = self.responses.get(key)
            if existing is not None and existing != response:
                raise AssertionError("Dataset has conflicting expected output for one request.")
            self.responses[key] = response

    def generate(self, request: ReminderRequest) -> ModelGeneration:
        self.calls += 1
        return ModelGeneration(
            response=self.responses[_request_key(request)],
            model_version="fake-model",
            response_id=f"fake-{self.calls}",
            prompt_tokens=10,
            candidate_tokens=5,
            attempts=1,
        )


class ExhaustingGenerator:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls = 0

    def generate(self, request: ReminderRequest) -> ModelGeneration:
        self.calls += 1
        if self.calls > 1:
            raise ProviderError(
                "CALL_BUDGET_EXHAUSTED",
                "Gemini provider-attempt budget is exhausted.",
            )
        return ModelGeneration(
            response=self.response,
            model_version="fake-model",
            response_id="fake-response",
            prompt_tokens=10,
            candidate_tokens=5,
            attempts=1,
        )


def test_TEST_EVALUATION_RUNS_130_CASES_AND_WRITES_A_PRIVATE_PASS_REPORT(
    tmp_path: Path,
) -> None:
    development = load_cases(DEVELOPMENT_DATASET)
    heldout = load_cases(HELDOUT_DATASET)
    cases = (*development, *heldout)
    generator = DatasetGenerator(cases)
    report = run_evaluation(
        cases,
        ReminderAgent(generator),
        model="gemini-3.5-flash-lite",
        temperature=0.3,
        prompt_version="test-prompt",
        max_calls=140,
        repeated_case_ids=select_repeat_case_ids(development),
        created_at=datetime.fromisoformat("2026-11-19T09:00:00+05:30"),
    )

    assert report.passed
    assert report.total_cases == 106
    assert report.total_runs == 130
    assert report.call_count == generator.calls
    assert report.call_count < report.total_runs
    assert report.call_count <= 140
    assert report.prompt_tokens == report.call_count * 10
    assert report.candidate_tokens == report.call_count * 5
    assert report.failed_thresholds == ()
    assert report.traceability_coverage["NFR-009"] == 12
    output = tmp_path / "nested" / "report.json"
    write_report(report, output)
    serialized = output.read_text(encoding="utf-8")
    assert cases[0].request_payload["text"] not in serialized
    assert "private" not in serialized
    assert json.loads(serialized)["passed"] is True


def test_TEST_EVALUATION_STOPS_VISIBLY_ON_EXHAUSTED_PROVIDER_BUDGET() -> None:
    cases = load_cases(DEVELOPMENT_DATASET)[:2]
    generator = ExhaustingGenerator(_response_dict(cases[0].expected))

    with pytest.raises(EvaluationInputError) as error:
        run_evaluation(
            cases,
            ReminderAgent(generator),
            model="gemini-3.5-flash-lite",
            temperature=0.3,
            prompt_version="test-prompt",
            max_calls=1,
            max_runs=2,
            command="development",
        )

    assert error.value.code == "CALL_BUDGET_EXHAUSTED"
    assert error.value.attempts == 1
    assert generator.calls == 2
    assert error.value.progress is not None
    assert error.value.progress.planned_runs == 2
    assert error.value.progress.completed_runs == 1
    assert error.value.progress.provider_attempts == 1
    assert len(error.value.progress.results) == 1
    assert error.value.progress.stopped_case_id == cases[1].case_id


def _request_key(request: ReminderRequest) -> tuple[Any, ...]:
    context = request.context
    return (
        request.text,
        context.reference_time,
        context.timezone,
        context.reminder_tasks,
    )


def _response_dict(response: ReminderResponse) -> dict[str, Any]:
    return {
        "intent": response.intent,
        "task": response.task,
        "datetime": response.datetime,
        "needs_clarification": response.needs_clarification,
        "clarification_question": response.clarification_question,
    }


def test_TEST_EVALUATION_COLLECTS_EXPECTED_VERSUS_ACTUAL_FOR_FAILED_RUNS_ONLY() -> None:
    cases = load_cases(DEVELOPMENT_DATASET)[:2]
    wrong_for_second_case = _response_dict(cases[0].expected)
    evidence: list[dict[str, Any]] = []

    class FixedGenerator:
        def generate(self, request: Any) -> ModelGeneration:
            return ModelGeneration(
                response=wrong_for_second_case,
                model_version="fake-model",
                response_id="fake-response",
                prompt_tokens=1,
                candidate_tokens=1,
                attempts=1,
            )

    run_evaluation(
        cases,
        ReminderAgent(FixedGenerator()),
        model="gemini-3.5-flash-lite",
        temperature=0.3,
        prompt_version="test-prompt",
        max_calls=140,
        max_runs=2,
        command="development",
        failure_evidence=evidence,
    )

    assert [item["case_id"] for item in evidence] == [cases[1].case_id]
    item = evidence[0]
    assert item["failure_codes"] == ["SEMANTIC_MISMATCH"]
    assert item["actual"] == wrong_for_second_case
    assert item["expected"]["task"] == cases[1].expected.task
    assert cases[1].request_payload["text"] not in json.dumps(item)
