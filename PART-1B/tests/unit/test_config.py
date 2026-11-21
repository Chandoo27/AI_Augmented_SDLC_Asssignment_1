from pathlib import Path

import pytest

from reminder_agent.config import ConfigurationError, load_settings


def test_TEST_CONFIG_LOADS_LOCAL_ENV_FILE_AND_HIDES_SECRET(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEMINI_API_KEY=unit-test-secret\n"
        "GEMINI_MODEL=gemini-3.5-flash-lite\n"
        "GEMINI_TEMPERATURE=0.3\n",
        encoding="utf-8",
    )

    settings = load_settings(env={}, dotenv_path=env_file)

    assert settings.model == "gemini-3.5-flash-lite"
    assert settings.temperature == 0.3
    assert "unit-test-secret" not in repr(settings)


def test_TEST_CONFIG_ENVIRONMENT_OVERRIDES_LOCAL_FILE(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=file-key\nGEMINI_MODEL=file-model\n", encoding="utf-8")

    settings = load_settings(
        env={
            "GEMINI_API_KEY": "process-key",
            "GEMINI_MODEL": "process-model",
        },
        dotenv_path=env_file,
    )

    assert settings.api_key == "process-key"
    assert settings.model == "process-model"


def test_TEST_CONFIG_REQUIRES_API_KEY() -> None:
    with pytest.raises(ConfigurationError) as error:
        load_settings(env={}, dotenv_path=None)

    assert error.value.code == "MISSING_API_KEY"


@pytest.mark.parametrize("temperature", ["0", "-0.1", "2.1", "nan", "inf", "invalid"])
def test_TEST_CONFIG_REJECTS_INVALID_TEMPERATURE(temperature: str) -> None:
    with pytest.raises(ConfigurationError) as error:
        load_settings(
            env={"GEMINI_API_KEY": "test-key", "GEMINI_TEMPERATURE": temperature},
            dotenv_path=None,
        )

    assert error.value.code == "INVALID_TEMPERATURE"


def test_TEST_CONFIG_REJECTS_EMPTY_MODEL() -> None:
    with pytest.raises(ConfigurationError) as error:
        load_settings(
            env={"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": ""},
            dotenv_path=None,
        )

    assert error.value.code == "INVALID_MODEL"


@pytest.mark.parametrize("timeout", ["0", "-1", "120.1", "nan", "inf", "invalid"])
def test_TEST_CONFIG_REJECTS_INVALID_TIMEOUT(timeout: str) -> None:
    with pytest.raises(ConfigurationError) as error:
        load_settings(
            env={"GEMINI_API_KEY": "test-key", "GEMINI_TIMEOUT_SECONDS": timeout},
            dotenv_path=None,
        )

    assert error.value.code == "INVALID_TIMEOUT"


@pytest.mark.parametrize("attempts", ["0", "4", "invalid"])
def test_TEST_CONFIG_REJECTS_UNBOUNDED_RETRY_COUNT(attempts: str) -> None:
    with pytest.raises(ConfigurationError) as error:
        load_settings(
            env={"GEMINI_API_KEY": "test-key", "GEMINI_MAX_ATTEMPTS": attempts},
            dotenv_path=None,
        )

    assert error.value.code == "INVALID_MAX_ATTEMPTS"


@pytest.mark.parametrize("call_limit", ["0", "-1", "141", "invalid"])
def test_TEST_CONFIG_REJECTS_INVALID_CALL_BUDGET(call_limit: str) -> None:
    with pytest.raises(ConfigurationError) as error:
        load_settings(
            env={"GEMINI_API_KEY": "test-key", "GEMINI_MAX_CALLS": call_limit},
            dotenv_path=None,
        )

    assert error.value.code == "INVALID_MAX_CALLS"


def test_TEST_CONFIG_USES_APPROVED_MODEL_AND_TEMPERATURE_DEFAULTS() -> None:
    settings = load_settings(env={"GEMINI_API_KEY": "test-key"}, dotenv_path=None)

    assert settings.model == "gemini-3.5-flash-lite"
    assert settings.temperature == 0.3
    assert settings.max_calls == 140
