import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-architect-pipeline-stage-boundary.py"
PROFILE_CHECK = ROOT / "scripts/check-architect-validation-profiles.py"

spec = importlib.util.spec_from_file_location("asb_profiles", SCRIPT)
asb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asb)

check_spec = importlib.util.spec_from_file_location("profile_check", PROFILE_CHECK)
profile_check = importlib.util.module_from_spec(check_spec)
check_spec.loader.exec_module(profile_check)

VALID = ROOT / "fixtures/architect-pipeline-stage-boundary/valid/complete-sequence"
FAILURE = ROOT / "fixtures/architect-pipeline-stage-boundary/invalid/cross-stage-architectures-to-decompose"
STAGE_FILES = {
    "/decompose": "decompose.json",
    "/architectures": "architectures.json",
    "/score-evidence": "score-evidence.json",
    "/score-audit": "score-audit.json",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prefix_sequence(tmp_path: Path, through_stage: str) -> Path:
    target = tmp_path / f"sequence-{through_stage.removeprefix('/')}"
    target.mkdir()
    order = list(asb.implemented_stage_order())
    for stage in order[: order.index(through_stage) + 1]:
        shutil.copy2(VALID / STAGE_FILES[stage], target / STAGE_FILES[stage])
    return target


def test_manifest_and_registry_expose_one_complete_topology():
    authority = asb.PIPELINE_AUTHORITY
    assert authority.stage_order == (
        "/intake",
        "/research",
        "/decompose",
        "/architectures",
        "/score-evidence",
        "/score-audit",
        "/recommend",
        "/build-tree",
        "/implementation",
        "/final-audit",
        "/handoff-export",
        "/project-gate-export",
    )
    assert set(authority.profiles) == set(authority.stage_order)
    assert authority.terminal_stage == "/project-gate-export"
    for index, stage in enumerate(authority.stage_order):
        exposed = asb.exposed_profile(authority, stage)
        assert exposed["ordinal"] == index + 1
        assert exposed["mandatory"] is True
        assert exposed["stage_version"] == authority.stage_version(stage)
        assert exposed["terminal"] is (stage == authority.terminal_stage)
        assert exposed["topology"]["predecessor"] == (
            authority.stage_order[index - 1] if index else None
        )
        assert exposed["topology"]["successor"] == (
            authority.stage_order[index + 1]
            if index + 1 < len(authority.stage_order)
            else None
        )


def test_registry_is_capability_only_and_profiles_are_truthful():
    authority = asb.PIPELINE_AUTHORITY
    assert authority.registry["authorization_role"] == "validation_capability_only"
    assert authority.implemented_stage_order == tuple(STAGE_FILES)
    for stage, profile in authority.profiles.items():
        validation = profile["validation"]
        if stage in STAGE_FILES:
            assert validation["status"] == "full_transaction_implemented"
            assert validation["executable"] is True
            assert validation["authorization_capable"] is True
            assert profile["receipt"]["supported"] is True
            assert profile["bundle"]["independent_regeneration"] is True
            assert profile["repair"]["ownership_status"] == "deterministic"
        else:
            assert validation["executable"] is False
            assert validation["authorization_capable"] is False
            assert profile["receipt"]["supported"] is False
            assert profile["bundle"]["supported"] is False
    assert authority.profiles["/project-gate-export"]["validation"]["status"] == "terminal"


@pytest.mark.parametrize("stage", list(STAGE_FILES))
def test_each_implemented_profile_generates_and_independently_regenerates(stage, tmp_path):
    sequence = prefix_sequence(tmp_path, stage)
    bundle = tmp_path / f"bundle-{stage.removeprefix('/')}"
    generated = asb.generate_transaction(sequence, bundle, ROOT)
    verified = asb.validate_bundle(bundle, ROOT)
    assert generated["run_validation_status"] == "valid"
    assert generated["authorization_valid"] is True
    assert generated["manifest"]["authorized_next_stage"] == asb.stage_successor(stage)
    assert verified["verification_status"] == "valid_bundle_verified"
    assert verified["authorization_valid"] is True


def mutate_invalid(stage: str, artifact: dict):
    if stage == "/decompose":
        artifact["payload"].pop("visible_groups")
    elif stage == "/architectures":
        artifact["payload"]["architecture_coverage_matrix"] = artifact["payload"][
            "architecture_coverage_matrix"
        ][:-1]
    elif stage == "/score-evidence":
        artifact["payload"]["candidate_scores"][0]["scores_audited"] = True
    elif stage == "/score-audit":
        artifact["payload"]["validated_stage_4_artifact_ref"]["artifact_sha256"] = "0" * 64


@pytest.mark.parametrize("stage", list(STAGE_FILES))
def test_each_implemented_profile_has_a_fail_closed_negative_transaction(stage, tmp_path):
    sequence = prefix_sequence(tmp_path, stage)
    path = sequence / STAGE_FILES[stage]
    value = load(path)
    mutate_invalid(stage, value)
    write(path, value)
    bundle = tmp_path / f"failure-{stage.removeprefix('/')}"
    generated = asb.generate_transaction(sequence, bundle, ROOT)
    verified = asb.validate_bundle(bundle, ROOT)
    assert generated["run_validation_status"] == "invalid"
    assert generated["authorization_valid"] is False
    assert generated["manifest"]["authorized_next_stage"] is None
    assert verified["verification_status"] == "invalid_bundle_verified"
    assert verified["authorization_valid"] is False


NON_EXECUTABLE = [
    stage
    for stage in asb.PIPELINE_AUTHORITY.stage_order
    if stage not in STAGE_FILES
]


@pytest.mark.parametrize("stage", NON_EXECUTABLE)
def test_non_executable_profiles_never_emit_a_bundle(stage, tmp_path):
    sequence = tmp_path / "sequence"
    sequence.mkdir()
    write(sequence / f"{stage.removeprefix('/')}.json", {"stage_id": stage})
    output = tmp_path / "bundle"
    result = asb.generate_transaction(sequence, output, ROOT)
    assert result["bundle_integrity_status"] == "not_produced"
    assert result["authorization_valid"] is False
    assert result["output_published"] is False
    assert not output.exists()
    assert result["diagnostics"][0]["code"] == "ASB-STAGE-VALIDATION-NOT-IMPLEMENTED"


def test_full_manifest_transition_matrix_and_anchor_authorization_boundary():
    authority = asb.PIPELINE_AUTHORITY
    for source in authority.stage_order:
        successor = authority.successor(source)
        if successor is None:
            terminal = {
                "anchor_type": "NEXT_STAGE_ANCHOR",
                "source_stage": source,
                "target_stage": "/intake",
            }
            errors = asb.anchor_semantic_diagnostics(terminal, authority)
            assert errors[0]["code"] == "ASB-ANCHOR-TERMINAL-CONTINUATION"
            continue
        anchor = {
            "anchor_schema": asb.ANCHOR_SCHEMA,
            "anchor_type": "NEXT_STAGE_ANCHOR",
            "source_stage": source,
            "target_stage": successor,
        }
        state = asb.standalone_anchor_state(anchor, authority)
        assert state["legal_manifest_edge"] is True
        assert state["authorization_valid"] is False
        errors = asb.anchor_semantic_diagnostics(anchor, authority)
        if authority.is_implemented(source):
            assert errors == []
            assert state["source_stage_validation_implemented"] is True
        else:
            assert errors[0]["code"] == "ASB-ANCHOR-SOURCE-NOT-AUTHORIZATION-CAPABLE"
            assert state["source_stage_validation_implemented"] is False

        illegal_targets = {
            authority.stage_order[0],
            authority.stage_order[-1],
            source,
        } - {successor}
        for target in illegal_targets:
            invalid = {**anchor, "target_stage": target}
            errors = asb.anchor_semantic_diagnostics(invalid, authority)
            assert errors[0]["code"] == "ASB-ANCHOR-TOPOLOGY-INVALID"

    unknown_source = {
        "anchor_type": "NEXT_STAGE_ANCHOR",
        "source_stage": "/unknown-stage",
        "target_stage": authority.stage_order[0],
    }
    assert asb.anchor_semantic_diagnostics(unknown_source, authority)[0]["code"] == (
        "ASB-ANCHOR-UNKNOWN-SOURCE-STAGE"
    )
    unknown_target = {
        "anchor_type": "NEXT_STAGE_ANCHOR",
        "source_stage": authority.stage_order[0],
        "target_stage": "/unknown-stage",
    }
    assert asb.anchor_semantic_diagnostics(unknown_target, authority)[0]["code"] == (
        "ASB-ANCHOR-TOPOLOGY-INVALID"
    )


def test_generated_anchor_is_schema_valid_but_never_standalone_authority(tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(VALID, bundle, ROOT)
    anchor = load(bundle / "anchors/decompose.anchor.json")
    state = asb.standalone_anchor_state(anchor, asb.PIPELINE_AUTHORITY)
    assert state == {
        "anchor_schema_valid": True,
        "legal_manifest_edge": True,
        "source_stage_validation_implemented": True,
        "independently_regenerated_bundle_required": True,
        "anchor_alone_authorizes": False,
        "authorization_valid": False,
    }


def test_schema_valid_legal_anchor_from_blocked_source_remains_non_authorizing(tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(VALID, bundle, ROOT)
    anchor = load(bundle / "anchors/decompose.anchor.json")
    anchor["source_stage"] = "/intake"
    anchor["target_stage"] = "/research"
    state = asb.standalone_anchor_state(anchor, asb.PIPELINE_AUTHORITY)
    assert state == {
        "anchor_schema_valid": True,
        "legal_manifest_edge": True,
        "source_stage_validation_implemented": False,
        "independently_regenerated_bundle_required": True,
        "anchor_alone_authorizes": False,
        "authorization_valid": False,
    }
    assert asb.anchor_semantic_diagnostics(anchor, asb.PIPELINE_AUTHORITY)[0][
        "code"
    ] == "ASB-ANCHOR-SOURCE-NOT-AUTHORIZATION-CAPABLE"


@pytest.mark.parametrize("historical", ["1.1.0", "1.2.0", "1.3.0"])
def test_historical_anchors_are_readable_but_never_current_authority(historical, tmp_path):
    bundle = tmp_path / "bundle"
    asb.generate_transaction(VALID, bundle, ROOT)
    anchor = load(bundle / "anchors/decompose.anchor.json")
    original = copy.deepcopy(anchor)
    anchor["anchor_schema"] = f"ev4-stage-anchor@{historical}"
    schema = load(ROOT / "schemas/ev4-stage-anchor.v1.4.schema.json")
    assert list(Draft202012Validator(schema).iter_errors(anchor))
    state = asb.standalone_anchor_state(anchor, asb.PIPELINE_AUTHORITY)
    assert state["anchor_schema_valid"] is False
    assert state["authorization_valid"] is False
    assert original["anchor_schema"] == "ev4-stage-anchor@1.4.0"


SUCCESS_STABLE_HASHES = {
    "artifacts/decompose.json": "93950a7321f82215dc409d403800278bf654544668bdb09f50cd86d8cb6fe6da",
    "artifacts/architectures.json": "5996ee7be86035cb8819e12a82c2300b1ee75c1bbbd1686e3b6f5cc5d3937c4a",
    "artifacts/score-evidence.json": "f458ae10eae882b3c99d460a262c6117d523d112e02b14d861fbc60f7138b75a",
    "artifacts/score-audit.json": "c699a51daa2678384f3c07756216c9f442856cc7d394bc0ea9e66cfed14a992e",
    "receipts/decompose.receipt.json": "cf970e7b76fa1616a4cade612cc619c875149e7579a0ab221b23e1dba61ac020",
    "receipts/architectures.receipt.json": "5357ff665a6bf30b2312f38369a6395194e2dcad62ae83b5edbccb0393bb1c08",
    "receipts/score-evidence.receipt.json": "9ff704e2195f7c3d7669edc4e88074f9da99cb943226181ec7e67d23e041d2bc",
    "receipts/score-audit.receipt.json": "63946ab1d0ea5ee00d5292682c1e56c0d4f2a17898c841d091024519b3a77a1c",
    "boundaries/decompose.boundary.json": "549e672ff9a660de4130c23209b487cd3165db4ffbaea71976aa64d4023861b6",
    "boundaries/architectures.boundary.json": "7e2177521649aa5d5e014e932d329663d43bc8ea7eaf275d4a787e7014037ccd",
    "boundaries/score-evidence.boundary.json": "38a0a1566038f1b401c16eb02954b36d900617ab7c1df63eeb6dafe2f681e355",
    "boundaries/score-audit.boundary.json": "63a229c40d2958876a71859855474f68fcb4b9e1bb1609e6ee6768cc1d61fe6a",
}
SUCCESS_HISTORICAL_ANCHOR_HASHES = {
    "decompose": "c317b8a07a4092606a6593f8e547a423083d4fc2bce9cfbe5b30fb8d7fceebbb",
    "architectures": "39d6f3f72ff7cc81921ecb7afc7df7b3f46c8998bd057ec90b5954d126a91a47",
    "score-evidence": "7de32bd8078b74ce395e287ed46d64e3829c188030cf514ba4f0d99c710717b1",
    "score-audit": "8f4b968581c004cbe4e5a39b901cba5751cd2a4400092994fecf0bcf6e974e2d",
}


def compatibility_projection(manifest: dict, historical_anchor_hashes: dict[str, str]):
    projected = copy.deepcopy(manifest)
    projected["bundle_schema"] = "ev4-architect-validation-bundle@1.1.0"
    for entry in projected["anchors"]:
        stem = Path(entry["path"]).name.removesuffix(".anchor.json")
        entry["schema"] = "ev4-stage-anchor@1.3.0"
        entry["sha256"] = historical_anchor_hashes[stem]
    projected["bundle_content_digest"] = "0" * 64
    projected["bundle_content_digest"] = asb.manifest_digest(projected)
    return projected


def test_existing_success_transaction_is_byte_stable_except_versioned_anchor_and_bundle(tmp_path):
    bundle = tmp_path / "success"
    generated = asb.generate_transaction(VALID, bundle, ROOT)
    for relative, digest in SUCCESS_STABLE_HASHES.items():
        assert asb.sha_file(bundle / relative) == digest
    for stage, digest in SUCCESS_HISTORICAL_ANCHOR_HASHES.items():
        anchor = load(bundle / f"anchors/{stage}.anchor.json")
        anchor["anchor_schema"] = "ev4-stage-anchor@1.3.0"
        assert asb.sha_bytes(asb.canonical_bytes(anchor)) == digest
    projected = compatibility_projection(
        generated["manifest"], SUCCESS_HISTORICAL_ANCHOR_HASHES
    )
    assert asb.sha_bytes(asb.canonical_bytes(projected)) == (
        "268bea566e000364d342b2945e678c24277f4817313b967fcabd154c47820fd5"
    )


def test_existing_failure_transaction_is_byte_stable_except_versioned_anchor_and_bundle(tmp_path):
    bundle = tmp_path / "failure"
    generated = asb.generate_transaction(FAILURE, bundle, ROOT)
    stable = {
        "artifacts/decompose.json": "4d4e049c23ea77bbe0c3d100d486cc14e037fe366b0f7aec2162f8471c6975e2",
        "artifacts/architectures.json": "2c1b6ec04dcf07dbb19e1c4dc9a9afd66c17bb7c7f330bee3369e1f7972c0650",
        "receipts/decompose.receipt.json": "37fb25f38dcd09e77c409eec60dc06591e910830d072f8b3e1db163cd96f9394",
        "receipts/architectures.receipt.json": "e89401bdad97ab2f4aa5b107b79cb247aecfb65d9359e6a601676db0f12d08e7",
        "failure-event.json": "775a75c0c5fd37452335af5764aefe59a78d159615a294e3c33465fb6e4a6763",
        "boundaries/repair.boundary.json": "c80bfbe98d7fc6c4edb617516c3bfbf41f1f6ee75b01eba8e2bdf9112e3146c8",
    }
    for relative, digest in stable.items():
        assert asb.sha_file(bundle / relative) == digest
    repair = load(bundle / "anchors/repair.anchor.json")
    repair["anchor_schema"] = "ev4-stage-anchor@1.3.0"
    historical_repair_hash = "d5791e1d046714a2c7b5d62d35c56d603621e793fb105137869d73b263bd2a9b"
    assert asb.sha_bytes(asb.canonical_bytes(repair)) == historical_repair_hash
    projected = compatibility_projection(
        generated["manifest"], {"repair": historical_repair_hash}
    )
    assert asb.sha_bytes(asb.canonical_bytes(projected)) == (
        "217224e6d06e1328184f915a609b972034a6a8728252e738a3180fb2a9b58a7f"
    )


def test_registry_schema_handlers_generators_and_legacy_table_drift_check():
    assert profile_check.validate(ROOT) == []
    consumers = list((ROOT / "scripts").glob("architect_validation_*.py"))
    consumers.append(ROOT / "scripts/check-architect-bootstrap.py")
    for path in consumers:
        source = path.read_text(encoding="utf-8")
        for legacy in [
            "STAGE_ORDER =",
            "NEXT_STAGE =",
            "PREDECESSOR =",
            "STAGE_VERSIONS =",
            "EXPECTED_INITIAL_SEQUENCE =",
            "EXPECTED_FINAL_STAGE =",
        ]:
            assert legacy not in source
