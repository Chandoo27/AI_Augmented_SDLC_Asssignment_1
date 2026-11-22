import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from google import genai
from google.genai import errors, types

from reminder_agent.config import Settings
from reminder_agent.models import ReminderRequest
from reminder_agent.prompt import GENERATION_SCHEMA, SYSTEM_INSTRUCTION, build_user_content

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
RATE_LIMIT_WAIT_SECONDS = 20.0
TRANSIENT_WAIT_SECONDS = 10.0


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str, attempts: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.attempts = attempts


@dataclass(frozen=True)
class ModelGeneration:
    response: dict[str, Any]
    model_version: str | None
    response_id: str | None
    prompt_tokens: int | None
    candidate_tokens: int | None
    attempts: int


class ContentGenerator(Protocol):
    def generate_content(
        self,
        *,
        model: str,
        contents: str,
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse: ...


class GenerativeClient(Protocol):
    models: ContentGenerator


class GeminiAdapter:
    def __init__(
        self,
        settings: Settings,
        client: GenerativeClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._client = (
            client
            if client is not None
            else genai.Client(
                api_key=settings.api_key,
                http_options=types.HttpOptions(
                    timeout=round(settings.timeout_seconds * 1000),
                ),
            )
        )
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_attempt_at: float | None = None
        self._provider_attempts = 0

    @property
    def provider_attempts(self) -> int:
        return self._provider_attempts

    def generate(self, request: ReminderRequest) -> ModelGeneration:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=self._settings.temperature,
            response_mime_type="application/json",
            response_schema=GENERATION_SCHEMA,
        )
        contents = build_user_content(request)

        for attempt in range(1, self._settings.max_attempts + 1):
            if self._provider_attempts >= self._settings.max_calls:
                raise ProviderError(
                    "CALL_BUDGET_EXHAUSTED",
                    "Gemini provider-attempt budget is exhausted.",
                    attempts=attempt - 1,
                )
            self._pace()
            self._provider_attempts += 1
            try:
                response = self._client.models.generate_content(
                    model=self._settings.model,
                    contents=contents,
                    config=config,
                )
            except (errors.APIError, httpx.TransportError) as error:
                if self._is_retryable(error):
                    if attempt < self._settings.max_attempts:
                        self._sleep(self._retry_wait(error))
                        continue
                    raise ProviderError(
                        self._retry_failure_code(error),
                        "Gemini request failed after the configured attempts.",
                        attempts=attempt,
                    ) from error
                raise ProviderError(
                    "GEMINI_PROVIDER_ERROR",
                    "Gemini rejected the request.",
                    attempts=attempt,
                ) from error

            return self._parse_generation(response, attempt)

        raise ProviderError(
            "GEMINI_RETRY_EXHAUSTED",
            "Gemini request failed.",
            attempts=self._settings.max_attempts,
        )

    def _pace(self) -> None:
        # Keeps calls under the free-tier requests-per-minute limit instead of
        # relying on retries after a 429 response.
        now = self._monotonic()
        if self._last_attempt_at is not None:
            wait = self._settings.min_interval_seconds - (now - self._last_attempt_at)
            if wait > 0:
                self._sleep(wait)
                now = self._monotonic()
        self._last_attempt_at = now

    @staticmethod
    def _retry_wait(error: errors.APIError | httpx.TransportError) -> float:
        if isinstance(error, errors.APIError) and error.code == 429:
            return RATE_LIMIT_WAIT_SECONDS
        return TRANSIENT_WAIT_SECONDS

    @staticmethod
    def _is_retryable(error: errors.APIError | httpx.TransportError) -> bool:
        if isinstance(error, httpx.TransportError):
            return True
        return error.code in RETRYABLE_STATUS_CODES

    @staticmethod
    def _retry_failure_code(error: errors.APIError | httpx.TransportError) -> str:
        if isinstance(error, errors.APIError):
            if error.code == 408:
                return "GEMINI_TIMEOUT_RETRY_EXHAUSTED"
            if error.code == 429:
                return "GEMINI_RATE_LIMIT_RETRY_EXHAUSTED"
            if error.code in {500, 502, 503, 504}:
                return "GEMINI_SERVER_RETRY_EXHAUSTED"
        elif isinstance(error, httpx.TimeoutException):
            return "GEMINI_TIMEOUT_RETRY_EXHAUSTED"
        elif isinstance(error, httpx.TransportError):
            return "GEMINI_TRANSPORT_RETRY_EXHAUSTED"
        return "GEMINI_RETRY_EXHAUSTED"

    @staticmethod
    def _parse_generation(
        response: types.GenerateContentResponse,
        attempts: int,
    ) -> ModelGeneration:
        try:
            text = response.text
        except ValueError as error:
            raise ProviderError(
                "EMPTY_MODEL_RESPONSE",
                "Gemini returned no text candidate.",
                attempts=attempts,
            ) from error

        if not text or not text.strip():
            raise ProviderError(
                "EMPTY_MODEL_RESPONSE",
                "Gemini returned no text candidate.",
                attempts=attempts,
            )

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ProviderError(
                "INVALID_MODEL_JSON",
                "Gemini returned invalid JSON.",
                attempts=attempts,
            ) from error
        if not isinstance(payload, dict):
            raise ProviderError(
                "INVALID_MODEL_JSON",
                "Gemini response must be a JSON object.",
                attempts=attempts,
            )

        usage = response.usage_metadata
        return ModelGeneration(
            response=payload,
            model_version=response.model_version,
            response_id=response.response_id,
            prompt_tokens=None if usage is None else usage.prompt_token_count,
            candidate_tokens=None if usage is None else usage.candidates_token_count,
            attempts=attempts,
        )
