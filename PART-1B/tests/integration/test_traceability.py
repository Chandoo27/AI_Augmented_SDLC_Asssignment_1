from pathlib import Path

from reminder_agent.evaluation import validate_traceability

ROOT = Path(__file__).parents[2]
MANIFEST_PATH = ROOT / "evals" / "traceability.json"
SPECIFICATION_PATH = ROOT / "specs" / "001-reminder-agent" / "spec.md"


def test_TEST_TRACEABILITY_COVERS_EVERY_FUNCTIONAL_AND_NONFUNCTIONAL_REQUIREMENT() -> None:
    coverage = validate_traceability(MANIFEST_PATH, SPECIFICATION_PATH)

    assert len(coverage) == 24
    assert all(case_ids for case_ids in coverage.values())
    assert len(coverage["NFR-009"]) == 12
    assert "EV-HARNESS-CALL-BUDGET-001" in coverage["NFR-010"]
