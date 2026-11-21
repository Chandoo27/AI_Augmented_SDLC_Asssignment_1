import json

import pytest

from reminder_agent.output import serialize_response
from reminder_agent.validation import ActionValidationError


def test_TEST_OUTPUT_SERIALIZES_ONLY_THE_FIVE_CONTRACT_FIELDS() -> None:
    response = {
        "intent": "clarification",
        "task": "",
        "datetime": "",
        "needs_clarification": True,
        "clarification_question": "Which reminder do you mean?",
    }

    serialized = serialize_response(response)

    assert json.loads(serialized) == response
    assert not serialized.startswith("```")
    assert "\n" not in serialized


def test_TEST_OUTPUT_REFUSES_INVALID_RESPONSE_SCHEMA() -> None:
    with pytest.raises(ActionValidationError) as error:
        serialize_response({"intent": "create"})

    assert error.value.code == "INVALID_RESPONSE_SCHEMA"
