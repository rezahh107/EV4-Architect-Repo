from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "architect_quality_runtime.py"
FIXTURE_PATH = REPO_ROOT / "fixtures" / "architect-quality-runtime" / "valid" / "full-pipeline.json"

spec = importlib.util.spec_from_file_location("architect_quality_runtime", MODULE_PATH)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def fixture() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def by_stage(results: list[dict], stage_id: str) -> dict:
    return next(item for item in results if item["stage_id"] == stage_id)


def assert_invalid(results: list[dict], expected: str) -> None:
    outcome = runtime.validate_run(results, root=REPO_ROOT)
    assert outcome["status"] == "invalid"
    assert any(expected in error for error in outcome["errors"]), outcome["errors"]


def test_full_pipeline_without_internal_authorization_evidence_passes() -> None:
    results = fixture()
    outcome = runtime.validate_run(results, root=REPO_ROOT)
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["all_required_stages_visited"] is True
    assert all(item["runtime_context"]["anchor_present"] is False for item in results)
    assert all(item["runtime_context"]["validation_bundle_present"] is False for item in results)
    assert all(item["runtime_context"]["independent_regeneration_executed"] is False for item in results)
    assert all(item["runtime_context"]["exact_head_ci_available"] is False for item in results)
    assert all(item["runtime_context"]["pr_review_available"] is False for item in results)
    assert all(item["runtime_context"]["repository_maintenance_required"] is False for item in results)
    assert by_stage(results, "/recommend")["decision_state"]["selected_candidate_id"] == "A07"
    assert by_stage(results, "/implementation")["decision_state"]["implementation_tree_digest"] == by_stage(results, "/build-tree")["decision_state"]["build_tree_digest"]
    assert by_stage(results, "/project-gate-export")["project_gate_export"]["legacy_export_substituted"] is False


def test_intake_without_blocker_continues() -> None:
    assert runtime.validate_stage_result(fixture()[0], root=REPO_ROOT) == []


def test_intake_architecture_changing_uncertainty_needs_input() -> None:
    result = fixture()[0]
    result["stage_status"] = "needs_input"
    result["next_stage"] = None
    result["blocking_issues"] = [{"issue_id":"INTAKE_MOBILE_ARCHITECTURE_DECISION","reason":"Mobile behavior changes the architecture.","repair_stage":"/intake"}]
    assert runtime.validate_stage_result(result, root=REPO_ROOT) == []


@pytest.mark.parametrize("disposition", ["active_lookup_required", "existing_evidence_sufficient", "no_platform_question"])
def test_nonblocking_research_dispositions_continue(disposition: str) -> None:
    result = fixture()[1]
    result["research_disposition"] = disposition
    assert runtime.validate_stage_result(result, root=REPO_ROOT) == []


def test_research_missing_required_source_blocks_truthfully() -> None:
    result = fixture()[1]
    result["research_disposition"] = "blocked_by_missing_required_source"
    result["stage_status"] = "blocked"
    result["next_stage"] = None
    result["blocking_issues"] = [{"issue_id":"RESEARCH_REQUIRED_SOURCE_UNAVAILABLE","reason":"A version-sensitive capability decision lacks an obtainable authoritative source.","repair_stage":"/research"}]
    assert runtime.validate_stage_result(result, root=REPO_ROOT) == []


def test_skip_mandatory_stage_rejected() -> None:
    results = fixture(); results.pop(1)
    assert_invalid(results, "mandatory Stage order mismatch")


def test_intake_direct_to_architectures_rejected() -> None:
    results = fixture(); results[0]["next_stage"] = "/architectures"
    assert_invalid(results, "exact Manifest successor")


def test_recommendation_during_intake_rejected() -> None:
    results = fixture(); by_stage(results, "/intake")["decision_state"]["recommendation_made"] = True
    assert_invalid(results, "recommendation is premature")


def test_implementation_selection_during_decompose_rejected() -> None:
    results = fixture(); by_stage(results, "/decompose")["decision_state"]["implementation_tree_digest"] = "sha256:" + "b" * 64
    assert_invalid(results, "implementation selection is premature")


