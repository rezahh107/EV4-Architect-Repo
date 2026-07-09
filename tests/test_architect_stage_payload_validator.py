import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-architect-stage-payload.py"

spec = importlib.util.spec_from_file_location("architect_payload_validator", SCRIPT)
validator_module = importlib.util.module_from_spec(spec)
sys.modules["architect_payload_validator"] = validator_module
assert spec.loader is not None
spec.loader.exec_module(validator_module)


def run_validator_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def load_minimal_payload():
    return json.loads((ROOT / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json").read_text(encoding="utf-8"))


def mutate_payload(dotted_path, replacement):
    payload = load_minimal_payload()
    current = payload
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[int(part)] if part.isdigit() else current[part]
    if parts[-1].isdigit():
        current[int(parts[-1])] = replacement
    else:
        current[parts[-1]] = replacement
    return payload


def test_fixture_suite_passes():
    failures, reports = validator_module.validate_fixture_suite(ROOT)
    assert failures == 0
    assert len(reports) == 20


def test_kernel_decision_escape_route_fixtures_have_stable_diagnostics():
    failures, reports = validator_module.validate_fixture_suite(ROOT)
    assert failures == 0
    expected = {
        "architecture-family-without-kernel-decision-record": "ARCH-KERNEL-DECISION-001",
        "asset-intent-without-kernel-media-choice-record": "ARCH-KERNEL-DECISION-002",
        "scoped-css-without-kernel-styling-record": "ARCH-KERNEL-DECISION-003",
    }
    for case_id, diagnostic in expected.items():
        report = next(item for item in reports if item["fixture"].endswith(f"#{case_id}"))
        assert report["actual"] == "invalid"
        assert diagnostic in report["diagnostic_codes"]


def test_invalid_fixture_rejected_with_stable_rule_code():
    failures, reports = validator_module.validate_fixture_suite(ROOT)
    assert failures == 0
    dynamic = next(item for item in reports if item["fixture"].endswith("#dynamic-loop-inferred-without-evidence"))
    assert dynamic["actual"] == "invalid"
    assert "A_R09_DYNAMIC_LOOP_UNSUPPORTED" in dynamic["diagnostic_codes"]


def test_insufficient_evidence_fixture_classified_distinctly():
    validator = validator_module.ArchitectPayloadValidator(ROOT)
    payload = validator.validate_file(ROOT / "fixtures/architect-stage-payload/insufficient-evidence/missing-real-stage-output.v1.json")
    assert payload["status"] == "insufficient_evidence"
    assert payload["diagnostics"] == []


def test_missing_file_returns_structured_invalid_without_traceback():
    completed = run_validator_cli("--file", "fixtures/architect-stage-payload/invalid/missing-file.json", "--format", "json")
    assert completed.returncode == 1
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["status"] == "invalid"
    assert payload["diagnostics"][0]["code"] == "FILE_READ_ERROR"


def test_array_and_primitive_inputs_are_invalid_not_crashes(tmp_path):
    validator = validator_module.ArchitectPayloadValidator(ROOT)
    array_file = tmp_path / "array.json"
    primitive_file = tmp_path / "primitive.json"
    array_file.write_text("[]", encoding="utf-8")
    primitive_file.write_text('"not-object"', encoding="utf-8")

    for file_path in [array_file, primitive_file]:
        payload = validator.validate_file(file_path)
        assert payload["status"] == "invalid"
        assert payload["diagnostics"][0]["code"] == "INPUT_NOT_OBJECT"


def test_diagnostic_order_is_deterministic():
    validator = validator_module.ArchitectPayloadValidator(ROOT)
    payload = load_minimal_payload()
    payload["architecture_identity"]["decision_source"]["evidence_refs"] = []
    payload["architecture_identity"]["decision_source"]["locked_decision_refs"] = []
    first = validator.validate_value(payload)["diagnostics"]
    second = validator.validate_value(payload)["diagnostics"]
    assert first == second


def test_cli_json_smoke_valid_fixture():
    completed = run_validator_cli(
        "--file",
        "fixtures/architect-stage-payload/valid/minimal-complete.v1.json",
        "--expect",
        "valid",
        "--format",
        "json",
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "valid"


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        ("evidence_register", None),
        ("evidence_register", 7),
        ("approved_structure_model", None),
        ("approved_structure_model.structure_nodes", {"not": "an array"}),
        ("architecture_identity.decision_source", None),
        ("forbidden_work", None),
        ("architect_intent", None),
        ("architect_intent.scoped_css_intent", []),
        ("architect_intent.dynamic_loop_intent.evidence_refs", None),
        ("architect_intent.responsive_risk_seeds", {"not": "an array"}),
    ],
)
def test_schema_invalid_nested_types_fail_before_semantic_rules(path, replacement):
    validator = validator_module.ArchitectPayloadValidator(ROOT)
    payload = mutate_payload(path, replacement)

    first = validator.validate_value(payload)
    second = validator.validate_value(copy.deepcopy(payload))

    assert first == second
    assert first["status"] == "invalid"
    codes = [item["code"] for item in first["diagnostics"]]
    assert "SCHEMA_VALIDATION_FAILED" in codes
    assert all(code == "SCHEMA_VALIDATION_FAILED" for code in codes)
    assert all("rule_id" not in item for item in first["diagnostics"])


def test_cli_schema_invalid_nested_type_returns_structured_json_without_traceback(tmp_path):
    payload = mutate_payload("evidence_register", None)
    malformed = tmp_path / "schema-invalid-nested-type.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    first = run_validator_cli("--file", str(malformed), "--format", "json")
    second = run_validator_cli("--file", str(malformed), "--format", "json")

    assert first.returncode == 1
    assert second.returncode == 1
    assert first.stderr == ""
    assert second.stderr == ""
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert result["status"] == "invalid"
    assert [item["code"] for item in result["diagnostics"]] == ["SCHEMA_VALIDATION_FAILED"]
