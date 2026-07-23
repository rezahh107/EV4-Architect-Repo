from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_conversational_stage_output as conversational
import architect_quality_runtime as runtime

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"
EXAMPLES_DIR = REPO_ROOT / "examples/conversational-stage-output"


def prefinal_outputs() -> list[dict]:
    return conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT)


def terminal_output() -> dict:
    return json.loads(TERMINAL_PATH.read_text(encoding="utf-8"))


def trusted_context() -> dict:
    sha = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return {
        "producer_provenance": {
            "repository": "rezahh107/EV4-Architect-Repo",
            "ref": "exact-head-conversational-stage-output-test",
            "commit_sha": sha,
        }
    }


def evaluate_prefix(items: list[dict], count: int):
    state = runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
    results = []
    for output in items[:count]:
        result, state = runtime.evaluate_stage(output["stage_id"], output, state, root=REPO_ROOT)
        results.append(result)
        assert result["stage_status"] == "pass", result["blocking_issues"]
    return results, state


def test_contract_and_base_schema_identity_and_scope() -> None:
    _, schema = conversational.load_authority(REPO_ROOT)
    assert conversational.CONTRACT_ID == "ev4-architect-conversational-stage-output@1.0.0"
    assert schema["$id"] == "ev4-architect-conversational-stage-output-base@1.0.0"
    assert "forbidden_authority_fields" not in json.dumps(schema)
    sample = copy.deepcopy(prefinal_outputs()[0])
    sample["stage_specific_extension"] = {"allowed": True}
    assert conversational.validate_base_structure(sample, root=REPO_ROOT) == []


def test_base_schema_rejects_missing_type_and_caller_authority() -> None:
    sample = copy.deepcopy(prefinal_outputs()[0])
    sample.pop("run_id")
    sample["unknown_introductions"] = {}
    sample["stage_status"] = "pass"
    errors = conversational.validate_base_structure(sample, root=REPO_ROOT)
    assert any("run_id" in error for error in errors)
    assert any("unknown_introductions" in error for error in errors)
    assert any("not valid" in error or "should not" in error or "must not" in error for error in errors)


def test_every_example_and_fixture_is_manifest_consistent() -> None:
    paths = [*EXAMPLES_DIR.glob("*.json"), *PREFINAL_DIR.glob("*.json"), TERMINAL_PATH]
    assert paths
    for path in paths:
        output = json.loads(path.read_text(encoding="utf-8"))
        assert conversational.validate_manifest_consistency(output, root=REPO_ROOT) == [], path


def test_complete_prefinal_run_passes_official_runtime() -> None:
    outcome = conversational.validate_run_outputs(prefinal_outputs(), root=REPO_ROOT, require_terminal=False)
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["stages_visited"][-1] == "/handoff-export"
    assert outcome["run_state"]["current_stage"] == "/project-gate-export"
    assert outcome["run_state"]["selected_candidate_id"] == "ARCH-FAM-C"
    assert outcome["run_state"]["selected_candidate_locked"] is True
    assert outcome["run_state"]["build_tree_digest"].startswith("sha256:")
    assert outcome["run_state"]["implementation_digest"].startswith("sha256:")


