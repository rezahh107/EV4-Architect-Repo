import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-architect-pipeline-stage-boundary.py"
spec = importlib.util.spec_from_file_location("asb", SCRIPT)
asb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asb)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True)


def codes(result):
    return [diagnostic["code"] for diagnostic in result["diagnostics"]]


def validate_case(case_id):
    return asb.Validator(ROOT).validate_sequence(ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id)


def test_valid_complete_sequence_passes_and_receipts_are_deterministic():
    validator = asb.Validator(ROOT)
    sequence = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence"
    first = validator.validate_sequence(sequence)
    second = validator.validate_sequence(sequence)
    assert first == second
    assert first["status"] == "valid"
    assert len(first["receipts"]) == 4


def test_resolved_inactive_unknowns_may_be_omitted_from_stage4_uncertainty_register():
    result = asb.Validator(ROOT).validate_sequence(ROOT / "fixtures/architect-pipeline-stage-boundary/valid/resolved-inactive-unknowns-sequence")
    assert result["status"] == "valid"


def test_t01_to_t06_boundary_schema_failures():
    expected = {
        "T01": "SCHEMA_VALIDATION_FAILED",
        "T02": "SCHEMA_VALIDATION_FAILED",
        "T03": "SCHEMA_VALIDATION_FAILED",
        "T04": "ASB-DUPLICATE-UNKNOWN-ID",
        "T05": "SCHEMA_VALIDATION_FAILED",
        "T06": "SCHEMA_VALIDATION_FAILED",
    }
    validator = asb.Validator(ROOT)
    for case_id, code in expected.items():
        artifact = next((ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id).glob("*.json"))
        result = validator.validate_path(artifact)
        assert result["status"] == "invalid"
        assert code in codes(result)
        assert result["diagnostics"][0]["path"].startswith("$")


def test_sequence_unknown_lineage_and_resolution_rules():
    expected = {
        "T07": "ASB-UNKNOWN-LEDGER-MISSING-UPSTREAM-ID",
        "T08": "ASB-UNKNOWN-RESOLVED-WITHOUT-EVIDENCE",
        "T09": "ASB-CANDIDATE-UNTRACKED-UNKNOWN",
    }
    for case_id, code in expected.items():
        result = validate_case(case_id)
        assert result["status"] == "invalid"
        assert code in codes(result)
        assert result["diagnostics"][0]["repair_target_stage"] in {"/decompose", "/architectures"}


def test_stage4_rejects_missing_receipt_reconstruction_bad_candidate_and_unknown_total():
    expected = {
        "T10": "ASB-UPSTREAM-VALIDATION-REQUIRED",
        "T11": "ASB-DOWNSTREAM-RECONSTRUCTION-FORBIDDEN",
        "T12": "ASB-CANDIDATE-NOT-IN-VALIDATED-STAGE3",
        "T16": "ASB-FINAL-TOTAL-WITH-UNKNOWN",
    }
    for case_id, code in expected.items():
        assert code in codes(validate_case(case_id))


def test_sequence_rejects_missing_duplicate_and_stage_mismatch_boundaries():
    expected = {
        "T19-missing-stage2": ("ASB-MISSING-PREDECESSOR-STAGE", "/decompose"),
        "T20-missing-stage3": ("ASB-MISSING-PREDECESSOR-STAGE", "/decompose"),
        "T21-missing-stage4": ("ASB-MISSING-PREDECESSOR-STAGE", "/decompose"),
        "T22-duplicate-stage2": ("ASB-DUPLICATE-STAGE-ARTIFACT", "/decompose"),
        "T23-stage-file-mismatch": ("ASB-STAGE-FILE-MISMATCH", "/decompose"),
    }
    for case_id, (code, stage) in expected.items():
        result = validate_case(case_id)
        assert result["status"] == "invalid"
        assert result["diagnostics"][0]["code"] == code
        assert result["diagnostics"][0]["stage_id"] == stage


