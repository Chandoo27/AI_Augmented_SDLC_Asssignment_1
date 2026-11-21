import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from reminder_agent.evaluation import (
    DEFAULT_THRESHOLDS,
    EvaluationInputError,
    compute_metrics,
    load_cases,
    plan_runs,
    select_repeat_case_ids,
    semantic_correct,
    threshold_failures,
    write_report,
)
from reminder_agent.models import EvaluationCase, EvaluationReport, EvaluationResult
from reminder_agent.validation import RequestValidationError, validate_request

ROOT = Path(__file__).parents[2]
DEVELOPMENT_DATASET = ROOT / "data" / "evaluation" / "v1.jsonl"
HELDOUT_DATASET = ROOT / "data" / "evaluation" / "heldout-v1.jsonl"


def test_TEST_EVALUATION_LOADS_VERSIONED_86_CASE_DEVELOPMENT_DATASET() -> None:
    cases = load_cases(DEVELOPMENT_DATASET)

    assert len(cases) == 86
    assert {case.dataset_version for case in cases} == {"v1"}
    assert {case.operation for case in cases} == {
        "create",
        "reschedule",
        "snooze",
        "clarification",
    }
    assert all(case.requirement_ids for case in cases)
    assert all("text" in case.request_payload for case in cases)


def test_TEST_EVALUATION_LOADS_20_CASE_HELDOUT_DATASET_WITH_FIXED_CONTEXT() -> None:
    cases = load_cases(HELDOUT_DATASET)

    assert len(cases) == 20
    assert {case.dataset_version for case in cases} == {"heldout-v1"}
    assert {case.operation for case in cases} == {
        "create",
        "reschedule",
        "snooze",
        "clarification",
    }
    assert {case.request_payload["context"]["reference_time"] for case in cases} <= {
        "2026-03-07T09:00:00-05:00",
        "2026-11-19T09:00:00+05:30",
    }