def test_terminal_fixture_passes_official_evaluator_and_exporter() -> None:
    outputs = [*prefinal_outputs(), terminal_output()]
    outcome = conversational.validate_run_outputs(
        outputs,
        root=REPO_ROOT,
        require_terminal=True,
        trusted_context=trusted_context(),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["canonical_payload_valid"] is True
    assert terminal["legacy_export_substituted"] is False
    assert terminal["source_payload_digest"].startswith("sha256:")
    assert terminal["export_digest"].startswith("sha256:")


def test_instruction_mirrors_use_one_exact_normative_block() -> None:
    paths = [
        REPO_ROOT / "contracts/ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1.md",
        REPO_ROOT / "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md",
        REPO_ROOT / "release/EV4_PROJECT_RELEASE_PACK_v1/PROJECT_INSTRUCTIONS_FINAL.md",
        REPO_ROOT / "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_STAGE_PROTOCOLS_BUNDLE.md",
    ]
    pattern = re.compile(
        r"<!-- BEGIN ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->(.*?)<!-- END ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->",
        re.DOTALL,
    )
    blocks = []
    for path in paths:
        match = pattern.search(path.read_text(encoding="utf-8"))
        assert match, path
        blocks.append(match.group(1).strip())
    assert len(set(blocks)) == 1
    block = blocks[0]
    assert "no attachment was created" in block
    assert "model_authored_stage_output_only" in block
    assert "base Schema `ev4-architect-conversational-stage-output-base@1.0.0`" in block


def test_missing_stage_wrong_order_wrong_version_and_run_id_mismatch_fail() -> None:
    items = prefinal_outputs()
    missing = copy.deepcopy(items)
    missing.pop(3)
    assert conversational.validate_run_outputs(missing, root=REPO_ROOT)["status"] == "invalid"

    wrong_order = copy.deepcopy(items)
    wrong_order[1], wrong_order[2] = wrong_order[2], wrong_order[1]
    assert conversational.validate_run_outputs(wrong_order, root=REPO_ROOT)["status"] == "invalid"

    wrong_version = copy.deepcopy(items[0])
    wrong_version["stage_version"] = "9.9.9"
    assert any("stage_version" in error for error in conversational.validate_manifest_consistency(wrong_version, root=REPO_ROOT))

    mismatched_run = copy.deepcopy(items)
    mismatched_run[4]["run_id"] = "another-run"
    assert conversational.validate_run_outputs(mismatched_run, root=REPO_ROOT)["status"] == "invalid"


def test_missing_unknown_and_invalid_checks_fail_closed() -> None:
    item = copy.deepcopy(prefinal_outputs()[0])
    item["check_evidence"].pop("required_input_captured")
    item["check_evidence"]["cross_stage_check"] = {"result": "pass", "reason": "Invalid."}
    errors = conversational.validate_manifest_consistency(item, root=REPO_ROOT)
    assert any("missing Manifest checks" in error for error in errors)
    assert any("unknown or cross-Stage" in error for error in errors)

    invalid = copy.deepcopy(prefinal_outputs()[0])
    invalid["check_evidence"]["required_input_captured"] = {"result": "pass", "reason": ""}
    assert conversational.validate_base_structure(invalid, root=REPO_ROOT)


def test_forbidden_not_applicable_and_caller_authority_are_rejected() -> None:
    item = copy.deepcopy(prefinal_outputs()[0])
    item["check_evidence"]["required_input_captured"]["result"] = "not_applicable"
    result, _ = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
    )
    assert any(issue["issue_id"] == "RUNTIME_NOT_APPLICABLE_FORBIDDEN" for issue in result["blocking_issues"])

    authority = copy.deepcopy(prefinal_outputs()[0])
    authority["next_stage"] = "/research"
    assert conversational.validate_base_structure(authority, root=REPO_ROOT)
    result, _ = runtime.evaluate_stage(
        "/intake",
        authority,
        runtime.initial_run_state(authority["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
    )
    assert any(issue["issue_id"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN" for issue in result["blocking_issues"])


def test_candidate_and_build_implementation_mutations_use_runtime_outcomes() -> None:
    items = prefinal_outputs()
    _, state = evaluate_prefix(items, 7)
    drift = copy.deepcopy(items[7])
    drift["decision_input"]["selected_candidate_id"] = "ARCH-FAM-X"
    result, _ = runtime.evaluate_stage("/build-tree", drift, state, root=REPO_ROOT)
    assert any(issue["issue_id"] == "RUNTIME_CANDIDATE_DRIFT" for issue in result["blocking_issues"])

    missing_tree = copy.deepcopy(items[7])
    missing_tree.pop("canonical_content")
    result, _ = runtime.evaluate_stage("/build-tree", missing_tree, state, root=REPO_ROOT)
    assert any(issue["issue_id"] == "RUNTIME_BUILD_TREE_CONTENT_REQUIRED" for issue in result["blocking_issues"])

    _, implementation_state = evaluate_prefix(items, 8)
    missing_approved = copy.deepcopy(items[8])
    missing_approved["canonical_content"].pop("approved_build_tree")
    result, _ = runtime.evaluate_stage("/implementation", missing_approved, implementation_state, root=REPO_ROOT)
    assert any(issue["issue_id"] == "RUNTIME_APPROVED_TREE_CONTENT_REQUIRED" for issue in result["blocking_issues"])

    mismatch = copy.deepcopy(items[8])
    mismatch["canonical_content"]["approved_build_tree"]["root"] = "other-root"
    result, _ = runtime.evaluate_stage("/implementation", mismatch, implementation_state, root=REPO_ROOT)
    assert any(issue["issue_id"] == "RUNTIME_IMPLEMENTATION_FIDELITY_FAILED" for issue in result["blocking_issues"])


def test_unknown_lifecycle_mutations_fail_closed_or_persist() -> None:
    items = prefinal_outputs()
    invalid_intro = copy.deepcopy(items[0])
    invalid_intro["unknown_introductions"] = [{"unknown_id": "", "statement": "Missing identity.", "downstream_critical": False}]
    result, _ = runtime.evaluate_stage(
        "/intake",
        invalid_intro,
        runtime.initial_run_state(invalid_intro["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
    )
    assert any(issue["issue_id"] == "RUNTIME_UNKNOWN_INTRODUCTION_INVALID" for issue in result["blocking_issues"])

    with_unknown = copy.deepcopy(items)
    with_unknown[0]["unknown_introductions"] = [{"unknown_id": "U-TEST", "statement": "Needs resolution.", "downstream_critical": False}]
    _, state = evaluate_prefix(with_unknown, 1)
    result, next_state = runtime.evaluate_stage("/research", with_unknown[1], state, root=REPO_ROOT)
    assert result["stage_status"] == "pass"
    assert next_state["unknown_ledger"][0]["status"] == "active"

    _, state = evaluate_prefix(with_unknown, 4)
    invalid_resolution = copy.deepcopy(with_unknown[4])
    invalid_resolution["unknown_resolutions"] = [{"unknown_id": "U-TEST", "resolution_type": "invalid", "note": "Not supported."}]
    result, _ = runtime.evaluate_stage("/score-evidence", invalid_resolution, state, root=REPO_ROOT)
    assert any(issue["issue_id"] == "RUNTIME_UNKNOWN_RESOLUTION_INVALID" for issue in result["blocking_issues"])


def test_active_critical_unknown_and_high_final_audit_finding_block_handoff() -> None:
    items = prefinal_outputs()
    critical = copy.deepcopy(items)
    critical[0]["unknown_introductions"] = [{"unknown_id": "U-CRITICAL", "statement": "Required evidence is missing.", "downstream_critical": True}]
    _, state = evaluate_prefix(critical, 9)
    result, _ = runtime.evaluate_stage("/final-audit", critical[9], state, root=REPO_ROOT)
    assert any(issue["issue_id"] == "RUNTIME_CRITICAL_UNKNOWN_ACTIVE" for issue in result["blocking_issues"])

    _, state = evaluate_prefix(items, 9)
    high = copy.deepcopy(items[9])
    high["final_audit_findings"] = [{"finding_id": "F-HIGH", "severity": "high", "reason": "Material architecture drift."}]
    result, _ = runtime.evaluate_stage("/final-audit", high, state, root=REPO_ROOT)
    assert any(issue["issue_id"] == "RUNTIME_FINAL_AUDIT_SEVERE" for issue in result["blocking_issues"])


def test_terminal_missing_payload_and_candidate_mismatch_are_rejected() -> None:
    items = prefinal_outputs()
    _, state = evaluate_prefix(items, 11)

    missing = terminal_output()
    missing.pop("project_gate_payload")
    result, _ = runtime.evaluate_stage("/project-gate-export", missing, state, root=REPO_ROOT, trusted_context=trusted_context())
    assert any(issue["issue_id"] == "RUNTIME_PROJECT_GATE_PAYLOAD_REQUIRED" for issue in result["blocking_issues"])

    mismatch = terminal_output()
    mismatch["project_gate_payload"]["architecture_identity"]["selected_candidate_id"] = "OTHER"
    result, _ = runtime.evaluate_stage("/project-gate-export", mismatch, state, root=REPO_ROOT, trusted_context=trusted_context())
    assert any(issue["issue_id"] == "RUNTIME_PROJECT_GATE_CANDIDATE_MISMATCH" for issue in result["blocking_issues"])


@pytest.mark.parametrize("field", ["status", "stage_status", "checks", "quality_checks", "next_stage", "canonical_payload_valid", "legacy_export_substituted", "build_tree_digest", "implementation_digest", "implementation_tree_digest", "continuation_authorized", "official_pass", "official_digest"])
def test_every_conversational_authority_alias_is_forbidden(field: str) -> None:
    item = copy.deepcopy(prefinal_outputs()[0])
    item[field] = True
    assert conversational.validate_base_structure(item, root=REPO_ROOT)
