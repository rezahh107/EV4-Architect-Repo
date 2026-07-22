from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "scripts" / "architect_quality_runtime.py"
CHECK_PATH = REPO_ROOT / "scripts" / "check-architect-quality-runtime.py"
FIXTURE_PATH = REPO_ROOT / "fixtures" / "architect-quality-runtime" / "valid" / "full-pipeline.json"

runtime_spec = importlib.util.spec_from_file_location("architect_quality_runtime", RUNTIME_PATH)
assert runtime_spec and runtime_spec.loader
runtime = importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime)

check_spec = importlib.util.spec_from_file_location("check_architect_quality_runtime", CHECK_PATH)
assert check_spec and check_spec.loader
checker = importlib.util.module_from_spec(check_spec)
check_spec.loader.exec_module(checker)


def outputs() -> list[dict]:
    return checker.load_outputs(FIXTURE_PATH, REPO_ROOT)


def evaluate_prefix(items: list[dict], count: int):
    state = runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
    results = []
    for output in items[:count]:
        result, state = runtime.evaluate_stage(output["stage_id"], output, state, root=REPO_ROOT)
        results.append(result)
        assert result["stage_status"] == "pass", result["blocking_issues"]
    return results, state


def test_full_pipeline_is_evaluator_derived_and_passes() -> None:
    outcome = runtime.evaluate_run(outputs(), root=REPO_ROOT)
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["all_required_stages_visited"] is True
    assert all(item["evaluated_stage_output_digest"].startswith("sha256:") for item in outcome["results"])
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["source_payload_digest"].startswith("sha256:")
    assert terminal["export_digest"].startswith("sha256:")
    assert terminal["legacy_export_substituted"] is False


def test_serialized_stage_result_is_informational_only() -> None:
    results, _ = evaluate_prefix(outputs(), 1)
    errors = runtime.validate_stage_result(results[0], root=REPO_ROOT)
    assert any("informational only" in error for error in errors)


@pytest.mark.parametrize("field", ["status", "stage_status", "checks", "quality_checks", "next_stage", "build_tree_digest"])
def test_caller_authority_fields_cannot_grant_pass(field: str) -> None:
    item = outputs()[0]
    item[field] = "pass"
    result, _ = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
    )
    assert result["stage_status"] == "blocked"
    assert any(issue["issue_id"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN" for issue in result["blocking_issues"])


def test_unknown_and_missing_stage_checks_fail_closed() -> None:
    item = outputs()[0]
    item["check_evidence"]["anything"] = {"result": "pass", "reason": "Invented check."}
    item["check_evidence"].pop("required_input_captured")
    result, _ = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
    )
    ids = {issue["issue_id"] for issue in result["blocking_issues"]}
    assert "RUNTIME_UNKNOWN_CHECK" in ids
    assert "RUNTIME_REQUIRED_CHECK_MISSING" in ids


def test_no_platform_question_is_valid_research_noop() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 1)
    result, _ = runtime.evaluate_stage("/research", items[1], state, root=REPO_ROOT)
    assert result["stage_status"] == "pass"
    assert result["research_disposition"] == "no_platform_question"


def test_active_unknown_is_preserved_without_repetition() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 1)
    assert state["unknown_ledger"][0]["status"] == "active"
    result, next_state = runtime.evaluate_stage("/research", items[1], state, root=REPO_ROOT)
    assert result["stage_status"] == "pass"
    assert next_state["unknown_ledger"][0]["status"] == "active"


def test_unknown_resolution_requires_explicit_note() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 4)
    bad = copy.deepcopy(items[4])
    bad["unknown_resolutions"][0]["note"] = ""
    result, _ = runtime.evaluate_stage("/score-evidence", bad, state, root=REPO_ROOT)
    assert result["stage_status"] == "blocked"
    assert any(issue["issue_id"] == "RUNTIME_UNKNOWN_RESOLUTION_INVALID" for issue in result["blocking_issues"])


def test_downstream_critical_unknown_rejects_arbitrary_evidence() -> None:
    items = outputs()
    items[0]["unknown_introductions"][0]["downstream_critical"] = True
    _, state = evaluate_prefix(items, 4)
    bad = copy.deepcopy(items[4])
    bad["unknown_resolutions"][0]["evidence_ref"] = "arbitrary-string"
    result, _ = runtime.evaluate_stage("/score-evidence", bad, state, root=REPO_ROOT)
    assert result["stage_status"] == "blocked"
    assert any(issue["issue_id"] == "RUNTIME_CRITICAL_UNKNOWN_EVIDENCE_REQUIRED" for issue in result["blocking_issues"])


def test_candidate_lock_rejects_downstream_substitution() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 7)
    bad = copy.deepcopy(items[7])
    bad["decision_input"]["selected_candidate_id"] = "ARCH-FAM-X"
    result, _ = runtime.evaluate_stage("/build-tree", bad, state, root=REPO_ROOT)
    assert result["stage_status"] == "blocked"
    assert any(issue["issue_id"] == "RUNTIME_CANDIDATE_DRIFT" for issue in result["blocking_issues"])


def test_build_tree_digest_is_computed_from_real_content() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 7)
    result, _ = runtime.evaluate_stage("/build-tree", items[7], state, root=REPO_ROOT)
    assert result["decision_state"]["build_tree_digest"] == runtime._digest(items[7]["canonical_content"])


def test_implementation_null_or_fabricated_fidelity_cannot_pass() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 8)
    bad = copy.deepcopy(items[8])
    bad["canonical_content"].pop("approved_build_tree")
    bad["implementation_tree_digest"] = "sha256:" + "a" * 64
    result, _ = runtime.evaluate_stage("/implementation", bad, state, root=REPO_ROOT)
    ids = {issue["issue_id"] for issue in result["blocking_issues"]}
    assert result["stage_status"] == "blocked"
    assert "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN" in ids
    assert "RUNTIME_APPROVED_TREE_CONTENT_REQUIRED" in ids


def test_project_gate_boolean_without_payload_cannot_pass() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 11)
    bad = copy.deepcopy(items[11])
    bad.pop("project_gate_payload")
    bad["canonical_payload_valid"] = True
    bad["legacy_export_substituted"] = False
    result, _ = runtime.evaluate_stage("/project-gate-export", bad, state, root=REPO_ROOT)
    assert result["stage_status"] == "blocked"
    assert result["project_gate_export"] is None


def test_project_gate_candidate_mismatch_rejected() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 11)
    bad = copy.deepcopy(items[11])
    bad["project_gate_payload"]["architecture_identity"]["selected_candidate_id"] = "OTHER"
    result, _ = runtime.evaluate_stage("/project-gate-export", bad, state, root=REPO_ROOT)
    assert result["stage_status"] == "blocked"
    assert any(issue["issue_id"] == "RUNTIME_PROJECT_GATE_CANDIDATE_MISMATCH" for issue in result["blocking_issues"])


def test_partial_rerun_reactivates_unknown_and_invalidates_lock() -> None:
    outcome = runtime.evaluate_run(outputs(), root=REPO_ROOT)
    rerun = runtime.apply_partial_rerun(outcome["run_state"], "/score-evidence", root=REPO_ROOT)
    assert "U-mobile-behavior" in rerun["reactivated_unknowns"]
    assert rerun["candidate_lock_invalidated"] is True
    assert rerun["preserved_state"]["selected_candidate_locked"] is False
