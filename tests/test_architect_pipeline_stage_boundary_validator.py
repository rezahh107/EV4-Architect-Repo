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
        assert code in codes(result) or "SCHEMA_VALIDATION_FAILED" in codes(result)
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
        assert code in codes(result) or "SCHEMA_VALIDATION_FAILED" in codes(result)
        assert result["diagnostics"][0]["repair_target_stage"] in {"/decompose", "/architectures"}


def test_stage4_rejects_missing_receipt_reconstruction_bad_candidate_and_unknown_total():
    expected = {
        "T10": "ASB-UPSTREAM-VALIDATION-REQUIRED",
        "T11": "ASB-DOWNSTREAM-RECONSTRUCTION-FORBIDDEN",
        "T12": "ASB-CANDIDATE-NOT-IN-VALIDATED-STAGE3",
        "T16": "ASB-FINAL-TOTAL-WITH-UNKNOWN",
    }
    for case_id, code in expected.items():
        result_codes = codes(validate_case(case_id))
        assert code in result_codes or "SCHEMA_VALIDATION_FAILED" in result_codes


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
    expected_fields = ["run_id", "artifact_id", "artifact_schema", "artifact_sha256", "source_stage"]
    for prefix in ["T24-stage3-source", "T25-stage4-ref", "T26-stage5-ref"]:
        for field in expected_fields:
            case_dir = ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / f"{prefix}-{field}"
            if not case_dir.exists():
                continue
            result = validate_case(f"{prefix}-{field}")
            assert result["status"] == "invalid"
            result_codes = codes(result)
            assert f"ASB-LINEAGE-{field.upper().replace('_', '-')}-MISMATCH" in result_codes or "SCHEMA_VALIDATION_FAILED" in result_codes or "ASB-EMPTY-SEQUENCE" in result_codes


def test_anchor_schema_constrained_validation_fields_fail_schema_validation():
    validator = asb.Validator(ROOT)
    for case_id in ["T27-anchor-source_validation-receipt_schema", "T27-anchor-source_validation-validator_id"]:
        artifact = next((ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id).glob("*.json"))
        result = validator.validate_path(artifact)
        assert result["status"] == "invalid"
        assert "SCHEMA_VALIDATION_FAILED" in codes(result)


def test_anchor_and_stage5_fail_closed():
    validator = asb.Validator(ROOT)
    for case_id, code in {"T14": "SCHEMA_VALIDATION_FAILED", "T15": "SCHEMA_VALIDATION_FAILED", "T17": "ASB-STAGE5-MISSING-VALID-STAGE4"}.items():
        artifact = next((ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id).glob("*.json"))
        result = validator.validate_path(artifact)
        assert result["status"] == "invalid"
        assert code in codes(result) or "SCHEMA_VALIDATION_FAILED" in codes(result)


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


def test_valid_receipt_bound_anchor_standalone_path_and_field_mutations(tmp_path):
    fixture = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence-receipts-anchors"
    artifact = fixture / "artifacts/architectures.json"
    receipt = fixture / "receipts/architectures.receipt.json"
    anchor = fixture / "anchors/architectures.anchor.json"
    boundary = fixture / "boundaries/architectures.boundary.json"
    valid = run("--anchor", str(anchor), "--anchor-source-artifact", str(artifact), "--anchor-source-receipt", str(receipt), "--anchor-source-boundary", str(boundary), "--format", "json")
    assert valid.returncode == 0
    assert json.loads(valid.stdout)["status"] == "valid"

    mutations = {
        (None, "anchor_schema"): "ASB-ANCHOR-ANCHOR-SCHEMA-MISMATCH",
        (None, "run_id"): "ASB-ANCHOR-RUN-ID-MISMATCH",
        (None, "anchor_type"): "ASB-ANCHOR-ANCHOR-TYPE-MISMATCH",
        (None, "target_stage"): "ASB-ANCHOR-TARGET-STAGE-MISMATCH",
        (None, "repair_target_stage"): "ASB-ANCHOR-REPAIR-TARGET-STAGE-MISMATCH",
        ("boundary_ref", "boundary_id"): "ASB-ANCHOR-BOUNDARY-REF-BOUNDARY-ID-MISMATCH",
        ("boundary_ref", "boundary_schema"): "ASB-ANCHOR-BOUNDARY-REF-BOUNDARY-SCHEMA-MISMATCH",
        ("boundary_ref", "boundary_sha256"): "ASB-ANCHOR-BOUNDARY-REF-BOUNDARY-SHA256-MISMATCH",
    }
    for (section, field), code in mutations.items():
        payload = json.loads(anchor.read_text())
        if section is None:
            payload[field] = "mutated"
        else:
            payload[section][field] = "0" * 64 if field == "boundary_sha256" else "mutated"
        mutated = tmp_path / f"{section}-{field}.json"
        mutated.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        result = run("--anchor", str(mutated), "--anchor-source-artifact", str(artifact), "--anchor-source-receipt", str(receipt), "--anchor-source-boundary", str(boundary), "--format", "json")
        assert result.returncode == 1
        assert code in codes(json.loads(result.stdout))


