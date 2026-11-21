import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]
QUICKSTART_PATH = ROOT / "specs" / "001-reminder-agent" / "quickstart.md"
WORKFLOW_PATH = ROOT.parent / ".github" / "workflows" / "ci.yml"
PYPROJECT_PATH = ROOT / "pyproject.toml"


def test_TEST_QUICKSTART_DOCUMENTS_EVALUATION_AND_PRIVACY_REQUIREMENTS() -> None:
    quickstart = QUICKSTART_PATH.read_text(encoding="utf-8")

    for required_text in (
        "GEMINI_API_KEY",
        "reminder-agent-evaluate",
        "140",
        "95%",
        "raw request text",
        "rotated",
    ):
        assert required_text in quickstart


def test_TEST_CI_WORKFLOW_RUNS_REQUIRED_QUALITY_GATES() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    for required_command in (
        "ruff format --check",
        "ruff check",
        "mypy src/reminder_agent",
        "pytest --cov --cov-branch",
        "bandit -q -r src/reminder_agent",
        "detect-secrets scan -n",
        "pip_audit",
    ):
        assert required_command in workflow


def test_TEST_COVERAGE_THRESHOLD_IS_CONFIGURED() -> None:
    configuration = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    coverage = configuration["tool"]["coverage"]

    assert coverage["report"]["fail_under"] == 90
    assert coverage["run"]["branch"] is True
    assert set(coverage["run"]["source"]) == {
        "reminder_agent.engine",
        "reminder_agent.gemini_client",
        "reminder_agent.output",
        "reminder_agent.validation",
    }
