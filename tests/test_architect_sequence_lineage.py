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


def load_minimal_payload():
    return json.loads((ROOT / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json").read_text(encoding="utf-8"))


def write_sequence_fixture(tmp_path, steps):
    sequence = {
        "schema_id": "ev4-architect-sequence-lineage-fixture@1.0.0",
        "purpose": "test-generated-sequence",
        "steps": steps,
    }
    fixture = tmp_path / "sequence.json"
    fixture.write_text(json.dumps(sequence), encoding="utf-8")
    return fixture


def test_sequence_uses_sliding_baseline_for_intermediate_decision_records(tmp_path):
    first = load_minimal_payload()
    second = load_minimal_payload()
    introduced_record = {
        "decision_family": "class_scope",
        "decision_card_ref": "kernel/decision-governance/p0-decision-matrices.v0.json#decision_family_id=class_scope",
        "selected_option": "selected class scope remains local",
        "rejected_options": ["global selector scope"],
        "evidence_refs": ["ev-stage8"],
        "evidence_state": "proposed",
    }
    second["kernel_decision_records"].append(introduced_record)
    third = load_minimal_payload()
    fixture = write_sequence_fixture(
        tmp_path,
        [
            {"step_id": "section_plan_generation", "payload": first},
            {"step_id": "revision_or_reopen_flow", "payload": second},
            {"step_id": "handoff_package_generation", "payload": third},
        ],
    )

    result = sequence_module.validate_sequence(ROOT, fixture)

    assert result["status"] == "invalid"
    missing = next(item for item in result["diagnostics"] if item["code"] == "ARCH-SEQUENCE-LINEAGE-RECORD-MISSING")
    assert missing["decision_family"] == "class_scope"
    assert missing["baseline_step_id"] == "revision_or_reopen_flow"


def test_sequence_list_lineage_fields_compare_order_independently(tmp_path):
    first = load_minimal_payload()
    second = load_minimal_payload()
    second["kernel_decision_records"][0]["evidence_refs"] = list(reversed(second["kernel_decision_records"][0]["evidence_refs"]))
    second["kernel_decision_records"][0]["rejected_options"] = list(reversed(second["kernel_decision_records"][0]["rejected_options"]))
    fixture = write_sequence_fixture(
        tmp_path,
        [
            {"step_id": "section_plan_generation", "payload": first},
            {"step_id": "handoff_package_generation", "payload": second},
        ],
    )

    result = sequence_module.validate_sequence(ROOT, fixture)

    assert result == {"status": "valid", "diagnostics": []}


def test_payload_validator_loader_reuses_cached_instance():
    sequence_module._PAYLOAD_VALIDATOR_CACHE.clear()

    first = sequence_module._load_payload_validator(ROOT)
    second = sequence_module._load_payload_validator(ROOT)

    assert first is second
