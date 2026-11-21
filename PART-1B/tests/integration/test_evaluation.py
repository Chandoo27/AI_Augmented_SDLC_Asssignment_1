import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from reminder_agent.evaluation import (
    EvaluationInputError,
    load_cases,
    select_repeat_case_ids,
    semantic_correct,
)
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