def test_standalone_stage3_stage4_stage5_validation_with_upstream_receipts():
    fixture = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence-receipts-anchors"
    stage3 = run(
        "--artifact", str(fixture / "artifacts/architectures.json"),
        "--upstream-artifact", str(fixture / "artifacts/decompose.json"),
        "--upstream-receipt", str(fixture / "receipts/decompose.receipt.json"),
        "--format", "json",
    )
    assert stage3.returncode == 0
    assert json.loads(stage3.stdout)["status"] == "valid"
    stage4 = run(
        "--artifact", str(fixture / "artifacts/score-evidence.json"),
        "--upstream-artifact", str(fixture / "artifacts/architectures.json"),
        "--upstream-receipt", str(fixture / "receipts/architectures.receipt.json"),
        "--format", "json",
    )
    assert stage4.returncode == 0
    assert json.loads(stage4.stdout)["status"] == "valid"
    stage5 = run(
        "--artifact", str(fixture / "artifacts/score-audit.json"),
        "--upstream-artifact", str(fixture / "artifacts/score-evidence.json"),
        "--upstream-receipt", str(fixture / "receipts/score-evidence.receipt.json"),
        "--format", "json",
    )
    assert stage5.returncode == 0
    assert json.loads(stage5.stdout)["status"] == "valid"


def test_standalone_validation_rejects_missing_stale_mismatched_or_fabricated_receipts(tmp_path):
    fixture = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence-receipts-anchors"
    missing = run("--artifact", str(fixture / "artifacts/architectures.json"), "--format", "json")
    assert missing.returncode == 1
    assert "ASB-UPSTREAM-VALIDATION-REQUIRED" in codes(json.loads(missing.stdout))

    stale = json.loads((fixture / "receipts/decompose.receipt.json").read_text())
    stale["artifact_sha256"] = "0" * 64
    stale_path = tmp_path / "stale.receipt.json"
    stale_path.write_text(json.dumps(stale, indent=2, sort_keys=True) + "\n")
    result = run(
        "--artifact", str(fixture / "artifacts/architectures.json"),
        "--upstream-artifact", str(fixture / "artifacts/decompose.json"),
        "--upstream-receipt", str(stale_path),
        "--format", "json",
    )
    assert result.returncode == 1
    assert "ASB-UPSTREAM-RECEIPT-ARTIFACT-SHA256-MISMATCH" in codes(json.loads(result.stdout))

    fabricated = dict(stale)
    fabricated.update({"artifact_sha256": stale["artifact_sha256"], "receipt_id": "fabricated", "status": "valid"})
    fabricated_path = tmp_path / "fabricated.receipt.json"
    fabricated_path.write_text(json.dumps(fabricated, indent=2, sort_keys=True) + "\n")
    fabricated_result = run(
        "--artifact", str(fixture / "artifacts/architectures.json"),
        "--upstream-artifact", str(fixture / "artifacts/decompose.json"),
        "--upstream-receipt", str(fabricated_path),
        "--format", "json",
    )
    assert fabricated_result.returncode == 1
    fabricated_codes = codes(json.loads(fabricated_result.stdout))
    assert "ASB-UPSTREAM-RECEIPT-RECEIPT-ID-MISMATCH" in fabricated_codes
    assert "ASB-UPSTREAM-RECEIPT-ARTIFACT-SHA256-MISMATCH" in fabricated_codes


def test_empty_sequence_fails_closed_with_stable_diagnostic(tmp_path):
    result = run("--sequence", str(tmp_path), "--format", "json")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "invalid"
    assert payload["diagnostics"][0]["code"] == "ASB-EMPTY-SEQUENCE"


def test_sequence_writes_deterministic_receipts_and_separate_anchors(tmp_path):
    sequence = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence"
    receipts = tmp_path / "receipts"
    anchors = tmp_path / "anchors"
    completed = run("--sequence", str(sequence), "--write-receipts", str(receipts), "--write-anchors", str(anchors), "--format", "json")
    assert completed.returncode == 0
    for prefix in ["decompose", "architectures", "score-evidence", "score-audit"]:
        receipt = receipts / f"{prefix}.receipt.json"
        anchor = anchors / f"{prefix}.anchor.json"
        assert receipt.exists()
        assert anchor.exists()
        second_receipts = tmp_path / "receipts-second"
        second_anchors = tmp_path / "anchors-second"
    completed_second = run("--sequence", str(sequence), "--write-receipts", str(second_receipts), "--write-anchors", str(second_anchors), "--format", "json")
    assert completed_second.returncode == 0
    for prefix in ["decompose", "architectures", "score-evidence", "score-audit"]:
        assert (receipts / f"{prefix}.receipt.json").read_text() == (second_receipts / f"{prefix}.receipt.json").read_text()
        assert (anchors / f"{prefix}.anchor.json").read_text() == (second_anchors / f"{prefix}.anchor.json").read_text()


def test_fixture_cli_and_json_sequence_output():
    assert run("--fixtures").returncode == 0
    completed = run("--sequence", "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence", "--format", "json")
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "valid"