def test_hidden_recommendation_during_score_evidence_rejected() -> None:
    results = fixture(); by_stage(results, "/score-evidence")["decision_state"]["hidden_recommendation"] = True
    assert_invalid(results, "hidden recommendation is forbidden")


def test_recommendation_before_accepted_score_audit_rejected() -> None:
    results = fixture()
    audit = by_stage(results, "/score-audit")
    audit["quality_checks"]["score_audit_acceptance"] = "fail"
    audit["stage_status"] = "blocked"; audit["next_stage"] = None
    audit["blocking_issues"] = [{"issue_id":"SCORE_AUDIT_FAILED","reason":"Audit found unresolved scoring defects.","repair_stage":"/score-evidence"}]
    assert_invalid(results, "accepted /score-audit is required")


def test_unknown_converted_to_exact_rejected() -> None:
    results = fixture(); by_stage(results, "/score-evidence")["decision_state"]["unknown_converted_to_exact"] = True
    assert_invalid(results, "unknown evidence cannot become an exact value")


def test_selected_candidate_drift_after_lock_rejected() -> None:
    results = fixture(); by_stage(results, "/build-tree")["decision_state"]["selected_candidate_id"] = "A02"
    assert_invalid(results, "selected_candidate_id changed after lock")


def test_rearchitecture_during_build_tree_rejected() -> None:
    results = fixture(); by_stage(results, "/build-tree")["decision_state"]["architecture_drift"] = True
    assert_invalid(results, "architecture drift is forbidden")


def test_implementation_tree_mismatch_rejected() -> None:
    results = fixture(); by_stage(results, "/implementation")["decision_state"]["implementation_tree_digest"] = "sha256:" + "c" * 64
    assert_invalid(results, "implementation must preserve the approved tree")


def test_silent_unknown_removal_rejected() -> None:
    results = fixture(); by_stage(results, "/research")["carried_unknowns"] = []
    assert_invalid(results, "disappeared without explicit resolution")


def test_handoff_with_high_final_audit_finding_rejected() -> None:
    results = fixture(); final = by_stage(results, "/final-audit")
    final["final_audit_findings"] = [{"finding_id":"FA-HIGH-001","severity":"high","reason":"Implementation drift remains."}]
    assert_invalid(results, "blocker or high-severity findings prevent pass")


def test_invalid_final_payload_rejected() -> None:
    results = fixture(); by_stage(results, "/project-gate-export")["project_gate_export"]["canonical_payload_valid"] = False
    assert_invalid(results, "canonical Architect payload must validate")


def test_legacy_builder_feed_substitution_rejected() -> None:
    results = fixture(); by_stage(results, "/project-gate-export")["project_gate_export"]["legacy_export_substituted"] = True
    assert_invalid(results, "legacy export substitution is forbidden")


def test_non_successor_continuation_rejected() -> None:
    results = fixture(); by_stage(results, "/architectures")["next_stage"] = "/recommend"
    assert_invalid(results, "exact Manifest successor")


@pytest.mark.parametrize("issue_id", ["ANCHOR_MISSING","VALIDATION_BUNDLE_MISSING","INDEPENDENT_REGENERATION_MISSING","VALIDATION_PROFILE_INCOMPLETE","EXACT_HEAD_CI_UNAVAILABLE","PR_REVIEW_UNAVAILABLE","REPOSITORY_MAINTENANCE_REQUIRED"])
def test_optional_audit_conditions_cannot_block_normal_run(issue_id: str) -> None:
    result = fixture()[0]
    result["stage_status"] = "blocked"; result["next_stage"] = None
    result["blocking_issues"] = [{"issue_id":issue_id,"reason":"Optional repository-audit evidence is unavailable.","repair_stage":None}]
    errors = runtime.validate_stage_result(result, root=REPO_ROOT)
    assert any("cannot block a normal Run" in error for error in errors)
