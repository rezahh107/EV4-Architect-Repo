import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-architect-sequence-lineage.py"

spec = importlib.util.spec_from_file_location("architect_sequence_lineage", SCRIPT)
sequence_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(sequence_module)


def run_sequence_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def test_sequence_lineage_fixture_suite_passes():
    failures, reports = sequence_module.validate_sequence_suite(ROOT)
    assert failures == 0
    assert len(reports) == 2


def test_valid_sequence_preserves_required_kernel_lineage_fields():
    result = sequence_module.validate_sequence(
        ROOT,
        ROOT / "fixtures/architect-stage-payload/sequence/valid/lineage-preserved.v1.json",
    )
    assert result == {"status": "valid", "diagnostics": []}


def test_invalid_sequence_missing_lineage_field_fails_with_stable_code():
    result = sequence_module.validate_sequence(
        ROOT,
        ROOT / "fixtures/architect-stage-payload/sequence/invalid/lineage-break-missing-evidence-refs.v1.json",
    )
    assert result["status"] == "invalid"
    codes = [item["code"] for item in result["diagnostics"]]
    assert "ARCH-SEQUENCE-LINEAGE-DRIFT" in codes


def test_cli_rejects_invalid_sequence_fixture():
    completed = run_sequence_cli(
        "--file",
        "fixtures/architect-stage-payload/sequence/invalid/lineage-break-missing-evidence-refs.v1.json",
        "--expect",
        "invalid",
        "--format",
        "json",
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["status"] == "invalid"
