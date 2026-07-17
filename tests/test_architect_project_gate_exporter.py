from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)

BASE_FIXTURE = ROOT / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json"
CASE_MANIFEST = ROOT / "fixtures/architect-project-gate-export/cases.v1.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def complete_unit_payload() -> dict:
    payload = load_json(BASE_FIXTURE)
    payload["synthetic"] = False
    payload["payload_identity"]["synthetic_fixture_notice"] = "Unit-only non-production vector for exporter behavior; not real-run evidence."
    for item in payload["evidence_register"]:
        item["claim"] = item["claim"].replace("synthetic", "unit vector")
        if isinstance(item.get("source_ref"), dict):
            item["source_ref"]["reference"] = item["source_ref"]["reference"].replace("synthetic", "unit-vector")
    return payload


def provenance() -> exporter.GitProvenance:
    return exporter.GitProvenance(
        repository=exporter.REPOSITORY,
        ref="feature/architect-project-gate-exporter",
        commit_sha="a" * 40,
    )


def apply_mutations(value: dict, mutations: list[dict]) -> dict:
    result = copy.deepcopy(value)
    for mutation in mutations:
        cursor = result
        tokens = mutation["path"].split(".")
        for token in tokens[:-1]:
            cursor = cursor[int(token)] if token.isdigit() else cursor[token]
        last = tokens[-1]
        if mutation["op"] == "set":
            if last.isdigit():
                cursor[int(last)] = mutation["value"]
            else:
                cursor[last] = mutation["value"]
        elif mutation["op"] == "delete":
            if last.isdigit():
                del cursor[int(last)]
            else:
                del cursor[last]
        else:
            raise AssertionError(f"unsupported mutation: {mutation['op']}")
    return result


def init_repo(path: Path, remote: str = "https://github.com/rezahh107/EV4-Architect-Repo.git") -> str:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "ARCH-01 Tests"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "arch01@example.invalid"], check=True)
    (path / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "test fixture"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "remote", "add", "origin", remote], check=True)
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_case_manifest_is_explicitly_synthetic():
    manifest = load_json(CASE_MANIFEST)
    assert manifest["classification"] == "synthetic_test_vectors_only"
    assert manifest["real_run_evidence"] is False
    assert {case["case_id"] for case in manifest["cases"]} >= {
        "complete-nonsynthetic-unit-vector",
        "synthetic-blocked",
        "insufficient-evidence-blocked",
        "invalid-evidence-reference",
    }


def test_official_payload_validator_accepts_complete_unit_vector():
    result = exporter.validate_payload(ROOT, complete_unit_payload())
    assert result["status"] == "valid"


def test_allowed_export_uses_active_contracts_and_exact_provenance():
    export, hashes = exporter.build_export(
        complete_unit_payload(), provenance(), "run-001", "payload.json"
    )
    exporter.validate_contracts(ROOT, export)
    exporter.verify_hashes(export, hashes)
    assert export["schema_version"] == "producer-gate-export.v1"
    assert export["final_stage_bundle"]["schema_version"] == "stage-evidence-bundle.v1"
    assert export["final_stage_bundle"]["payload_schema"]["id"] == "ev4-architect-stage-payload@1.0.0"
    assert export["producer"]["repository"] == exporter.REPOSITORY
    assert export["producer"]["commit_sha"] == "a" * 40
    assert export["handoff"] == {
        "target": "ce-intake",
        "status": "successful_with_flags",
        "allowed": True,
        "failure_reasons": [],
        "blocking_diagnostics": [],
        "unresolved_evidence": complete_unit_payload()["unresolved_evidence"],
    }
    assert export["acquisition_mode"]["silent_fallback_allowed"] is False
    assert hashes["payload_hash"] == exporter.digest(complete_unit_payload())


def test_repeat_export_same_run_is_byte_stable():
    payload = complete_unit_payload()
    first, first_hashes = exporter.build_export(payload, provenance(), "run-repeat", "payload.json")
    second, second_hashes = exporter.build_export(payload, provenance(), "run-repeat", "payload.json")
    assert exporter.canonical_bytes(first) == exporter.canonical_bytes(second)
    assert first_hashes == second_hashes


def test_different_run_id_changes_bundle_and_export_identity():
    payload = complete_unit_payload()
    first, first_hashes = exporter.build_export(payload, provenance(), "run-a", "payload.json")
    second, second_hashes = exporter.build_export(payload, provenance(), "run-b", "payload.json")
    assert first["final_stage_bundle"]["payload"]["data"] == second["final_stage_bundle"]["payload"]["data"]
    assert first["final_stage_bundle"]["bundle_id"] != second["final_stage_bundle"]["bundle_id"]
    assert first["export_id"] != second["export_id"]
    assert first_hashes["payload_hash"] == second_hashes["payload_hash"]
    assert first_hashes["bundle_hash"] != second_hashes["bundle_hash"]
    assert first_hashes["export_hash"] != second_hashes["export_hash"]