def test_lineage_mutations_fail_for_stage3_stage4_and_stage5_refs():
    expected_fields = ["artifact_id", "artifact_schema", "artifact_sha256", "validation_receipt_id", "validation_status", "source_stage"]
    for prefix in ["T24-stage3-source", "T25-stage4-ref", "T26-stage5-ref"]:
        for field in expected_fields:
            result = validate_case(f"{prefix}-{field}")
            assert result["status"] == "invalid"
            assert f"ASB-LINEAGE-{field.upper().replace('_', '-')}-MISMATCH" in codes(result)


def test_anchor_mutations_have_field_specific_diagnostics():
    fields = {
        "T27-anchor-source_artifact-artifact_id": "ASB-ANCHOR-SOURCE-ARTIFACT-ARTIFACT-ID-MISMATCH",
        "T27-anchor-source_artifact-artifact_schema": "ASB-ANCHOR-SOURCE-ARTIFACT-ARTIFACT-SCHEMA-MISMATCH",
        "T27-anchor-source_artifact-artifact_sha256": "ASB-ANCHOR-SOURCE-ARTIFACT-ARTIFACT-SHA256-MISMATCH",
        "T27-anchor-source_artifact-stage_id": "ASB-ANCHOR-SOURCE-ARTIFACT-STAGE-ID-MISMATCH",
        "T27-anchor-source_validation-receipt_id": "ASB-ANCHOR-SOURCE-VALIDATION-RECEIPT-ID-MISMATCH",
        "T27-anchor-source_validation-validator_version": "ASB-ANCHOR-SOURCE-VALIDATION-VALIDATOR-VERSION-MISMATCH",
        "T27-anchor-source_validation-status": "ASB-ANCHOR-SOURCE-VALIDATION-STATUS-MISMATCH",
    }
    validator = asb.Validator(ROOT)
    for case_id, code in fields.items():
        artifact = next((ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id).glob("*.json"))
        result = validator.validate_path(artifact)
        assert result["status"] == "invalid"
        assert code in codes(result)


def test_anchor_schema_constrained_validation_fields_fail_schema_validation():
    validator = asb.Validator(ROOT)
    for case_id in ["T27-anchor-source_validation-receipt_schema", "T27-anchor-source_validation-validator_id"]:
        artifact = next((ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id).glob("*.json"))
        result = validator.validate_path(artifact)
        assert result["status"] == "invalid"
        assert "SCHEMA_VALIDATION_FAILED" in codes(result)


def test_anchor_and_stage5_fail_closed():
    validator = asb.Validator(ROOT)
    for case_id, code in {"T14": "ASB-ANCHOR-SOURCE-ARTIFACT-ARTIFACT-SHA256-MISMATCH", "T15": "ASB-ANCHOR-VALID-RECEIPT-REQUIRED", "T17": "ASB-STAGE5-MISSING-VALID-STAGE4"}.items():
        artifact = next((ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id).glob("*.json"))
        result = validator.validate_path(artifact)
        assert result["status"] == "invalid"
        assert code in codes(result)


def test_incident_regression_fails_at_earliest_stage2_boundary():
    result = validate_case("incident-fail-late")
    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["stage_id"] == "/decompose"
    assert result["diagnostics"][0]["rule_id"] == "ASB-R01"


def test_receipt_digest_changes_with_exact_bytes_and_cli_writes_receipt(tmp_path):
    source = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/decompose.valid.json"
    first_artifact = tmp_path / "a.json"
    changed_artifact = tmp_path / "b.json"
    first_artifact.write_bytes(source.read_bytes())
    changed_artifact.write_bytes(source.read_bytes() + b"\n")
    first = json.loads(run("--artifact", str(first_artifact), "--format", "json").stdout)
    changed = json.loads(run("--artifact", str(changed_artifact), "--format", "json").stdout)
    assert first["artifact_sha256"] != changed["artifact_sha256"]
    output = tmp_path / "receipt.json"
    completed = run("--artifact", str(first_artifact), "--write-receipt", str(output))
    assert completed.returncode == 0
    assert json.loads(output.read_text())["status"] == "valid"


def test_fixture_cli_and_json_sequence_output():
    assert run("--fixtures").returncode == 0
    completed = run("--sequence", "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence", "--format", "json")
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "valid"
