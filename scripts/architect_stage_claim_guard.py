"""Deterministic Stage predicates for the single Architect Runtime.

Model-authored check claims are explanatory input only. This module derives
quality-check outcomes; the official Runtime derives completion semantics only
after the final Stage status is known.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

REASONING_COMPLETE = "reasoning_complete"
VALIDATED_PASS = "validated_pass"

DETERMINISTIC_PREDICATE = "DETERMINISTIC_PREDICATE"
STRUCTURAL_COMPLETENESS = "STRUCTURAL_COMPLETENESS"
ATTRIBUTED_REASONING_ONLY = "ATTRIBUTED_REASONING_ONLY"
EXTERNAL_BOUNDARY = "EXTERNAL_BOUNDARY"

REASONING_STAGES = frozenset(
    {"/intake", "/research", "/decompose", "/architectures", "/score-evidence"}
)

CHECK_EVALUATION_BASIS: dict[str, dict[str, str]] = {
    "/intake": {
        "required_input_captured": STRUCTURAL_COMPLETENESS,
        "architecture_not_selected": DETERMINISTIC_PREDICATE,
        "exact_values_not_invented": ATTRIBUTED_REASONING_ONLY,
    },
    "/research": {
        "research_scope_resolved": DETERMINISTIC_PREDICATE,
        "platform_project_boundary_preserved": ATTRIBUTED_REASONING_ONLY,
        "unsupported_claims_remain_unknown": ATTRIBUTED_REASONING_ONLY,
    },
    "/decompose": {
        "observation_inference_separated": STRUCTURAL_COMPLETENESS,
        "implementation_not_selected": DETERMINISTIC_PREDICATE,
        "unknowns_recorded": STRUCTURAL_COMPLETENESS,
    },
    "/architectures": {
        "architecture_coverage_complete": ATTRIBUTED_REASONING_ONLY,
        "recommendation_not_made": DETERMINISTIC_PREDICATE,
        "unknowns_propagated": DETERMINISTIC_PREDICATE,
    },
    "/score-evidence": {
        "evidence_scoring_valid": STRUCTURAL_COMPLETENESS,
        "hidden_recommendation_absent": DETERMINISTIC_PREDICATE,
        "unknowns_not_numeric": DETERMINISTIC_PREDICATE,
    },
    "/score-audit": {
        "score_audit_acceptance": DETERMINISTIC_PREDICATE,
        "rubric_integrity": DETERMINISTIC_PREDICATE,
        "unknowns_not_numeric": DETERMINISTIC_PREDICATE,
    },
    "/recommend": {
        "audited_candidate_selected": DETERMINISTIC_PREDICATE,
        "candidate_lock_established": DETERMINISTIC_PREDICATE,
    },
    "/build-tree": {
        "selected_candidate_preserved": DETERMINISTIC_PREDICATE,
        "canonical_build_tree_present": STRUCTURAL_COMPLETENESS,
        "architecture_drift_absent": DETERMINISTIC_PREDICATE,
    },
    "/implementation": {
        "selected_candidate_preserved": DETERMINISTIC_PREDICATE,
        "canonical_implementation_present": STRUCTURAL_COMPLETENESS,
        "approved_build_tree_preserved": DETERMINISTIC_PREDICATE,
    },
    "/final-audit": {
        "final_audit_acceptance": DETERMINISTIC_PREDICATE,
        "candidate_lock_preserved": DETERMINISTIC_PREDICATE,
        "implementation_fidelity_confirmed": DETERMINISTIC_PREDICATE,
    },
    "/handoff-export": {
        "handoff_eligibility": DETERMINISTIC_PREDICATE,
        "blocking_unknowns_absent": DETERMINISTIC_PREDICATE,
        "final_audit_preserved": DETERMINISTIC_PREDICATE,
    },
    "/project-gate-export": {
        "canonical_payload_valid": EXTERNAL_BOUNDARY,
        "canonical_export_valid": EXTERNAL_BOUNDARY,
        "legacy_export_not_substituted": EXTERNAL_BOUNDARY,
    },
}


@dataclass(frozen=True)
class ClaimGuardResult:
    quality_checks: dict[str, str]
    issues: tuple[dict[str, Any], ...]
    evaluation_basis: dict[str, str]
    legacy_result_fields_ignored: tuple[str, ...]


def _issue(code: str, reason: str, stage_id: str) -> dict[str, Any]:
    return {"issue_id": code, "reason": reason, "repair_stage": stage_id}


def _content(output: dict[str, Any]) -> dict[str, Any]:
    value = output.get("canonical_content")
    return value if isinstance(value, dict) else {}


def _decision(output: dict[str, Any]) -> dict[str, Any]:
    value = output.get("decision_input")
    return value if isinstance(value, dict) else {}


def _history_output(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    for item in reversed(state.get("evaluated_stage_outputs", [])):
        if isinstance(item, dict) and item.get("stage_id") == stage_id:
            return item
    return None


def _history_result(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    for item in reversed(state.get("derived_stage_results", [])):
        if isinstance(item, dict) and item.get("stage_id") == stage_id:
            return item
    return None


def _candidate_ids_from_architectures(state: dict[str, Any]) -> set[str]:
    rows = _content(_history_output(state, "/architectures") or {}).get("candidates", [])
    return {
        str(item.get("candidate_id"))
        for item in rows
        if isinstance(item, dict) and str(item.get("candidate_id", "")).strip()
    }


def _eligible_candidate_ids(state: dict[str, Any]) -> set[str]:
    values = _content(_history_output(state, "/score-audit") or {}).get("eligible_candidates", [])
    return {str(item) for item in values if isinstance(item, str) and item.strip()}


def _score_candidate_ids(state: dict[str, Any]) -> set[str]:
    rows = _content(_history_output(state, "/score-evidence") or {}).get("candidate_scores", [])
    return {
        str(item.get("candidate_id"))
        for item in rows
        if isinstance(item, dict) and str(item.get("candidate_id", "")).strip()
    }


def _active_critical_unknowns(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in state.get("unknown_ledger", [])
        if isinstance(item, dict)
        and item.get("status") == "active"
        and item.get("downstream_critical") is True
    ]


def _valid_check_claim(record: Any) -> bool:
    if not isinstance(record, dict):
        return False
    reason = record.get("reason")
    claim = record.get("claim")
    return (
        isinstance(reason, str)
        and bool(reason.strip())
        and (claim is None or isinstance(claim, str) and bool(claim.strip()))
    )


def _intake(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    if check == "required_input_captured":
        basis = content.get("input_basis")
        return isinstance(basis, dict) and any(
            isinstance(value, str) and value.strip() for value in basis.values()
        )
    if check == "architecture_not_selected":
        forbidden = {"selected_candidate_id", "architecture_family", "selected_architecture"}
        return not forbidden.intersection(content) and not decision.get("selected_candidate_id")
    if check == "exact_values_not_invented":
        return decision.get("unknown_converted_to_exact") is not True and content.get(
            "exact_values_invented"
        ) is not True
    return False


def _research(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    disposition = output.get("research_disposition")
    decision = _decision(output)
    if check == "research_scope_resolved":
        return disposition in {
            "active_lookup_completed", "existing_evidence_sufficient", "no_platform_question"
        }
    if check == "platform_project_boundary_preserved":
        return not decision.get("selected_candidate_id") and decision.get("hidden_recommendation") is not True
    if check == "unsupported_claims_remain_unknown":
        return decision.get("unknown_converted_to_exact") is not True
    return False


def _decompose(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    if check == "observation_inference_separated":
        return (
            isinstance(content.get("observations"), list)
            and bool(content.get("observations"))
            and isinstance(content.get("inferences"), list)
        )
    if check == "implementation_not_selected":
        return not decision.get("selected_candidate_id") and "implementation" not in content
    if check == "unknowns_recorded":
        return isinstance(content.get("unknowns"), list)
    return False


def _architectures(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    rows = content.get("candidates")
    valid_rows = [
        item for item in rows or []
        if isinstance(item, dict)
        and isinstance(item.get("candidate_id"), str) and item["candidate_id"].strip()
        and isinstance(item.get("family"), str) and item["family"].strip()
        and isinstance(item.get("coverage"), list) and item["coverage"]
    ]
    if check == "architecture_coverage_complete":
        ids = [item["candidate_id"] for item in valid_rows]
        return len(valid_rows) >= 2 and len(ids) == len(set(ids))
    if check == "recommendation_not_made":
        return (
            not decision.get("selected_candidate_id")
            and decision.get("hidden_recommendation") is not True
            and "selected_candidate_id" not in content
        )
    if check == "unknowns_propagated":
        return decision.get("unknown_converted_to_exact") is not True
    return False


def _score_evidence(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    rows = content.get("candidate_scores")
    architecture_ids = _candidate_ids_from_architectures(state)
    valid_states = {
        "observed", "validated", "resolved", "derived", "proposed",
        "unverified", "insufficient_evidence",
    }
    valid_rows = [
        item for item in rows or []
        if isinstance(item, dict)
        and isinstance(item.get("candidate_id"), str)
        and item.get("candidate_id") in architecture_ids
        and isinstance(item.get("coverage"), str) and item["coverage"].strip()
        and item.get("evidence_state") in valid_states
    ]
    if check == "evidence_scoring_valid":
        return bool(architecture_ids) and {item["candidate_id"] for item in valid_rows} == architecture_ids
    if check == "hidden_recommendation_absent":
        return not decision.get("selected_candidate_id") and decision.get("hidden_recommendation") is not True
    if check == "unknowns_not_numeric":
        return decision.get("unknown_converted_to_exact") is not True and all(
            not (
                item.get("evidence_state") in {"unverified", "insufficient_evidence"}
                and isinstance(item.get("score"), (int, float))
            )
            for item in rows or [] if isinstance(item, dict)
        )
    return False


def _score_audit(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    eligible = content.get("eligible_candidates")
    scored = _score_candidate_ids(state)
    eligible_set = {item for item in eligible or [] if isinstance(item, str) and item.strip()}
    defects = content.get("material_defects")
    if check == "score_audit_acceptance":
        return (
            content.get("audit_status") in {"pass", "pass_with_minor_flags"}
            and isinstance(defects, list) and not defects
            and bool(eligible_set) and eligible_set <= scored
        )
    if check == "rubric_integrity":
        return isinstance(eligible, list) and len(eligible) == len(eligible_set) and bool(scored) and eligible_set <= scored
    if check == "unknowns_not_numeric":
        return decision.get("unknown_converted_to_exact") is not True
    return False


def _recommend(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    candidate = _decision(output).get("selected_candidate_id")
    eligible = _eligible_candidate_ids(state)
    architectures = _candidate_ids_from_architectures(state)
    if check == "audited_candidate_selected":
        return isinstance(candidate, str) and candidate in eligible and candidate in architectures
    if check == "candidate_lock_established":
        return isinstance(candidate, str) and bool(candidate.strip())
    return False


def _build_tree(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    selected = state.get("selected_candidate_id")
    if check == "selected_candidate_preserved":
        return (
            bool(state.get("selected_candidate_locked"))
            and decision.get("selected_candidate_id", selected) == selected
            and content.get("candidate_id") == selected
        )
    if check == "canonical_build_tree_present":
        nodes = content.get("nodes")
        ids = {item.get("id") for item in nodes or [] if isinstance(item, dict) and isinstance(item.get("id"), str)}
        return isinstance(content.get("root"), str) and content.get("root") in ids and isinstance(nodes, list) and bool(nodes)
    if check == "architecture_drift_absent":
        return decision.get("architecture_drift") is not True
    return False


def _implementation(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    selected = state.get("selected_candidate_id")
    if check == "selected_candidate_preserved":
        return bool(state.get("selected_candidate_locked")) and decision.get("selected_candidate_id", selected) == selected
    if check == "canonical_implementation_present":
        classes = content.get("class_intent")
        class_map = content.get("class_application_map")
        element_map = content.get("element_mapping")
        return (
            isinstance(content.get("approved_build_tree"), dict)
            and isinstance(classes, list) and bool(classes)
            and isinstance(class_map, list) and bool(class_map)
            and isinstance(element_map, list) and bool(element_map)
        )
    if check == "approved_build_tree_preserved":
        digest_fn = state.get("_digest_function")
        approved = content.get("approved_build_tree")
        return (
            callable(digest_fn) and isinstance(approved, dict)
            and bool(state.get("build_tree_digest"))
            and digest_fn(approved) == state.get("build_tree_digest")
        )
    return False


def _final_audit(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    content, decision = _content(output), _decision(output)
    findings = output.get("final_audit_findings")
    severe = any(
        isinstance(item, dict) and item.get("severity") in {"blocker", "high"}
        for item in findings or []
    )
    required_scope = {"candidate_lock", "build_tree_fidelity", "implementation_fidelity", "handoff_safety"}
    if check == "final_audit_acceptance":
        return isinstance(findings, list) and not severe and required_scope <= set(content.get("audit_scope", []))
    if check == "candidate_lock_preserved":
        selected = state.get("selected_candidate_id")
        return bool(state.get("selected_candidate_locked")) and decision.get("selected_candidate_id", selected) == selected
    if check == "implementation_fidelity_confirmed":
        prior = _history_result(state, "/implementation") or {}
        return bool(state.get("implementation_digest")) and prior.get("stage_status") == "pass"
    return False


def _handoff(check: str, output: dict[str, Any], state: dict[str, Any]) -> bool:
    package = _content(output).get("handoff_package")
    final_result = _history_result(state, "/final-audit") or {}
    if check == "handoff_eligibility":
        return (
            isinstance(package, dict) and final_result.get("stage_status") == "pass"
            and bool(state.get("selected_candidate_locked"))
            and bool(state.get("build_tree_digest"))
            and bool(state.get("implementation_digest"))
        )
    if check == "blocking_unknowns_absent":
        return not _active_critical_unknowns(state)
    if check == "final_audit_preserved":
        return (
            isinstance(package, dict)
            and isinstance(package.get("final_audit_ref"), str)
            and bool(package["final_audit_ref"].strip())
            and final_result.get("stage_status") == "pass"
        )
    return False


_STAGE_EVALUATORS: dict[str, Callable[[str, dict[str, Any], dict[str, Any]], bool]] = {
    "/intake": _intake,
    "/research": _research,
    "/decompose": _decompose,
    "/architectures": _architectures,
    "/score-evidence": _score_evidence,
    "/score-audit": _score_audit,
    "/recommend": _recommend,
    "/build-tree": _build_tree,
    "/implementation": _implementation,
    "/final-audit": _final_audit,
    "/handoff-export": _handoff,
}


def validate_manifest_check_classification(manifest: dict[str, Any]) -> None:
    rows = manifest.get("project_execution_stages")
    if not isinstance(rows, list):
        raise ValueError("Pipeline Manifest.project_execution_stages must be an array")
    manifest_stages = {
        row.get("stage_id"): set(row.get("required_quality_checks", []))
        for row in rows if isinstance(row, dict)
    }
    if set(manifest_stages) != set(CHECK_EVALUATION_BASIS):
        raise ValueError(
            "Manifest Stage/check classification drift: "
            f"manifest={sorted(manifest_stages)}, classified={sorted(CHECK_EVALUATION_BASIS)}"
        )
    for stage_id, expected in manifest_stages.items():
        classified = set(CHECK_EVALUATION_BASIS[stage_id])
        if expected != classified:
            raise ValueError(
                f"Manifest check classification drift for {stage_id}: "
                f"missing={sorted(expected - classified)}, extra={sorted(classified - expected)}"
            )


def evaluate_claims(
    *, stage_output: dict[str, Any], run_state: dict[str, Any], stage: dict[str, Any]
) -> ClaimGuardResult:
    stage_id = str(stage["stage_id"])
    required = list(stage.get("required_quality_checks", []))
    supplied = stage_output.get("check_evidence")
    issues: list[dict[str, Any]] = []
    ignored: list[str] = []
    if not isinstance(supplied, dict):
        supplied = {}
        issues.append(_issue("RUNTIME_CHECK_EVIDENCE_INVALID", "check_evidence must be an object", stage_id))
    for key in sorted(set(supplied) - set(required)):
        issues.append(_issue("RUNTIME_UNKNOWN_CHECK", f"Unknown or cross-Stage check: {key}", stage_id))
    for key in required:
        record = supplied.get(key)
        if isinstance(record, dict) and "result" in record:
            ignored.append(key)
        if not _valid_check_claim(record):
            issues.append(_issue(
                "RUNTIME_REQUIRED_CHECK_CLAIM_MISSING",
                f"Missing or invalid non-authorizing check claim: {key}", stage_id,
            ))

    checks: dict[str, str] = {}
    basis = dict(CHECK_EVALUATION_BASIS[stage_id])
    if stage_id == "/project-gate-export":
        checks = {key: "fail" for key in required}
    else:
        evaluator = _STAGE_EVALUATORS[stage_id]
        for key in required:
            passed = evaluator(key, stage_output, run_state)
            checks[key] = "pass" if passed else "fail"
            if not passed:
                issues.append(_issue(
                    "RUNTIME_STAGE_PREDICATE_FAILED",
                    f"Derived predicate failed for {stage_id}:{key}", stage_id,
                ))
    return ClaimGuardResult(
        quality_checks=checks,
        issues=tuple(issues),
        evaluation_basis=basis,
        legacy_result_fields_ignored=tuple(sorted(ignored)),
    )
