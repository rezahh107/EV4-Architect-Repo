import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-architect-pipeline-stage-boundary.py"
spec = importlib.util.spec_from_file_location("asb_tx", SCRIPT)
asb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asb)
VALID = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence"
FAILURE = ROOT / "fixtures/architect-pipeline-stage-boundary/invalid/cross-stage-architectures-to-decompose"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def recompute_manifest(bundle: Path):
    manifest_path = bundle / "manifest.json"
    manifest = load(manifest_path)
    for collection in ["artifacts", "receipts", "boundaries", "anchors"]:
        for entry in manifest[collection]:
            target = bundle / entry["path"]
            if target.exists():
                entry["sha256"] = asb.sha_file(target)
    if manifest.get("failure_event_path") and (bundle / manifest["failure_event_path"]).exists():
        manifest["failure_event_sha256"] = asb.sha_file(bundle / manifest["failure_event_path"])
    manifest["bundle_content_digest"] = "0" * 64
    manifest["bundle_content_digest"] = asb.manifest_digest(manifest)
    write(manifest_path, manifest)


def assert_rejected(bundle: Path, expected_code: str | None = None):
    result = asb.validate_bundle(bundle, ROOT)
    assert result["bundle_integrity_status"] == "invalid"
    assert result["run_validation_status"] == "unknown"
    assert result["authorization_valid"] is False
    assert result["diagnostics"]
    if expected_code:
        assert result["diagnostics"][0]["code"] == expected_code


def make_failure(tmp_path: Path) -> Path:
    bundle = tmp_path / "failure"
    generated = asb.generate_transaction(FAILURE, bundle, ROOT)
    assert generated["run_validation_status"] == "invalid"
    return bundle


def make_success(tmp_path: Path) -> Path:
    bundle = tmp_path / "success"
    generated = asb.generate_transaction(VALID, bundle, ROOT)
    assert generated["run_validation_status"] == "valid"
    return bundle


def test_changed_failing_artifact_with_manifest_only_is_rejected(tmp_path):
    bundle = make_failure(tmp_path)
    path = bundle / "artifacts/architectures.json"
    artifact = load(path)
    artifact["artifact_id"] = "forged-failing-artifact"
    write(path, artifact)
    recompute_manifest(bundle)
    assert_rejected(bundle)


def test_substituted_invalid_receipt_is_rejected(tmp_path):
    bundle = make_failure(tmp_path)
    path = bundle / "receipts/architectures.receipt.json"
    receipt = load(path)
    receipt["diagnostics"][0]["path"] = "$/forged"
    write(path, receipt)
    recompute_manifest(bundle)
    assert_rejected(bundle)


def test_success_boundary_inserted_into_failure_bundle_is_rejected(tmp_path):
    failure = make_failure(tmp_path)
    success = make_success(tmp_path)
    source = success / "boundaries/decompose.boundary.json"
    target = failure / "boundaries/forged-success.boundary.json"
    shutil.copyfile(source, target)
    manifest = load(failure / "manifest.json")
    value = load(target)
    manifest["boundaries"].append(asb.file_entry("boundaries/forged-success.boundary.json", value, asb.sha_file(target), "boundary"))
    manifest["bundle_content_digest"] = "0" * 64
    manifest["bundle_content_digest"] = asb.manifest_digest(manifest)
    write(failure / "manifest.json", manifest)
    assert_rejected(failure)


def test_next_anchor_inserted_into_failure_bundle_is_rejected(tmp_path):
    failure = make_failure(tmp_path)
    success = make_success(tmp_path)
    source = success / "anchors/decompose.anchor.json"
    target = failure / "anchors/forged-next.anchor.json"
    shutil.copyfile(source, target)
    manifest = load(failure / "manifest.json")
    value = load(target)
    manifest["anchors"].append(asb.file_entry("anchors/forged-next.anchor.json", value, asb.sha_file(target), "anchor"))
    manifest["bundle_content_digest"] = "0" * 64
    manifest["bundle_content_digest"] = asb.manifest_digest(manifest)
    write(failure / "manifest.json", manifest)
    assert_rejected(failure)


@pytest.mark.parametrize(
    "rel",
    [
        "anchors/repair.anchor.json",
        "failure-event.json",
        "receipts/decompose.receipt.json",
    ],
)
def test_required_failure_evidence_removal_is_rejected(tmp_path, rel):
    bundle = make_failure(tmp_path)
    (bundle / rel).unlink()
    assert_rejected(bundle, "ASB-BUNDLE-FILE-SET-MISMATCH")


def test_failure_event_duplication_is_rejected(tmp_path):
    bundle = make_failure(tmp_path)
    shutil.copyfile(bundle / "failure-event.json", bundle / "failure-event-copy.json")
    assert_rejected(bundle, "ASB-BUNDLE-FILE-SET-MISMATCH")


def test_manifest_with_empty_artifact_directory_is_rejected(tmp_path):
    bundle = make_failure(tmp_path)
    for path in (bundle / "artifacts").glob("*.json"):
        path.unlink()
    assert_rejected(bundle, "ASB-BUNDLE-FILE-SET-MISMATCH")


def test_cross_run_artifact_splice_is_rejected(tmp_path):
    bundle = make_failure(tmp_path)
    artifact_path = bundle / "artifacts/decompose.json"
    artifact = load(artifact_path)
    artifact["run_id"] = "other-run"
    write(artifact_path, artifact)
    recompute_manifest(bundle)
    assert_rejected(bundle)


def test_failure_event_manifest_hash_substitution_is_rejected(tmp_path):
    bundle = make_failure(tmp_path)
    manifest = load(bundle / "manifest.json")
    manifest["failure_event_sha256"] = "0" * 64
    manifest["bundle_content_digest"] = "0" * 64
    manifest["bundle_content_digest"] = asb.manifest_digest(manifest)
    write(bundle / "manifest.json", manifest)
    assert_rejected(bundle, "ASB-FAILURE-EVENT-HASH-MISMATCH")


@pytest.mark.parametrize(
    "rel,mutator",
    [
        ("boundaries/score-audit.boundary.json", lambda x: x["authorization"].update(next_stage_authorized=False)),
        ("boundaries/score-audit.boundary.json", lambda x: x.update(target_stage=None)),
        ("anchors/score-audit.anchor.json", lambda x: x.update(anchor_type="REPAIR_ANCHOR")),
        ("anchors/architectures.anchor.json", lambda x: x["handoff_state"].update(confidence_delta=["receipt_status:valid"])),
        ("manifest.json", lambda x: x.update(authorized_next_stage="/score-audit")),
    ],
)
def test_success_bundle_authorization_mutations_are_rejected(tmp_path, rel, mutator):
    bundle = make_success(tmp_path)
    path = bundle / rel
    value = load(path)
    mutator(value)
    write(path, value)
    if rel != "manifest.json":
        recompute_manifest(bundle)
    else:
        value["bundle_content_digest"] = "0" * 64
        value["bundle_content_digest"] = asb.manifest_digest(value)
        write(path, value)
    assert_rejected(bundle)


def test_duplicate_stage_entry_is_rejected(tmp_path):
    bundle = make_failure(tmp_path)
    manifest = load(bundle / "manifest.json")
    manifest["artifacts"].append(dict(manifest["artifacts"][0]))
    manifest["bundle_content_digest"] = "0" * 64
    manifest["bundle_content_digest"] = asb.manifest_digest(manifest)
    write(bundle / "manifest.json", manifest)
    assert_rejected(bundle, "ASB-BUNDLE-DUPLICATE-PATH")