def test_TEST_EVALUATION_REJECTS_DUPLICATE_CASE_IDS(tmp_path: Path) -> None:
    first_row = json.loads(DEVELOPMENT_DATASET.read_text(encoding="utf-8").splitlines()[0])
    duplicate_row = dict(first_row)
    dataset = tmp_path / "duplicate.jsonl"
    dataset.write_text(
        json.dumps(first_row) + "\n" + json.dumps(duplicate_row) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(EvaluationInputError) as error:
        load_cases(dataset, min_cases=1)

    assert error.value.code == "DUPLICATE_CASE_ID"


def test_TEST_EVALUATION_SELECTS_THREE_MODEL_ELIGIBLE_CASES_PER_OPERATION() -> None:
    cases = load_cases(DEVELOPMENT_DATASET)

    repeated_ids = select_repeat_case_ids(cases, cases_per_operation=3)
    repeated = [case for case in cases if case.case_id in repeated_ids]

    assert len(repeated_ids) == 12
    assert Counter(case.operation for case in repeated) == {
        "create": 3,
        "reschedule": 3,
        "snooze": 3,
        "clarification": 3,
    }
    assert all(_is_model_eligible(case.request_payload) for case in repeated)


def test_TEST_SEMANTIC_SCORE_ACCEPTS_EQUIVALENT_OFFSETS() -> None:
    expected = {
        "intent": "create",
        "task": "pay electricity bill",
        "datetime": "2026-11-20T18:00:00+05:30",
        "needs_clarification": False,
        "clarification_question": "",
    }
    actual = {
        **expected,
        "datetime": "2026-11-20T12:30:00Z",
    }

    assert semantic_correct(actual, expected)


def test_TEST_EVALUATION_PLANS_130_RUNS_AND_ENFORCES_RUN_BUDGET() -> None:
    development = load_cases(DEVELOPMENT_DATASET)
    heldout = load_cases(HELDOUT_DATASET)
    repeat_ids = select_repeat_case_ids(development)

    plan = plan_runs(
        (*development, *heldout),
        repeated_case_ids=repeat_ids,
        max_runs=130,
    )

    assert len(plan) == 130
    expected_counts = {case.case_id: 1 for case in (*development, *heldout)}
    expected_counts.update({case_id: 3 for case_id in repeat_ids})
    assert Counter(case_id for case_id, _ in plan) == expected_counts
    with pytest.raises(EvaluationInputError) as error:
        plan_runs((*development, *heldout), repeat_ids, max_runs=129)
    assert error.value.code == "RUN_BUDGET_EXCEEDED"


def test_TEST_EVALUATION_REPORTS_SEPARATE_METRICS_AND_OPERATION_DENOMINATORS() -> None:
    development = load_cases(DEVELOPMENT_DATASET)
    create_cases = [case for case in development if case.operation == "create"][:2]
    reschedule_case = next(case for case in development if case.operation == "reschedule")
    clarification_case = next(case for case in development if case.operation == "clarification")
    cases = (*create_cases, reschedule_case, clarification_case)
    results = (
        _result(create_cases[0], schema_valid=True, property_valid=True, semantic_correct=True),
        _result(create_cases[1], schema_valid=False, property_valid=False, semantic_correct=False),
        _result(reschedule_case, schema_valid=True, property_valid=False, semantic_correct=True),
        _result(
            clarification_case,
            schema_valid=True,
            property_valid=True,
            semantic_correct=True,
        ),
    )

    metrics = compute_metrics(results, cases)

    assert metrics.total_cases == 4
    assert metrics.total_runs == 4
    assert metrics.schema_valid_rate == 0.75
    assert metrics.property_valid_rate == 0.5
    assert metrics.semantic_accuracy == 0.75
    assert metrics.operation_metrics["create"]["run_count"] == 2.0
    assert metrics.operation_metrics["reschedule"]["run_count"] == 1.0
    assert metrics.operation_metrics["clarification"]["run_count"] == 1.0
    assert metrics.clarification_required_count == 1
    assert metrics.clarification_correct_count == 1
    assert metrics.clarification_accuracy == 1.0
    assert threshold_failures(metrics, DEFAULT_THRESHOLDS) == (
        "overall_semantic_accuracy",
        "per_operation_semantic_accuracy",
        "property_validity",
        "schema_validity",
    )
    complete_scores = tuple(
        _result(case, schema_valid=True, property_valid=True, semantic_correct=True)
        for case in cases
    )
    assert threshold_failures(
        compute_metrics(complete_scores, cases),
        DEFAULT_THRESHOLDS,
    ) == ("per_operation_semantic_accuracy",)


def test_TEST_EVALUATION_REPORT_OMITS_REQUEST_AND_RESPONSE_CONTENT(
    tmp_path: Path,
) -> None:
    case = load_cases(DEVELOPMENT_DATASET)[0]
    result = _result(case, schema_valid=True, property_valid=True, semantic_correct=True)
    report = EvaluationReport(
        schema_version="1.0.0",
        dataset_version="v1",
        prompt_version="p1",
        model="gemini-3.5-flash-lite",
        model_version=None,
        temperature=0.3,
        command="development",
        created_at=datetime.fromisoformat("2026-11-19T09:00:00+05:30"),
        total_cases=1,
        total_runs=1,
        call_count=1,
        prompt_tokens=31,
        candidate_tokens=12,
        schema_valid_count=1,
        property_valid_count=1,
        semantic_correct_count=1,
        clarification_required_count=0,
        clarification_correct_count=0,
        operation_metrics={"create": {"semantic_accuracy": 1.0}},
        thresholds=dict(DEFAULT_THRESHOLDS),
        results=(result,),
        passed=True,
    )
    output = tmp_path / "report.json"

    write_report(report, output)

    serialized = output.read_text(encoding="utf-8")
    assert case.request_payload["text"] not in serialized
    assert '"response":' not in serialized
    assert '"api_key":' not in serialized
    assert json.loads(serialized)["results"][0]["case_id"] == case.case_id


@pytest.mark.parametrize(
    ("question", "topic", "is_correct"),
    [
        ("When should I set the reminder?", "time", True),
        ("Which existing reminder do you mean?", "target", True),
        ("What should I remind you about?", "task", True),
        ("Which existing reminder do you mean?", "time", False),
        ("", "request", False),
    ],
)
def test_TEST_SEMANTIC_SCORE_CHECKS_CLARIFICATION_TOPIC(
    question: str,
    topic: str,
    is_correct: bool,
) -> None:
    expected = {
        "intent": "clarification",
        "task": "",
        "datetime": "",
        "needs_clarification": True,
        "clarification_question": "What time should I use?",
    }
    actual = {
        **expected,
        "clarification_question": question,
    }

    assert semantic_correct(actual, expected, clarification_topic=topic) is is_correct


def _is_model_eligible(request_payload: dict[str, Any] | Any) -> bool:
    try:
        validate_request(request_payload)
    except RequestValidationError:
        return False
    return True


def _result(
    case: EvaluationCase,
    *,
    schema_valid: bool,
    property_valid: bool,
    semantic_correct: bool,
) -> EvaluationResult:
    return EvaluationResult(
        case_id=case.case_id,
        run_index=1,
        operation=case.operation,
        category=case.category,
        schema_valid=schema_valid,
        property_valid=property_valid,
        semantic_correct=semantic_correct,
    )
