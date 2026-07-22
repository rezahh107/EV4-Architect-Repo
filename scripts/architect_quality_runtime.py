"""Minimal quality-first runtime for the EV4 Architect pipeline.

Only evaluate_stage derives continuation. Serialized Stage Results are
informational and must be recomputed from Stage Output plus Run State.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifests/architect-pipeline-manifest.v1.json"
SCHEMA_PATH = ROOT / "schemas/ev4-architect-stage-result.v1.schema.json"
INFRA_BLOCKERS = {
    "ANCHOR_MISSING", "VALIDATION_BUNDLE_MISSING", "INDEPENDENT_REGENERATION_MISSING",
    "VALIDATION_PROFILE_INCOMPLETE", "EXACT_HEAD_CI_UNAVAILABLE",
    "PR_REVIEW_UNAVAILABLE", "REPOSITORY_MAINTENANCE_REQUIRED",
}
CALLER_AUTHORITY_FIELDS = {
    "status", "stage_status", "checks", "quality_checks", "next_stage",
    "canonical_payload_valid", "legacy_export_substituted",
    "build_tree_digest", "implementation_digest", "implementation_tree_digest",
}
CHECK_RESULTS = {"pass", "fail", "not_applicable", "unknown"}
RESOLUTION_TYPES = {"user_confirmation", "authoritative_source", "validated_artifact", "not_applicable"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_authority(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _load(root / MANIFEST_PATH.relative_to(ROOT))
    schema = _load(root / SCHEMA_PATH.relative_to(ROOT))
    model = manifest.get("normal_run_continuation", {})
    if model.get("model") != "quality_driven":
        raise ValueError("quality_driven continuation is required")
    if model.get("serialized_stage_result_authorizes") is not False:
        raise ValueError("serialized Stage Results must not authorize continuation")
    for key in (
        "internal_anchor_required", "internal_validation_bundle_required",
        "independent_regeneration_required", "validation_profile_required",
        "exact_head_ci_required", "pr_review_required", "repository_maintenance_required",
    ):
        if model.get(key) is not False:
            raise ValueError(f"normal_run_continuation.{key} must be false")
    if model.get("stage_result_schema") != schema.get("$id"):
        raise ValueError("Stage Result schema identity mismatch")
    return manifest, schema


def _stage_map(manifest: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    rows = manifest["project_execution_stages"]
    return [row["stage_id"] for row in rows], {row["stage_id"]: row for row in rows}


def initial_run_state(run_id: str, *, root: Path = ROOT) -> dict[str, Any]:
    order, _ = _stage_map(load_authority(root)[0])
    return {
        "run_id": run_id,
        "current_stage": order[0],
        "completed_stages": [],
        "unknown_ledger": [],
        "selected_candidate_id": None,
        "selected_candidate_locked": False,
        "build_tree_digest": None,
        "implementation_digest": None,
    }


def _issue(issue_id: str, reason: str, repair_stage: str | None, kind: str = "quality") -> dict[str, Any]:
    return {"issue_id": issue_id, "reason": reason, "repair_stage": repair_stage, "_kind": kind}


def _derive_checks(output: dict[str, Any], stage: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, str]:
    required = stage.get("required_quality_checks", [])
    allowed_na = set(stage.get("allowed_not_applicable_checks", []))
    if not required or len(required) != len(set(required)):
        raise ValueError(f"{stage['stage_id']}: finite Stage check authority is required")
    if stage.get("evaluation_mode") == "external_boundary_verified":
        return {key: "fail" for key in required}
    supplied = output.get("check_evidence", {})
    if not isinstance(supplied, dict):
        supplied = {}
        issues.append(_issue("RUNTIME_CHECK_EVIDENCE_INVALID", "check_evidence must be an object", stage["stage_id"]))
    for key in sorted(set(supplied) - set(required)):
        issues.append(_issue("RUNTIME_UNKNOWN_CHECK", f"Unknown or cross-Stage check: {key}", stage["stage_id"]))
    checks: dict[str, str] = {}
    for key in required:
        record = supplied.get(key)
        if not isinstance(record, dict) or record.get("result") not in CHECK_RESULTS or not str(record.get("reason", "")).strip():
            checks[key] = "unknown"
            issues.append(_issue("RUNTIME_REQUIRED_CHECK_MISSING", f"Missing or invalid required check: {key}", stage["stage_id"]))
            continue
        value = record["result"]
        if value == "not_applicable" and key not in allowed_na:
            value = "fail"
            issues.append(_issue("RUNTIME_NOT_APPLICABLE_FORBIDDEN", f"not_applicable is forbidden for {key}", stage["stage_id"]))
        if value in {"fail", "unknown"}:
            issues.append(_issue("RUNTIME_REQUIRED_CHECK_UNSATISFIED", f"Required check {key} is {value}", stage["stage_id"]))
        checks[key] = value
    return checks


def _apply_unknowns(output: dict[str, Any], state: dict[str, Any], stage: dict[str, Any], trusted: dict[str, Any], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ledger = copy.deepcopy(state.get("unknown_ledger", []))
    by_id = {item["unknown_id"]: item for item in ledger}
    for item in output.get("unknown_introductions", []):
        uid, statement = item.get("unknown_id"), item.get("statement")
        if not uid or not str(statement or "").strip() or uid in by_id:
            issues.append(_issue("RUNTIME_UNKNOWN_INTRODUCTION_INVALID", "Unknown identity must be new and have a statement", stage["stage_id"]))
            continue
        record = {
            "unknown_id": uid,
            "statement": statement,
            "status": "active",
            "introduced_at_stage": stage["stage_id"],
            "downstream_critical": bool(item.get("downstream_critical")),
            "evidence_refs": [],
            "resolution": None,
        }
        ledger.append(record)
        by_id[uid] = record
    evidence = trusted.get("evidence", {})
    for change in output.get("unknown_resolutions", []):
        uid, kind, note = change.get("unknown_id"), change.get("resolution_type"), change.get("note")
        record = by_id.get(uid)
        if not record or record["status"] != "active" or kind not in RESOLUTION_TYPES or not str(note or "").strip():
            issues.append(_issue("RUNTIME_UNKNOWN_RESOLUTION_INVALID", f"Invalid explicit resolution for {uid}", stage["stage_id"]))
            continue
        if kind == "not_applicable" and not stage.get("allow_not_applicable_unknown_resolution"):
            issues.append(_issue("RUNTIME_UNKNOWN_NOT_APPLICABLE_FORBIDDEN", f"not_applicable is forbidden at {stage['stage_id']}", stage["stage_id"]))
            continue
        ref = change.get("evidence_ref")
        if record.get("downstream_critical") and (not isinstance(ref, str) or ref not in evidence):
            issues.append(_issue("RUNTIME_CRITICAL_UNKNOWN_EVIDENCE_REQUIRED", f"Resolvable evidence is required for {uid}", stage["stage_id"]))
            continue
        record["status"] = "not_applicable" if kind == "not_applicable" else "resolved_with_evidence"
        record["evidence_refs"] = [ref] if ref else []
        record["resolution"] = {
            "resolution_type": kind,
            "note": note,
            "resolved_at_stage": stage["stage_id"],
            "evidence_ref": ref,
        }
    return ledger


def _producer_provenance(root: Path, trusted: dict[str, Any]):
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    base = importlib.import_module("architect_project_gate_exporter.base")
    value = trusted.get("producer_provenance")
    if isinstance(value, dict) and value.get("repository") == base.REPOSITORY and base.SHA40.fullmatch(str(value.get("commit_sha", ""))):
        return base.GitProvenance(value["repository"], value.get("ref", "runtime"), value["commit_sha"])
    try:
        sha = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        ref = subprocess.run(["git", "-C", str(root), "symbolic-ref", "--quiet", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        return base.GitProvenance(base.REPOSITORY, ref, sha)
    except Exception as exc:
        raise ValueError("Producer provenance is required only for the final external Project Gate export") from exc


def _evaluate_project_gate(output: dict[str, Any], state: dict[str, Any], root: Path, trusted: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    payload = output.get("project_gate_payload")
    if not isinstance(payload, dict):
        issues.append(_issue("RUNTIME_PROJECT_GATE_PAYLOAD_REQUIRED", "Actual canonical Architect Stage Payload is required", "/project-gate-export"))
        return None
    if payload.get("architecture_identity", {}).get("selected_candidate_id") != state.get("selected_candidate_id"):
        issues.append(_issue("RUNTIME_PROJECT_GATE_CANDIDATE_MISMATCH", "Payload candidate differs from Run State", "/project-gate-export"))
        return None
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    contracts = importlib.import_module("architect_project_gate_exporter.contracts")
    try:
        validation = contracts.validate_payload(root, payload)
        export, hashes = contracts.build_export(payload, _producer_provenance(root, trusted), state["run_id"], "quality_runtime:payload")
        contracts.validate_contracts(root, export)
        contracts.verify_hashes(export, hashes)
        if export.get("run_id") != state["run_id"] or export.get("handoff", {}).get("allowed") is not True:
            raise ValueError("Generated export is not allowed for this Run")
    except Exception as exc:
        issues.append(_issue("RUNTIME_PROJECT_GATE_VALIDATION_FAILED", f"Canonical Project Gate validation failed: {type(exc).__name__}: {exc}", "/project-gate-export"))
        return None
    return {
        "canonical_payload_valid": True,
        "legacy_export_substituted": False,
        "source_payload_digest": "sha256:" + hashes["payload_hash"],
        "export_digest": "sha256:" + hashes["export_hash"],
        "validator_identity": "ev4-producer-gate-export-validator@1.0.0",
        "validation_result": validation["status"],
        "export_id": export["export_id"],
    }


def evaluate_stage(stage_id: str, stage_output: dict[str, Any], run_state: dict[str, Any], *, root: Path = ROOT, trusted_context: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    trusted = trusted_context or {}
    manifest, schema = load_authority(root)
    order, stages = _stage_map(manifest)
    stage = stages.get(stage_id)
    if not stage or run_state.get("current_stage") != stage_id:
        raise ValueError("Run State and Stage do not match")
    if stage_output.get("run_id") != run_state.get("run_id") or stage_output.get("stage_id") != stage_id:
        raise ValueError("Stage Output identity mismatch")
    if stage_output.get("stage_version") != stage["stage_version"]:
        raise ValueError("Stage Output version mismatch")

    issues: list[dict[str, Any]] = []
    for field in sorted(CALLER_AUTHORITY_FIELDS.intersection(stage_output)):
        issues.append(_issue("RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN", f"Caller-authored authority field is forbidden: {field}", stage_id))
    for item in stage_output.get("blockers", []):
        if item.get("issue_id") not in INFRA_BLOCKERS:
            issues.append(_issue(str(item.get("issue_id")), str(item.get("reason")), item.get("repair_stage", stage_id), str(item.get("kind", "quality"))))

    checks = _derive_checks(stage_output, stage, issues)
    disposition = stage_output.get("research_disposition")
    if stage_id == "/research":
        allowed = {"active_lookup_completed", "existing_evidence_sufficient", "no_platform_question", "blocked_by_missing_required_source"}
        if disposition not in allowed:
            issues.append(_issue("RUNTIME_RESEARCH_DISPOSITION_REQUIRED", "A canonical research disposition is required", stage_id))
        elif disposition == "blocked_by_missing_required_source":
            issues.append(_issue("RESEARCH_REQUIRED_SOURCE_UNAVAILABLE", "A required downstream claim lacks obtainable evidence", stage_id))
    elif disposition is not None:
        issues.append(_issue("RUNTIME_RESEARCH_DISPOSITION_WRONG_STAGE", "research_disposition belongs only to /research", stage_id))

    ledger = _apply_unknowns(stage_output, run_state, stage, trusted, issues)
    next_state = copy.deepcopy(run_state)
    next_state["unknown_ledger"] = ledger
    selected = next_state.get("selected_candidate_id")
    locked = bool(next_state.get("selected_candidate_locked"))
    decision = stage_output.get("decision_input", {})
    if stage_id == "/recommend":
        candidate = decision.get("selected_candidate_id")
        if not candidate:
            issues.append(_issue("RUNTIME_CANDIDATE_REQUIRED", "Recommendation must identify the selected candidate", stage_id))
        else:
            selected, locked = candidate, True
            next_state["selected_candidate_id"] = candidate
            next_state["selected_candidate_locked"] = True
    elif locked and decision.get("selected_candidate_id", selected) != selected:
        issues.append(_issue("RUNTIME_CANDIDATE_DRIFT", "selected_candidate_id changed after lock", stage_id))
    if decision.get("architecture_drift") is True:
        issues.append(_issue("RUNTIME_ARCHITECTURE_DRIFT", "Architecture drift is forbidden", stage_id))
    if decision.get("hidden_recommendation") is True:
        issues.append(_issue("RUNTIME_HIDDEN_RECOMMENDATION", "Hidden recommendation is forbidden", stage_id))
    if decision.get("unknown_converted_to_exact") is True:
        issues.append(_issue("RUNTIME_UNKNOWN_TO_EXACT", "Unknown evidence cannot become an exact value", stage_id))

    build_digest = next_state.get("build_tree_digest")
    implementation_digest = next_state.get("implementation_digest")
    approved_digest = build_digest
    content = stage_output.get("canonical_content")
    if stage_id == "/build-tree":
        if content is None:
            issues.append(_issue("RUNTIME_BUILD_TREE_CONTENT_REQUIRED", "Canonical Build Tree content is required", stage_id))
        else:
            build_digest = _digest(content)
            next_state["build_tree_digest"] = build_digest
    if stage_id == "/implementation":
        if not isinstance(content, dict) or "approved_build_tree" not in content:
            issues.append(_issue("RUNTIME_APPROVED_TREE_CONTENT_REQUIRED", "Implementation content must embed the approved Build Tree", stage_id))
        else:
            approved_digest = _digest(content["approved_build_tree"])
            if not build_digest or approved_digest != build_digest:
                issues.append(_issue("RUNTIME_IMPLEMENTATION_FIDELITY_FAILED", "Implementation does not preserve the approved Build Tree", stage_id))
            implementation_digest = _digest(content)
            next_state["implementation_digest"] = implementation_digest

    findings = stage_output.get("final_audit_findings", [])
    if stage_id == "/final-audit" and any(item.get("severity") in {"blocker", "high"} for item in findings):
        issues.append(_issue("RUNTIME_FINAL_AUDIT_SEVERE", "Blocker or high Final Audit finding prevents handoff", "/implementation"))
    if stage_id != "/final-audit" and findings:
        issues.append(_issue("RUNTIME_FINAL_AUDIT_WRONG_STAGE", "Final Audit findings belong only to /final-audit", stage_id))
    if stage_id in {"/final-audit", "/handoff-export", "/project-gate-export"} and any(item["status"] == "active" and item.get("downstream_critical") for item in ledger):
        issues.append(_issue("RUNTIME_CRITICAL_UNKNOWN_ACTIVE", "A downstream-critical unknown remains active", stage_id))

    project_gate_export = None
    if stage_id == "/project-gate-export":
        project_gate_export = _evaluate_project_gate(stage_output, next_state, root, trusted, issues)
        checks = {key: "pass" if project_gate_export else "fail" for key in stage["required_quality_checks"]}

    public_issues = [
        {"issue_id": item["issue_id"], "reason": item["reason"], "repair_stage": item["repair_stage"]}
        for item in issues if item["issue_id"] not in INFRA_BLOCKERS
    ]
    status = "pass" if not public_issues else ("needs_input" if issues and all(item.get("_kind") == "user_input" for item in issues) else "blocked")
    next_stage = stage["next_stage"] if status == "pass" else None
    carried_unknowns = []
    for item in ledger:
        value = {
            "unknown_id": item["unknown_id"],
            "statement": item["statement"],
            "status": item["status"],
            "evidence_refs": item.get("evidence_refs", []),
            "downstream_critical": bool(item.get("downstream_critical")),
        }
        if item.get("resolution") is not None:
            value["resolution"] = item["resolution"]
        carried_unknowns.append(value)

    result = {
        "stage_result_schema": schema["$id"],
        "run_id": next_state["run_id"],
        "stage_id": stage_id,
        "stage_version": stage["stage_version"],
        "stage_status": status,
        "blocking_issues": public_issues,
        "carried_unknowns": carried_unknowns,
        "quality_checks": checks,
        "next_stage": next_stage,
        "research_disposition": disposition if stage_id == "/research" else None,
        "decision_state": {
            "recommendation_made": locked,
            "hidden_recommendation": False,
            "unknown_converted_to_exact": False,
            "selected_candidate_id": selected,
            "selected_candidate_locked": locked,
            "build_tree_digest": build_digest,
            "approved_build_tree_digest": approved_digest,
            "implementation_tree_digest": implementation_digest,
            "architecture_drift": False,
        },
        "runtime_context": {
            "anchor_present": False,
            "validation_bundle_present": False,
            "independent_regeneration_executed": False,
            "validation_profile_status": "not_required_for_normal_run",
            "exact_head_ci_available": False,
            "pr_review_available": False,
            "repository_maintenance_required": False,
        },
        "final_audit_findings": findings if stage_id == "/final-audit" else [],
        "project_gate_export": project_gate_export,
        "evaluation_mode": stage["evaluation_mode"],
        "evaluated_stage_output_digest": _digest(stage_output),
    }
    schema_errors = sorted(Draft202012Validator(schema).iter_errors(result), key=lambda error: list(error.absolute_path))
    if schema_errors:
        raise ValueError("Derived Stage Result schema failure: " + schema_errors[0].message)
    if status == "pass":
        next_state["completed_stages"] = [*run_state.get("completed_stages", []), stage_id]
        next_state["current_stage"] = next_stage
    else:
        next_state = copy.deepcopy(run_state)
    return result, next_state


def evaluate_run(outputs: list[dict[str, Any]], *, root: Path = ROOT, require_terminal: bool = True, trusted_context: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest, _ = load_authority(root)
    order, _ = _stage_map(manifest)
    if not outputs:
        return {"status": "invalid", "errors": ["run: empty Stage Output array"], "results": []}
    actual = [item.get("stage_id") for item in outputs]
    expected = order if require_terminal else order[:len(actual)]
    if actual != expected:
        return {"status": "invalid", "errors": ["run: mandatory Stage order mismatch"], "results": []}
    state = initial_run_state(outputs[0].get("run_id"), root=root)
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for output in outputs:
        try:
            result, state = evaluate_stage(output["stage_id"], output, state, root=root, trusted_context=trusted_context)
        except Exception as exc:
            errors.append(f"{output.get('stage_id')}: {type(exc).__name__}: {exc}")
            break
        results.append(result)
        if result["stage_status"] != "pass":
            errors.extend(f"{result['stage_id']}: {item['issue_id']}" for item in result["blocking_issues"])
            break
    if require_terminal and len(results) != len(order):
        errors.append("run: complete regression must visit every mandatory Stage")
    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "results": results,
        "stages_visited": [item["stage_id"] for item in results],
        "all_required_stages_visited": [item["stage_id"] for item in results] == order,
        "terminal_stage": order[-1],
        "run_state": state,
    }


def validate_stage_result(result: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    schema = load_authority(root)[1]
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(result)]
    return [*errors, "serialized Stage Result is informational only; recompute from Stage Output and Run State"]


def apply_partial_rerun(run_state: dict[str, Any], earliest_stage: str, *, root: Path = ROOT) -> dict[str, Any]:
    order, _ = _stage_map(load_authority(root)[0])
    index = order.index(earliest_stage)
    state = copy.deepcopy(run_state)
    invalidated = [stage for stage in state.get("completed_stages", []) if order.index(stage) >= index]
    state["completed_stages"] = [stage for stage in state.get("completed_stages", []) if order.index(stage) < index]
    state["current_stage"] = earliest_stage
    reactivated: list[str] = []
    for unknown in state.get("unknown_ledger", []):
        resolved_at = (unknown.get("resolution") or {}).get("resolved_at_stage")
        if resolved_at in order and order.index(resolved_at) >= index:
            unknown.update(status="active", resolution=None, evidence_refs=[])
            reactivated.append(unknown["unknown_id"])
    candidate_invalidated = index <= order.index("/recommend")
    if candidate_invalidated:
        state["selected_candidate_id"] = None
        state["selected_candidate_locked"] = False
    if index <= order.index("/build-tree"):
        state["build_tree_digest"] = None
    if index <= order.index("/implementation"):
        state["implementation_digest"] = None
    return {
        "earliest_rerun_stage": earliest_stage,
        "invalidated_stages": invalidated,
        "preserved_state": state,
        "reactivated_unknowns": reactivated,
        "candidate_lock_invalidated": candidate_invalidated,
    }
