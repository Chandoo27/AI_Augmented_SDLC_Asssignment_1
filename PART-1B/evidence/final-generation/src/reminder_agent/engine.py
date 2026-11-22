from dataclasses import dataclass
from typing import Any, Protocol

from reminder_agent.gemini_client import ModelGeneration
from reminder_agent.models import ReminderRequest
from reminder_agent.validation import (
    ActionValidationError,
    RequestValidationError,
    validate_action,
    validate_request,
)


class RequestGenerator(Protocol):
    def generate(self, request: ReminderRequest) -> ModelGeneration: ...


class PipelineError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        attempts: int = 0,
        rejected_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.attempts = attempts
        self.rejected_response = rejected_response


@dataclass(frozen=True)
class ProcessedResponse:
    response: dict[str, Any]
    generation: ModelGeneration | None
    local_error_code: str | None = None


class ReminderAgent:
    def __init__(self, generator: RequestGenerator) -> None:
        self._generator = generator

    def process(self, value: object) -> ProcessedResponse:
        try:
            request = validate_request(value)
        except RequestValidationError as error:
            return ProcessedResponse(
                response=_clarification_for(error),
                generation=None,
                local_error_code=error.code,
            )

        generation = self._generator.generate(request)
        try:
            response = validate_action(request, generation.response)
        except ActionValidationError as error:
            raise PipelineError(
                "INVALID_MODEL_ACTION",
                "Gemini returned an invalid reminder response.",
                attempts=generation.attempts,
                rejected_response=generation.response,
            ) from error
        return ProcessedResponse(response=response, generation=generation)


def _clarification_for(error: RequestValidationError) -> dict[str, Any]:
    questions = {
        "INVALID_TIMEZONE": "Which supported time zone should I use?",
        "INVALID_REFERENCE_TIME": "Please provide a valid reference time.",
        "MISSING_REFERENCE_TIME": "Please provide a reference date and time.",
        "MISSING_TIMEZONE": "What time zone should I use?",
        "REQUEST_TOO_LONG": "Please shorten the reminder request.",
    }
    return {
        "intent": "clarification",
        "task": "",
        "datetime": "",
        "needs_clarification": True,
        "clarification_question": questions.get(
            error.code,
            "Please provide a valid reminder request.",
        ),
    }