def test_synthetic_payload_produces_valid_blocked_export():
    payload = load_json(BASE_FIXTURE)
    export, hashes = exporter.build_export(payload, provenance(), "synthetic-run", "payload.json")
    exporter.validate_contracts(ROOT, export)
    exporter.verify_hashes(export, hashes)
    assert export["handoff"]["allowed"] is False
    assert export["handoff"]["status"] == "blocked"
    assert export["stage_manifest"][0]["status"] == "blocked"
    assert "ARCH_EXPORT_SYNTHETIC_HANDOFF_FORBIDDEN" in {
        item["code"] for item in export["handoff"]["blocking_diagnostics"]
    }


def test_insufficient_evidence_produces_valid_blocked_export():
    payload = complete_unit_payload()
    payload["payload_status"] = "insufficient_evidence"
    payload["unresolved_evidence"] = [
        {
            "unresolved_id": "missing-project-gate-evidence",
            "state": "insufficient_evidence",
            "owner": "architect",
            "reason": "Required Architect evidence is missing.",
            "blocks": ["architect_stage_payload_acceptance", "ce_transition"],
            "required_before": "project_gate_acceptance",
            "evidence_refs": ["ev-rec"],
        }
    ]
    result = exporter.validate_payload(ROOT, payload)
    assert result["status"] == "insufficient_evidence"
    export, hashes = exporter.build_export(payload, provenance(), "blocked-run", "payload.json")
    exporter.validate_contracts(ROOT, export)
    exporter.verify_hashes(export, hashes)
    assert export["handoff"]["allowed"] is False
    assert export["handoff"]["status"] == "insufficient_evidence"
    assert export["final_stage_bundle"]["evidence_status"] == "insufficient_evidence"
    assert export["final_stage_bundle"]["missing_evidence"][0]["id"] == "missing-project-gate-evidence"


def test_transition_blocking_unknown_cannot_be_accepted_even_when_payload_complete():
    payload = complete_unit_payload()
    payload["unresolved_evidence"].append(
        {
            "unresolved_id": "ce-transition-blocker",
            "state": "insufficient_evidence",
            "owner": "architect",
            "reason": "Architect handoff proof is incomplete.",
            "blocks": ["ce_transition"],
            "required_before": "ce_transition",
            "evidence_refs": ["ev-rec"],
        }
    )
    exporter.validate_payload(ROOT, payload)
    export, _ = exporter.build_export(payload, provenance(), "blocked-complete", "payload.json")
    assert export["handoff"]["allowed"] is False
    assert export["handoff"]["status"] == "blocked"


def test_invalid_evidence_reference_is_rejected_by_official_validator():
    payload = complete_unit_payload()
    payload["kernel_decision_records"][0]["evidence_refs"] = ["not-present"]
    with pytest.raises(exporter.ExportError) as exc:
        exporter.validate_payload(ROOT, payload)
    assert exc.value.code == "ARCH_EXPORT_ARCHITECT_PAYLOAD_INVALID"
    assert "ARCH-KERNEL-DECISION-004" in exc.value.reason


def test_missing_required_payload_field_is_rejected():
    payload = complete_unit_payload()
    del payload["architecture_identity"]
    with pytest.raises(exporter.ExportError) as exc:
        exporter.validate_payload(ROOT, payload)
    assert exc.value.code == "ARCH_EXPORT_ARCHITECT_PAYLOAD_INVALID"


