import copy
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys

from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-architect-pipeline-stage-boundary.py"
spec = importlib.util.spec_from_file_location("asb", SCRIPT)
asb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asb)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True)


def payload(completed):
    assert completed.stdout, completed.stderr
    return json.loads(completed.stdout)


def codes(result):
    return [diagnostic["code"] for diagnostic in result["diagnostics"]]


def validate_case(case_id):
    return asb.Validator(ROOT).validate_sequence(ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def make_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    completed = run("validate-run", "--sequence", "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence", "--output", str(bundle), "--format", "json")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return bundle


def validate_bundle(bundle):
    return run("validate-bundle", "--bundle", str(bundle), "--format", "json")


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


def test_schema_and_semantic_negative_fixtures_fail_with_declared_codes():
    expected = {
        "T01": "SCHEMA_VALIDATION_FAILED",
        "T02": "SCHEMA_VALIDATION_FAILED",
        "T03": "SCHEMA_VALIDATION_FAILED",
        "T04": "ASB-DUPLICATE-UNKNOWN-ID",
        "T05": "ASB-MISSING-PREDECESSOR-STAGE",
        "T06": "ASB-MISSING-PREDECESSOR-STAGE",
        "T07": "ASB-UNKNOWN-LEDGER-MISSING-UPSTREAM-ID",
        "T08": "ASB-UNKNOWN-RESOLVED-WITHOUT-EVIDENCE",
        "T09": "ASB-CANDIDATE-UNTRACKED-UNKNOWN",
        "T10": "ASB-UPSTREAM-VALIDATION-REQUIRED",
        "T11": "ASB-DOWNSTREAM-RECONSTRUCTION-FORBIDDEN",
        "T12": "ASB-CANDIDATE-NOT-IN-VALIDATED-STAGE3",
        "T16": "ASB-FINAL-TOTAL-WITH-UNKNOWN",
        "T17": "ASB-MISSING-PREDECESSOR-STAGE",
    }
    for case_id, code in expected.items():
        result = validate_case(case_id)
        assert result["status"] == "invalid", case_id
        assert code in codes(result), (case_id, codes(result))


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


def test_lineage_mutation_fixture_matrix_is_complete_and_field_specific():
    expected_fields = ["run_id", "artifact_id", "artifact_schema", "artifact_sha256", "source_stage"]
    for prefix in ["T24-stage3-source", "T25-stage4-ref", "T26-stage5-ref"]:
        for field in expected_fields:
            case_id = f"{prefix}-{field}"
            case_dir = ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case_id
            assert case_dir.exists(), case_id
            result = validate_case(case_id)
            assert result["status"] == "invalid"
            expected_code = f"ASB-LINEAGE-{field.upper().replace('_', '-')}-MISMATCH"
            assert expected_code in codes(result), (case_id, codes(result))


def test_incident_regression_fails_at_earliest_stage2_boundary():
    result = validate_case("incident-fail-late")
    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["stage_id"] == "/decompose"
    assert result["diagnostics"][0]["rule_id"] == "ASB-R01"


def test_external_receipts_and_anchors_are_diagnostic_only_not_authority(tmp_path):
    fixture = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence-receipts-anchors"
    stage3 = run(
        "--artifact", str(fixture / "artifacts/architectures.json"),
        "--upstream-artifact", str(fixture / "artifacts/decompose.json"),
        "--upstream-receipt", str(fixture / "receipts/decompose.receipt.json"),
        "--format", "json",
    )
    result = payload(stage3)
    assert stage3.returncode == 1
    assert result["diagnostic_only"] is True
    assert result["authorization_valid"] is False
    assert "ASB-STANDALONE-ARTIFACT-NOT-AUTHORITY" in codes(result)

    anchor = run(
        "--anchor", str(fixture / "anchors/architectures.anchor.json"),
        "--anchor-source-artifact", str(fixture / "artifacts/architectures.json"),
        "--anchor-source-receipt", str(fixture / "receipts/architectures.receipt.json"),
        "--anchor-source-boundary", str(fixture / "boundaries/architectures.boundary.json"),
        "--format", "json",
    )
    anchor_result = payload(anchor)
    assert anchor.returncode == 1
    assert anchor_result["diagnostic_only"] is True
    assert anchor_result["authorization_valid"] is False
    assert "ASB-STANDALONE-ANCHOR-NOT-AUTHORITY" in codes(anchor_result)


def test_forged_valid_receipt_for_semantically_invalid_upstream_does_not_authorize(tmp_path):
    sequence = tmp_path / "sequence"
    shutil.copytree(ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence", sequence)
    invalid = load(sequence / "decompose.json")
    invalid["payload"].pop("unknowns")
    write_json(sequence / "decompose.json", invalid)
    forged = asb.Validator(ROOT).receipt(invalid, asb.sha(sequence / "decompose.json"), "/decompose", [])
    write_json(sequence / "decompose.receipt.json", forged)
    completed = run("validate-run", "--sequence", str(sequence), "--output", str(tmp_path / "bundle"), "--format", "json")
    result = payload(completed)
    assert completed.returncode == 1
    assert result["status"] == "invalid"
    assert result["manifest"]["authorized_next_stage"] is None
    assert "SCHEMA_VALIDATION_FAILED" in codes(result)


def test_validate_run_failure_bundle_contains_no_success_authorization(tmp_path):
    sequence = tmp_path / "sequence"
    shutil.copytree(ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence", sequence)
    architectures = load(sequence / "architectures.json")
    architectures["payload"].pop("architecture_coverage_matrix")
    write_json(sequence / "architectures.json", architectures)
    bundle = tmp_path / "bundle"
    completed = run("validate-run", "--sequence", str(sequence), "--output", str(bundle), "--format", "json")
    result = payload(completed)
    assert completed.returncode == 1
    assert result["manifest"]["overall_status"] == "invalid"
    assert result["manifest"]["authorized_next_stage"] is None
    assert result["manifest"]["repair_target_stage"] == "/architectures"
    boundaries = [load(path) for path in (bundle / "boundaries").glob("*.json")]
    anchors = [load(path) for path in (bundle / "anchors").glob("*.json")]
    assert sum(1 for boundary in boundaries if boundary["authorization"]["next_stage_authorized"] is True) == 0
    assert sum(1 for anchor in anchors if anchor["anchor_type"] == "NEXT_STAGE_ANCHOR") == 0


def test_validate_run_clears_stale_success_evidence_before_failed_rerun(tmp_path):
    sequence = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence"
    output = tmp_path / "bundle"
    assert run("validate-run", "--sequence", str(sequence), "--output", str(output), "--format", "json").returncode == 0
    success_anchor = output / "anchors" / "decompose.anchor.json"
    assert success_anchor.exists()
    bad_sequence = tmp_path / "bad-sequence"
    shutil.copytree(sequence, bad_sequence)
    bad = load(bad_sequence / "architectures.json")
    bad["payload"].pop("architecture_coverage_matrix")
    write_json(bad_sequence / "architectures.json", bad)
    failed = run("validate-run", "--sequence", str(bad_sequence), "--output", str(output), "--format", "json")
    assert failed.returncode == 1
    assert not success_anchor.exists()
    assert all(load(path)["authorization"]["next_stage_authorized"] is False for path in (output / "boundaries").glob("*.json"))


def test_validate_bundle_independently_regenerates_and_rejects_mutations(tmp_path):
    mutation_matrix = [
        ("manifest.json", ["bundle_id"], "mutated"),
        ("manifest.json", ["bundle_schema"], "mutated"),
        ("manifest.json", ["bundle_content_digest"], "0" * 64),
        ("manifest.json", ["stage_sequence"], ["/architectures", "/decompose", "/score-evidence", "/score-audit"]),
        ("manifest.json", ["authorized_next_stage"], "/architectures"),
        ("receipts/decompose.receipt.json", ["run_id"], "other-run"),
        ("receipts/decompose.receipt.json", ["artifact_id"], "mutated"),
        ("receipts/decompose.receipt.json", ["artifact_schema"], "mutated"),
        ("receipts/decompose.receipt.json", ["artifact_sha256"], "0" * 64),
        ("receipts/decompose.receipt.json", ["receipt_id"], "mutated"),
        ("receipts/decompose.receipt.json", ["receipt_schema"], "mutated"),
        ("receipts/decompose.receipt.json", ["validator_id"], "mutated"),
        ("receipts/decompose.receipt.json", ["validator_version"], "mutated"),
        ("receipts/decompose.receipt.json", ["status"], "invalid"),
        ("receipts/decompose.receipt.json", ["diagnostics"], [{"code":"X","rule_id":"ASB-R01","stage_id":"/decompose","path":"$","expected":"x","observed":"y"}]),
        ("boundaries/decompose.boundary.json", ["boundary_id"], "mutated"),
        ("boundaries/decompose.boundary.json", ["boundary_schema"], "mutated"),
        ("boundaries/decompose.boundary.json", ["transition"], "repair"),
        ("boundaries/decompose.boundary.json", ["target_stage"], None),
        ("boundaries/decompose.boundary.json", ["repair_target_stage"], "/decompose"),
        ("boundaries/decompose.boundary.json", ["authorization", "next_stage_authorized"], False),
        ("anchors/decompose.anchor.json", ["anchor_id"], "mutated"),
        ("anchors/decompose.anchor.json", ["anchor_schema"], "mutated"),
        ("anchors/decompose.anchor.json", ["anchor_type"], "REPAIR_ANCHOR"),
        ("anchors/decompose.anchor.json", ["boundary_ref", "boundary_id"], "mutated"),
        ("anchors/architectures.anchor.json", ["handoff_state", "critical_unknowns"], []),
        ("anchors/architectures.anchor.json", ["handoff_state", "blocking_items"], []),
    ]
    for rel, path, value in mutation_matrix:
        bundle = make_bundle(tmp_path / rel.replace("/", "_").replace(".", "_"))
        target = bundle / rel
        data = load(target)
        cursor = data
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = value
        write_json(target, data)
        result = payload(validate_bundle(bundle))
        assert result["status"] == "invalid", (rel, path)
        result_codes = codes(result)
        assert (
            "ASB-BUNDLE-CARRIER-BYTE-MISMATCH" in result_codes
            or "ASB-BUNDLE-STATUS-CONTRADICTS-REGENERATED" in result_codes
            or any(code.startswith("ASB-BUNDLE-") and code.endswith("-SHA256-MISMATCH") for code in result_codes)
            or any(code.endswith("SCHEMA-VALIDATION-FAILED") for code in result_codes)
        ), (rel, path, result_codes)


def test_validate_bundle_rejects_path_traversal_extra_and_substituted_files(tmp_path):
    bundle = make_bundle(tmp_path / "path")
    manifest = load(bundle / "manifest.json")
    manifest["stages"][0]["artifact_path"] = "../outside.json"
    write_json(bundle / "manifest.json", manifest)
    result = payload(validate_bundle(bundle))
    assert result["status"] == "invalid"
    assert "ASB-BUNDLE-PATH-TRAVERSAL" in codes(result)

    bundle = make_bundle(tmp_path / "extra")
    write_json(bundle / "receipts" / "extra.receipt.json", load(bundle / "receipts" / "decompose.receipt.json"))
    result = payload(validate_bundle(bundle))
    assert "ASB-BUNDLE-EXTRA-FILE" in codes(result)

    bundle = make_bundle(tmp_path / "sub")
    shutil.copyfile(bundle / "receipts" / "architectures.receipt.json", bundle / "receipts" / "decompose.receipt.json")
    result = payload(validate_bundle(bundle))
    assert "ASB-BUNDLE-CARRIER-BYTE-MISMATCH" in codes(result) or "ASB-BUNDLE-RECEIPT-SHA256-MISMATCH" in codes(result)


def test_generated_schema_instances_and_positive_fixtures_validate(tmp_path):
    bundle = make_bundle(tmp_path / "schema")
    schemas = {kind: json.loads((ROOT / rel).read_text()) for kind, rel in asb.CARRIER_SCHEMAS.items()}
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    Draft202012Validator(schemas["bundle"]).validate(load(bundle / "manifest.json"))
    for stage in load(bundle / "manifest.json")["stages"]:
        Draft202012Validator(schemas["artifact"]).validate(load(bundle / stage["artifact_path"]))
        Draft202012Validator(schemas["receipt"]).validate(load(bundle / stage["receipt_path"]))
        Draft202012Validator(schemas["boundary"]).validate(load(bundle / stage["boundary_path"]))
        Draft202012Validator(schemas["anchor"]).validate(load(bundle / stage["anchor_path"]))
    for artifact in (ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence").glob("*.json"):
        Draft202012Validator(schemas["artifact"]).validate(load(artifact))


def test_architectures_anchor_preserves_active_u1_unknown(tmp_path):
    bundle = make_bundle(tmp_path / "anchor")
    architectures = load(bundle / "artifacts" / "architectures.json")
    assert any(row["unknown_id"] == "U-1" and row["state"] in asb.ACTIVE_UNKNOWN_STATES for row in architectures["payload"]["unknown_propagation_ledger"])
    anchor = load(bundle / "anchors" / "architectures.anchor.json")
    assert "U-1" in {item.get("unknown_id") for item in anchor["handoff_state"]["critical_unknowns"]}


def test_empty_sequence_fails_closed_with_stable_diagnostic(tmp_path):
    result = run("--sequence", str(tmp_path), "--format", "json")
    assert result.returncode == 1
    output = payload(result)
    assert output["status"] == "invalid"
    assert output["diagnostics"][0]["code"] == "ASB-EMPTY-SEQUENCE"


def test_fixture_cli_and_json_sequence_output():
    assert run("--fixtures").returncode == 0
    completed = run("--sequence", "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence", "--format", "json")
    assert completed.returncode == 0
    assert payload(completed)["status"] == "valid"
