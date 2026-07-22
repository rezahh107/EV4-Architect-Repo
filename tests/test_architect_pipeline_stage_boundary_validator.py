import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-architect-pipeline-stage-boundary.py"
spec = importlib.util.spec_from_file_location("asb", SCRIPT)
asb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asb)
VALID = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence"
FAILURE = ROOT / "fixtures/architect-pipeline-stage-boundary/invalid/cross-stage-architectures-to-decompose"


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def copy_sequence(tmp_path):
    target = tmp_path / "sequence"
    shutil.copytree(VALID, target)
    return target


def mutate_artifact(sequence, filename, mutation):
    path = sequence / filename
    value = load(path)
    mutation(value)
    write(path, value)


def assert_failure_case(tmp_path, case_id, filename, mutation, failed_stage, repair_target):
    sequence = copy_sequence(tmp_path)
    mutate_artifact(sequence, filename, mutation)
    bundle = tmp_path / "bundle"
    generated = asb.generate_transaction(sequence, bundle, ROOT)
    verified = asb.validate_bundle(bundle, ROOT)
    manifest = generated["manifest"]
    assert generated["run_validation_status"] == "invalid", case_id
    assert generated["authorization_valid"] is False
    assert manifest["authorized_next_stage"] is None
    assert manifest["repair_target_stage"] == repair_target
    assert len(manifest["boundaries"]) == 1
    assert len(manifest["anchors"]) == 1
    assert manifest["boundaries"][0]["path"] == "boundaries/repair.boundary.json"
    assert manifest["anchors"][0]["path"] == "anchors/repair.anchor.json"
    assert load(bundle / "failure-event.json")["failed_stage"] == failed_stage
    assert load(bundle / "failure-event.json")["repair_target_stage"] == repair_target
    assert load(bundle / "boundaries/repair.boundary.json")["authorization"]["next_stage_authorized"] is False
    assert load(bundle / "anchors/repair.anchor.json")["anchor_type"] == "REPAIR_ANCHOR"
    assert not list((bundle / "boundaries").glob("[!r]*.json"))
    assert not list((bundle / "anchors").glob("[!r]*.json"))
    assert verified["bundle_integrity_status"] == "valid"
    assert verified["run_validation_status"] == "invalid"
    assert verified["authorization_valid"] is False
    assert verified["verification_status"] == "invalid_bundle_verified"


@pytest.mark.parametrize(
    "case_id,filename,mutation,failed_stage,repair_target",
    [
        ("F01", "decompose.json", lambda x: x["payload"].pop("meaningful_content"), "/decompose", "/decompose"),
        ("F02", "architectures.json", lambda x: x["payload"]["architecture_coverage_matrix"].pop(), "/architectures", "/architectures"),
        ("F03", "architectures.json", lambda x: x["payload"].update(unknown_propagation_ledger=[]), "/architectures", "/decompose"),
        ("F04", "score-evidence.json", lambda x: x["payload"]["candidate_scores"][0].update(scores_audited=True), "/score-evidence", "/score-evidence"),
        ("F05", "score-evidence.json", lambda x: x["payload"]["candidate_scores"][0].update(candidate_id="C-NOT-IN-STAGE3"), "/score-evidence", "/architectures"),
        ("F06", "score-audit.json", lambda x: x["payload"].pop("allowed_next_stage"), "/score-audit", "/score-audit"),
        ("F07", "score-audit.json", lambda x: x["payload"]["validated_stage_4_artifact_ref"].update(artifact_id="wrong"), "/score-audit", "/score-evidence"),
    ],
)
def test_failure_ownership_matrix(tmp_path, case_id, filename, mutation, failed_stage, repair_target):
    assert_failure_case(tmp_path, case_id, filename, mutation, failed_stage, repair_target)


