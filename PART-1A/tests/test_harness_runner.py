import json
import sys

from scripts.run_harness import execute_gate, write_report


def test_nonzero_gate_exit_is_preserved_as_failure(tmp_path):
    result = execute_gate(
        "intentional-failure",
        (
            sys.executable,
            "-c",
            "import sys; print('gate output'); print('gate error', file=sys.stderr); sys.exit(7)",
        ),
        cwd=tmp_path,
    )

    assert result.status == "FAIL"
    assert result.return_code == 7
    assert result.stdout.strip() == "gate output"
    assert result.stderr.strip() == "gate error"


def test_report_preserves_gate_results_and_pass_status(tmp_path):
    report_path = write_report(
        [execute_gate("passing-gate", (sys.executable, "-c", "pass"), cwd=tmp_path)],
        tmp_path,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["gates"][0]["status"] == "PASS"