def test_strict_json_rejects_duplicate_keys(tmp_path: Path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_id":"a","schema_id":"b"}', encoding="utf-8")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.load_json(path)
    assert exc.value.code == "ARCH_EXPORT_MALFORMED_JSON"


def test_strict_json_rejects_non_finite_numbers(tmp_path: Path):
    path = tmp_path / "nan.json"
    path.write_text('{"value":NaN}', encoding="utf-8")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.load_json(path)
    assert exc.value.code == "ARCH_EXPORT_MALFORMED_JSON"


def test_canonicalization_preserves_unicode_and_rejects_non_finite():
    first = exporter.canonical_bytes({"z": "معماری", "a": 1})
    second = exporter.canonical_bytes({"a": 1, "z": "معماری"})
    assert first == second
    assert "معماری".encode("utf-8") in first
    with pytest.raises(exporter.ExportError) as exc:
        exporter.canonical_bytes({"bad": float("inf")})
    assert exc.value.code == "ARCH_EXPORT_NON_FINITE_NUMBER"


def test_tampered_bundle_is_rejected():
    export, hashes = exporter.build_export(complete_unit_payload(), provenance(), "tamper", "payload.json")
    export["final_stage_bundle"]["payload"]["data"]["architecture_identity"]["architecture_family"] = "tampered"
    with pytest.raises(exporter.ExportError) as exc:
        exporter.verify_hashes(export, hashes)
    assert exc.value.code == "ARCH_EXPORT_HASH_SELF_VERIFICATION_FAILED"


def test_tampered_stage_bundle_hash_is_rejected():
    export, hashes = exporter.build_export(complete_unit_payload(), provenance(), "tamper-stage", "payload.json")
    export["stage_manifest"][0]["output"]["artifact_hash"]["value"] = "0" * 64
    hashes = dict(hashes)
    hashes["export_hash"] = exporter.digest(export)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.verify_hashes(export, hashes)
    assert exc.value.code == "ARCH_EXPORT_BUNDLE_HASH_MISMATCH"


def test_atomic_write_refuses_overwrite_and_roundtrips(tmp_path: Path):
    output = tmp_path / "architect-project-gate.json"
    export, hashes = exporter.build_export(complete_unit_payload(), provenance(), "atomic", "payload.json")
    exporter.atomic_write(output, export, overwrite=False)
    reread = exporter.load_json(output)
    exporter.verify_hashes(reread, hashes)
    assert output.read_bytes().endswith(b"\n")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, export, overwrite=False)
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_EXISTS"


def test_output_path_must_remain_inside_repository(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inside(repo, tmp_path / "outside.json")
    assert exc.value.code == "ARCH_EXPORT_UNSAFE_OUTPUT_PATH"


def test_git_provenance_accepts_clean_repo_and_payload_untracked(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    commit = init_repo(repo)
    payload = repo / "architect-stage-payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    observed = exporter.inspect_repository(repo, payload, repo / "architect-project-gate.json")
    assert observed.repository == exporter.REPOSITORY
    assert observed.ref == "main"
    assert observed.commit_sha == commit


def test_git_provenance_rejects_wrong_remote(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo, "https://github.com/example/wrong.git")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inspect_repository(repo, repo / "payload.json", repo / "out.json")
    assert exc.value.code == "ARCH_EXPORT_WRONG_REPOSITORY"


def test_git_provenance_rejects_dirty_tracked_file(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inspect_repository(repo, repo / "payload.json", repo / "out.json")
    assert exc.value.code == "ARCH_EXPORT_DIRTY_WORKTREE"


def test_git_provenance_rejects_unrelated_untracked_file(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    (repo / "unrelated.txt").write_text("untracked\n", encoding="utf-8")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inspect_repository(repo, repo / "payload.json", repo / "out.json")
    assert exc.value.code == "ARCH_EXPORT_DIRTY_WORKTREE"


def test_git_provenance_rejects_detached_head(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    commit = init_repo(repo)
    subprocess.run(["git", "-C", str(repo), "checkout", "--detach", commit], check=True, capture_output=True)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inspect_repository(repo, repo / "payload.json", repo / "out.json")
    assert exc.value.code == "ARCH_EXPORT_DETACHED_HEAD"


def test_git_provenance_rejects_missing_repository(tmp_path: Path):
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inspect_repository(tmp_path, tmp_path / "payload.json", tmp_path / "out.json")
    assert exc.value.code == "ARCH_EXPORT_GIT_COMMAND_FAILED"


def test_fixture_manifest_mutations_produce_expected_boundaries():
    manifest = load_json(CASE_MANIFEST)
    base = load_json((CASE_MANIFEST.parent / manifest["base_fixture"]).resolve())
    by_id = {case["case_id"]: case for case in manifest["cases"]}

    complete = apply_mutations(base, by_id["complete-nonsynthetic-unit-vector"]["mutations"])
    exporter.validate_payload(ROOT, complete)
    allowed_export, _ = exporter.build_export(complete, provenance(), "manifest-complete", "payload.json")
    assert allowed_export["handoff"]["allowed"] is True

    synthetic = apply_mutations(base, by_id["synthetic-blocked"]["mutations"])
    exporter.validate_payload(ROOT, synthetic)
    synthetic_export, _ = exporter.build_export(synthetic, provenance(), "manifest-synthetic", "payload.json")
    assert synthetic_export["handoff"]["allowed"] is False

    insufficient = apply_mutations(base, by_id["insufficient-evidence-blocked"]["mutations"])
    exporter.validate_payload(ROOT, insufficient)
    insufficient_export, _ = exporter.build_export(insufficient, provenance(), "manifest-insufficient", "payload.json")
    assert insufficient_export["handoff"]["allowed"] is False

    invalid = apply_mutations(base, by_id["invalid-evidence-reference"]["mutations"])
    with pytest.raises(exporter.ExportError):
        exporter.validate_payload(ROOT, invalid)