def test_success_bundle_is_deterministic_and_independently_verified(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    first = asb.generate_transaction(VALID, one, ROOT)
    second = asb.generate_transaction(VALID, two, ROOT)
    assert first["run_validation_status"] == "valid"
    assert first["authorization_valid"] is True
    assert {p.relative_to(one) for p in one.rglob("*") if p.is_file()} == {p.relative_to(two) for p in two.rglob("*") if p.is_file()}
    for path in one.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (two / path.relative_to(one)).read_bytes()
    verified = asb.validate_bundle(one, ROOT)
    assert verified["bundle_integrity_status"] == "valid"
    assert verified["run_validation_status"] == "valid"
    assert verified["authorization_valid"] is True


def test_failure_bundle_is_deterministic_and_independently_verified(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    first = asb.generate_transaction(FAILURE, one, ROOT)
    second = asb.generate_transaction(FAILURE, two, ROOT)
    assert first["run_validation_status"] == "invalid"
    for path in one.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (two / path.relative_to(one)).read_bytes()
    verified = asb.validate_bundle(one, ROOT)
    assert verified["verification_status"] == "invalid_bundle_verified"


def recompute_manifest(bundle):
    manifest_path = bundle / "manifest.json"
    manifest = load(manifest_path)
    for collection in ["artifacts", "receipts", "boundaries", "anchors"]:
        for entry in manifest[collection]:
            entry["sha256"] = asb.sha_file(bundle / entry["path"])
    if manifest.get("failure_event_path"):
        manifest["failure_event_sha256"] = asb.sha_file(bundle / manifest["failure_event_path"])
    manifest["bundle_content_digest"] = "0" * 64
    manifest["bundle_content_digest"] = asb.manifest_digest(manifest)
    write(manifest_path, manifest)


def mutate_json(bundle, rel, mutator, recompute=True):
    path = bundle / rel
    value = load(path)
    mutator(value)
    write(path, value)
    if recompute:
        recompute_manifest(bundle)


MUTATIONS = [
    ("run_id", "manifest.json", lambda x: x.update(run_id="other-run"), False),
    ("failed_stage", "failure-event.json", lambda x: x.update(failed_stage="/score-audit"), True),
    ("repair_target_stage", "failure-event.json", lambda x: x.update(repair_target_stage="/architectures"), True),
    ("failing_artifact.artifact_id", "failure-event.json", lambda x: x["failing_artifact"].update(artifact_id="forged"), True),
    ("failing_artifact.artifact_schema", "failure-event.json", lambda x: x["failing_artifact"].update(artifact_schema="historical"), True),
    ("failing_artifact.artifact_sha256", "failure-event.json", lambda x: x["failing_artifact"].update(artifact_sha256="0"*64), True),
    ("failing_receipt.receipt_id", "failure-event.json", lambda x: x["failing_receipt"].update(receipt_id="forged"), True),
    ("failing_receipt.receipt_sha256", "failure-event.json", lambda x: x["failing_receipt"].update(receipt_sha256="0"*64), True),
    ("diagnostics", "failure-event.json", lambda x: x.update(diagnostics=[]), True),
    ("invalidation_scope", "failure-event.json", lambda x: x["invalidation_scope"].update(downstream_authorization_revoked=False), True),
    ("failure_event_id", "failure-event.json", lambda x: x.update(failure_event_id="forged"), True),
    ("failure_event_schema", "failure-event.json", lambda x: x.update(failure_event_schema="historical"), True),
    ("boundary_id", "boundaries/repair.boundary.json", lambda x: x.update(boundary_id="forged"), True),
    ("boundary_schema", "boundaries/repair.boundary.json", lambda x: x.update(boundary_schema="ev4-stage-boundary-record@1.0.0"), True),
    ("transition", "boundaries/repair.boundary.json", lambda x: x.update(transition="next_stage"), True),
    ("source_stage", "boundaries/repair.boundary.json", lambda x: x.update(source_stage="/score-audit"), True),
    ("target_stage", "boundaries/repair.boundary.json", lambda x: x.update(target_stage="/score-evidence"), True),
    ("next_stage_authorized", "boundaries/repair.boundary.json", lambda x: x["authorization"].update(next_stage_authorized=True), True),
    ("anchor_id", "anchors/repair.anchor.json", lambda x: x.update(anchor_id="forged"), True),
    ("anchor_schema", "anchors/repair.anchor.json", lambda x: x.update(anchor_schema="ev4-stage-anchor@1.2.0"), True),
    ("anchor_type", "anchors/repair.anchor.json", lambda x: x.update(anchor_type="NEXT_STAGE_ANCHOR"), True),
    ("boundary_ref", "anchors/repair.anchor.json", lambda x: x["boundary_ref"].update(boundary_id="forged"), True),
    ("failure_event_ref", "anchors/repair.anchor.json", lambda x: x["failure_event_ref"].update(failure_event_id="forged"), True),
    ("critical_unknowns", "anchors/repair.anchor.json", lambda x: x["handoff_state"].update(critical_unknowns=[{"unknown_id":"FORGED","state":"unknown","evidence_refs":[]}]), True),
    ("blocking_items", "anchors/repair.anchor.json", lambda x: x["handoff_state"].update(blocking_items=[{"unknown_id":"FORGED","state":"blocked","evidence_refs":[]}]), True),
    ("confidence_delta", "anchors/repair.anchor.json", lambda x: x["handoff_state"].update(confidence_delta=["receipt_status:invalid"]), True),
    ("bundle_id", "manifest.json", lambda x: x.update(bundle_id="forged"), False),
    ("bundle_schema", "manifest.json", lambda x: x.update(bundle_schema="ev4-architect-validation-bundle@1.0.0"), False),
    ("stage_sequence", "manifest.json", lambda x: x.update(stage_sequence=list(reversed(x["stage_sequence"]))), False),
    ("authorized_next_stage", "manifest.json", lambda x: x.update(authorized_next_stage="/score-evidence"), False),
    ("bundle_content_digest", "manifest.json", lambda x: x.update(bundle_content_digest="0"*64), False),
]


@pytest.mark.parametrize("name,rel,mutator,recompute", MUTATIONS)
def test_adversarial_mutations_are_rejected(tmp_path, name, rel, mutator, recompute):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(FAILURE, bundle, ROOT)
    mutate_json(bundle, rel, mutator, recompute)
    result = asb.validate_bundle(bundle, ROOT)
    assert result["bundle_integrity_status"] == "invalid", name
    assert result["authorization_valid"] is False
    assert result["diagnostics"], name


def test_recalculated_failure_event_forgery_is_rejected(tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(FAILURE, bundle, ROOT)
    event = load(bundle / "failure-event.json")
    event["failed_stage"] = "/score-audit"
    write(bundle / "failure-event.json", event)
    event_hash = asb.sha_file(bundle / "failure-event.json")
    for rel in ["boundaries/repair.boundary.json", "anchors/repair.anchor.json"]:
        value = load(bundle / rel)
        value["failure_event_ref"]["failure_event_sha256"] = event_hash
        write(bundle / rel, value)
    recompute_manifest(bundle)
    result = asb.validate_bundle(bundle, ROOT)
    assert result["bundle_integrity_status"] == "invalid"


def test_missing_failing_artifact_is_rejected(tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(FAILURE, bundle, ROOT)
    (bundle / "artifacts/architectures.json").unlink()
    result = asb.validate_bundle(bundle, ROOT)
    assert result["diagnostics"][0]["code"] == "ASB-BUNDLE-FILE-SET-MISMATCH"


def test_extra_unlisted_json_is_rejected(tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(FAILURE, bundle, ROOT)
    write(bundle / "extra.json", {})
    result = asb.validate_bundle(bundle, ROOT)
    assert result["diagnostics"][0]["code"] == "ASB-BUNDLE-FILE-SET-MISMATCH"


def test_path_traversal_is_rejected(tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(FAILURE, bundle, ROOT)
    manifest = load(bundle / "manifest.json")
    manifest["artifacts"][0]["path"] = "../escape.json"
    manifest["bundle_content_digest"] = "0" * 64
    manifest["bundle_content_digest"] = asb.manifest_digest(manifest)
    write(bundle / "manifest.json", manifest)
    result = asb.validate_bundle(bundle, ROOT)
    assert result["diagnostics"][0]["code"] == "ASB-BUNDLE-PATH-TRAVERSAL"


def test_current_schemas_are_strict_and_valid():
    for path in sorted((ROOT / "schemas").glob("ev4-*.schema.json")):
        schema = load(path)
        Draft202012Validator.check_schema(schema)
        assert schema.get("additionalProperties") is False


def test_legacy_file_writing_flags_are_removed():
    text = SCRIPT.read_text()
    assert "--write-receipt" not in text
    assert "--write-receipts" not in text
    assert "--write-anchors" not in text
    assert "ev4-stage-anchor@1.2.0" not in text
    assert "ev4-stage-boundary-record@1.0.0" not in text
    assert "ev4-architect-validation-bundle@1.0.0" not in text


def test_confidence_delta_is_structured_and_receipt_status_is_gate_result(tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(VALID, bundle, ROOT)
    anchor = load(bundle / "anchors/architectures.anchor.json")
    assert anchor["handoff_state"]["confidence_delta"]
    assert all(isinstance(item, dict) for item in anchor["handoff_state"]["confidence_delta"])
    assert anchor["handoff_state"]["gate_results"]["receipt_status"] == "valid"
    assert "receipt_status:valid" not in anchor["handoff_state"]["confidence_delta"]


RESOLVED = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/resolved-inactive-unknowns-sequence"
STAGE_FILES = {
    "/decompose": "decompose.json",
    "/architectures": "architectures.json",
    "/score-evidence": "score-evidence.json",
    "/score-audit": "score-audit.json",
}


@pytest.mark.parametrize("stage,filename", list(STAGE_FILES.items()))
def test_exact_stage_version_map_rejects_each_independent_mutation(tmp_path, stage, filename):
    sequence = copy_sequence(tmp_path)
    mutate_artifact(
        sequence,
        filename,
        lambda value: value.update(stage_version="0.0.0-stale"),
    )
    bundle = tmp_path / "bundle"
    generated = asb.generate_transaction(sequence, bundle, ROOT)
    assert generated["run_validation_status"] == "invalid"
    assert generated["authorization_valid"] is False
    assert generated["manifest"]["repair_target_stage"] == stage
    receipt = load(bundle / f"receipts/{asb.stage_prefix(stage)}.receipt.json")
    assert any(item["code"] == "ASB-STAGE-VERSION-MISMATCH" for item in receipt["diagnostics"])
    assert asb.validate_bundle(bundle, ROOT)["verification_status"] == "invalid_bundle_verified"


def test_stage_documents_use_only_current_transaction_authority_path():
    for relative in [
        "stages/02_DECOMPOSE.md",
        "stages/03_ARCHITECTURES.md",
        "stages/04_SCORE_EVIDENCE.md",
        "stages/05_SCORE_AUDIT.md",
    ]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "--write-receipt" not in text
        assert "--write-receipts" not in text
        assert "--write-anchors" not in text
        assert "validate-run" in text
        assert "validate-bundle" in text
        assert "diagnose-artifact" in text
        assert "non-authorizing" in text
    for stage, filename in STAGE_FILES.items():
        stage_path = {
            "/decompose": ROOT / "stages/02_DECOMPOSE.md",
            "/architectures": ROOT / "stages/03_ARCHITECTURES.md",
            "/score-evidence": ROOT / "stages/04_SCORE_EVIDENCE.md",
            "/score-audit": ROOT / "stages/05_SCORE_AUDIT.md",
        }[stage]
        assert f"Version: {asb.stage_version(stage)}" in stage_path.read_text(encoding="utf-8")


def test_resolved_and_inactive_unknowns_authorize_without_active_propagation(tmp_path):
    bundle = tmp_path / "bundle"
    generated = asb.generate_transaction(RESOLVED, bundle, ROOT)
    verified = asb.validate_bundle(bundle, ROOT)
    assert generated["bundle_integrity_status"] == "valid"
    assert generated["run_validation_status"] == "valid"
    assert generated["authorization_valid"] is True
    assert verified["bundle_integrity_status"] == "valid"
    assert verified["run_validation_status"] == "valid"
    assert verified["authorization_valid"] is True
    stage4 = load(bundle / "artifacts/score-evidence.json")
    assert stage4["payload"]["uncertainty_register"] == []
    anchor = load(bundle / "anchors/architectures.anchor.json")
    assert anchor["handoff_state"]["critical_unknowns"] == []
    assert anchor["handoff_state"]["blocking_items"] == []


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.pop("resolving_evidence_refs"),
        lambda row: row.update(resolving_evidence_refs=["forged-evidence"]),
        lambda row: row.update(resolution_reason=""),
        lambda row: row.update(evidence_refs=["s2"]),
    ],
)
def test_resolved_unknown_requires_exact_named_evidence(tmp_path, mutation):
    sequence = tmp_path / "sequence"
    shutil.copytree(RESOLVED, sequence)
    artifact_path = sequence / "architectures.json"
    artifact = load(artifact_path)
    row = artifact["payload"]["unknown_propagation_ledger"][0]
    mutation(row)
    write(artifact_path, artifact)
    bundle = tmp_path / "bundle"
    generated = asb.generate_transaction(sequence, bundle, ROOT)
    assert generated["run_validation_status"] == "invalid"
    assert generated["authorization_valid"] is False
    assert generated["manifest"]["repair_target_stage"] == "/architectures"
    receipt = load(bundle / "receipts/architectures.receipt.json")
    assert receipt["status"] == "invalid"


@pytest.mark.parametrize(
    "case,expected_repair",
    [
        ("T19-missing-stage2", "/decompose"),
        ("T20-missing-stage3", "/architectures"),
        ("T21-missing-stage4", "/score-evidence"),
        ("T22-duplicate-stage2", "/decompose"),
        ("T23-stage-file-mismatch", "/architectures"),
    ],
)
def test_structural_failures_are_deterministic_non_authorizing_cli_results(tmp_path, case, expected_repair):
    sequence = ROOT / "fixtures/architect-pipeline-stage-boundary/invalid" / case
    outputs = [tmp_path / "one", tmp_path / "two"]
    results = []
    for output in outputs:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "validate-run",
                "--sequence",
                str(sequence),
                "--output",
                str(output),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 1
        assert completed.stderr == ""
        results.append(json.loads(completed.stdout))
        assert not output.exists()
    assert results[0] == results[1]
    result = results[0]
    assert result["bundle_integrity_status"] == "not_produced"
    assert result["run_validation_status"] == "invalid"
    assert result["authorization_valid"] is False
    assert result["output_published"] is False
    assert result["diagnostics"][0]["repair_target_stage"] == expected_repair


@pytest.mark.parametrize(
    "mutation",
    [
        lambda refs: refs[0].update(run_id="other-run"),
        lambda refs: refs[0].update(artifact_id="forged-artifact"),
        lambda refs: refs[0].update(artifact_schema="historical"),
        lambda refs: refs[0].update(artifact_sha256="0" * 64),
        lambda refs: refs[0].update(source_stage="/decompose"),
        lambda refs: refs.clear(),
        lambda refs: refs.append(copy.deepcopy(refs[0])),
    ],
)
def test_stage4_payload_lineage_is_exactly_bound_to_regenerated_stage3(tmp_path, mutation):
    sequence = copy_sequence(tmp_path)
    stage4_path = sequence / "score-evidence.json"
    stage4 = load(stage4_path)
    mutation(stage4["payload"]["validated_upstream_artifact_refs"])
    write(stage4_path, stage4)
    # The top-level source_artifacts reference remains untouched and valid.
    assert stage4["source_artifacts"] == load(VALID / "score-evidence.json")["source_artifacts"]
    bundle = tmp_path / "bundle"
    generated = asb.generate_transaction(sequence, bundle, ROOT)
    assert generated["run_validation_status"] == "invalid"
    assert generated["authorization_valid"] is False
    assert generated["manifest"]["repair_target_stage"] == "/architectures"
    event = load(bundle / "failure-event.json")
    assert event["failed_stage"] == "/score-evidence"
    assert event["repair_target_stage"] == "/architectures"
    assert asb.validate_bundle(bundle, ROOT)["verification_status"] == "invalid_bundle_verified"


def assert_safe_output_rejection(sequence, output, marker=None):
    result = asb.generate_transaction(sequence, output, ROOT)
    assert result["bundle_integrity_status"] == "not_produced"
    assert result["run_validation_status"] == "invalid"
    assert result["authorization_valid"] is False
    assert result["output_published"] is False
    if marker is not None:
        assert marker.read_text(encoding="utf-8") == "preserve-me"


def test_output_safety_rejects_repository_root_without_deletion():
    marker = ROOT / "README.md"
    before = marker.read_bytes()
    result = asb.generate_transaction(VALID, ROOT, ROOT)
    assert result["bundle_integrity_status"] == "not_produced"
    assert marker.read_bytes() == before


def test_output_safety_rejects_sequence_and_overlapping_paths(tmp_path):
    sequence = tmp_path / "workspace/sequence"
    shutil.copytree(VALID, sequence)
    assert_safe_output_rejection(sequence, sequence)
    marker = sequence.parent / "marker.txt"
    marker.write_text("preserve-me", encoding="utf-8")
    assert_safe_output_rejection(sequence, sequence.parent, marker)
    assert_safe_output_rejection(sequence, sequence / "nested-output")
    alias = tmp_path / "sequence-alias"
    alias.symlink_to(sequence, target_is_directory=True)
    assert_safe_output_rejection(sequence, alias)


def test_output_safety_rejects_unrelated_existing_directory_before_deletion(tmp_path):
    output = tmp_path / "unrelated"
    output.mkdir()
    marker = output / "marker.txt"
    marker.write_text("preserve-me", encoding="utf-8")
    assert_safe_output_rejection(VALID, output, marker)


def test_owned_bundle_replacement_is_permitted_and_deterministic(tmp_path):
    output = tmp_path / "bundle"
    first = asb.generate_transaction(VALID, output, ROOT)
    first_bytes = {
        path.relative_to(output): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    (output / "unlisted-user-file.txt").write_text("must not survive owned replacement", encoding="utf-8")
    second = asb.generate_transaction(VALID, output, ROOT)
    second_bytes = {
        path.relative_to(output): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert first["authorization_valid"] is True
    assert second["authorization_valid"] is True
    assert first_bytes == second_bytes
    assert Path("unlisted-user-file.txt") not in second_bytes


def test_failed_generation_never_publishes_partial_or_replaces_owned_output(tmp_path, monkeypatch):
    output = tmp_path / "bundle"
    asb.generate_transaction(VALID, output, ROOT)
    before = {
        path.relative_to(output): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    globals_map = asb.generate_transaction.__globals__
    original = globals_map["_render_transaction"]

    def fail_after_partial_write(result, sequence, temp_output, root):
        (temp_output / "partial.txt").write_text("partial", encoding="utf-8")
        raise RuntimeError("synthetic render failure")

    monkeypatch.setitem(globals_map, "_render_transaction", fail_after_partial_write)
    with pytest.raises(RuntimeError, match="synthetic render failure"):
        asb.generate_transaction(VALID, output, ROOT)
    monkeypatch.setitem(globals_map, "_render_transaction", original)
    after = {
        path.relative_to(output): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert before == after
    assert not list(tmp_path.glob(".bundle.asb-tmp-*"))


def test_manifest_stage_documents_and_all_artifact_fixtures_share_exact_version_map():
    manifest = load(ROOT / "manifests/architect-pipeline-manifest.v1.json")
    manifest_versions = {
        stage["stage_id"]: stage["stage_version"]
        for stage in manifest["project_execution_stages"]
    }
    implemented = set(asb.implemented_stage_order())
    fixture_root = ROOT / "fixtures/architect-pipeline-stage-boundary"
    checked = 0
    for path in sorted(fixture_root.rglob("*.json")):
        try:
            value = load(path)
        except (json.JSONDecodeError, OSError):
            continue
        if (
            isinstance(value, dict)
            and value.get("artifact_schema") == asb.ARTIFACT_SCHEMA
            and "payload" in value
            and value.get("stage_id") in implemented
        ):
            checked += 1
            assert value["stage_version"] == manifest_versions[value["stage_id"]], path
    assert checked >= 100
