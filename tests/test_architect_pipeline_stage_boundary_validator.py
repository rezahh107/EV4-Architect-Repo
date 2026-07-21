import copy
import importlib.util
import json
import shutil
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
