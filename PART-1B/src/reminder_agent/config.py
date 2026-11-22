import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_MAX_CALLS = 200
DEFAULT_MIN_INTERVAL_SECONDS = 5.0
DEFAULT_DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class ConfigurationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False, compare=False)
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    max_calls: int = DEFAULT_MAX_CALLS
    min_interval_seconds: float = 0.0


def load_settings(
    env: Mapping[str, str] | None = None,
    dotenv_path: Path | None = DEFAULT_DOTENV_PATH,
) -> Settings:
    file_values: dict[str, str] = {}
    if dotenv_path is not None:
        try:
            file_values = {
                key: value for key, value in dotenv_values(dotenv_path).items() if value is not None
            }
        except OSError as error:
            raise ConfigurationError(
                "DOTENV_READ_ERROR", "Could not read local settings."
            ) from error

    effective = dict(file_values)
    effective.update(os.environ if env is None else env)

    api_key = effective.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ConfigurationError("MISSING_API_KEY", "GEMINI_API_KEY is required.")

    model = effective.get("GEMINI_MODEL", DEFAULT_MODEL).strip()
    if not model:
        raise ConfigurationError("INVALID_MODEL", "GEMINI_MODEL must not be empty.")

    try:
        temperature = float(effective.get("GEMINI_TEMPERATURE", str(DEFAULT_TEMPERATURE)))
    except ValueError as error:
        raise ConfigurationError(
            "INVALID_TEMPERATURE", "Temperature must be a number in (0, 2]."
        ) from error
    if not 0 < temperature <= 2:
        raise ConfigurationError("INVALID_TEMPERATURE", "Temperature must be a number in (0, 2].")

    try:
        timeout_seconds = float(
            effective.get("GEMINI_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
        )
    except ValueError as error:
        raise ConfigurationError("INVALID_TIMEOUT", "Timeout must be a positive number.") from error
    if not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 120:
        raise ConfigurationError(
            "INVALID_TIMEOUT",
            "Timeout must be a finite number between 0 and 120 seconds.",
        )

    try:
        max_attempts = int(effective.get("GEMINI_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS)))
    except ValueError as error:
        raise ConfigurationError(
            "INVALID_MAX_ATTEMPTS", "Maximum attempts must be an integer from 1 to 3."
        ) from error
    if not 1 <= max_attempts <= 3:
        raise ConfigurationError(
            "INVALID_MAX_ATTEMPTS", "Maximum attempts must be an integer from 1 to 3."
        )

    try:
        max_calls = int(effective.get("GEMINI_MAX_CALLS", str(DEFAULT_MAX_CALLS)))
    except ValueError as error:
        raise ConfigurationError(
            "INVALID_MAX_CALLS", "Maximum calls must be a positive integer."
        ) from error
    if not 1 <= max_calls <= DEFAULT_MAX_CALLS:
        raise ConfigurationError(
            "INVALID_MAX_CALLS",
            f"Maximum calls must be an integer from 1 to {DEFAULT_MAX_CALLS}.",
        )

    try:
        min_interval_seconds = float(
            effective.get("GEMINI_MIN_INTERVAL_SECONDS", str(DEFAULT_MIN_INTERVAL_SECONDS))
        )
    except ValueError as error:
        raise ConfigurationError(
            "INVALID_MIN_INTERVAL", "Minimum interval must be a number from 0 to 60 seconds."
        ) from error
    if not math.isfinite(min_interval_seconds) or not 0 <= min_interval_seconds <= 60:
        raise ConfigurationError(
            "INVALID_MIN_INTERVAL", "Minimum interval must be a number from 0 to 60 seconds."
        )

    return Settings(
        api_key=api_key,
        model=model,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        max_attempts=max_attempts,
        max_calls=max_calls,
        min_interval_seconds=min_interval_seconds,
    )
