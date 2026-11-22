import json
from collections.abc import Mapping
from typing import Any

from reminder_agent.validation import validate_response


def serialize_response(value: object) -> str:
    response: Mapping[str, Any] = validate_response(value)
    return json.dumps(response, ensure_ascii=False, separators=(",", ":"))
