"""Quality-first normal-run validation for the EV4 Architect pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifests/architect-pipeline-manifest.v1.json"
SCHEMA_PATH = ROOT / "schemas/ev4-architect-stage-result.v1.schema.json"
INFRASTRUCTURE_ONLY_BLOCKERS = {
    "ANCHOR_MISSING",
    "VALIDATION_BUNDLE_MISSING",
    "INDEPENDENT_REGENERATION_MISSING",
    "VALIDATION_PROFILE_INCOMPLETE",
    "EXACT_HEAD_CI_UNAVAILABLE",
    "PR_REVIEW_UNAVAILABLE",
    "REPOSITORY_MAINTENANCE_REQUIRED",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_authority(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _load(root / MANIFEST_PATH.relative_to(ROOT))
    schema = _load(root / SCHEMA_PATH.relative_to(ROOT))
    model = manifest.get("normal_run_continuation", {})
    if model.get("model") != "quality_driven":
        raise ValueError("Manifest normal_run_continuation.model must be quality_driven")
    for field in (
        "internal_anchor_required",
        "internal_validation_bundle_required",
        "independent_regeneration_required",
        "validation_profile_required",
        "exact_head_ci_required",
        "pr_review_required",
        "repository_maintenance_required",
    ):
        if model.get(field) is not False:
            raise ValueError(f"Manifest normal_run_continuation.{field} must be false")
    if model.get("stage_result_schema") != schema.get("$id"):
        raise ValueError("Manifest Stage Result schema identity mismatch")
    return manifest, schema


def _schema_errors(value: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda e: list(e.absolute_path))
    return [
        f"schema:{'/'.join(map(str, error.absolute_path)) or '<root>'}:{error.message}"
        for error in errors
    ]


def _stage_authority(manifest: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    rows = manifest["project_execution_stages"]
    return [row["stage_id"] for row in rows], {row["stage_id"]: row for row in rows}


def validate_stage_result(
    result: dict[str, Any],
    *,
    root: Path = ROOT,
    previous_result: dict[str, Any] | None = None,
) -> list[str]:
    manifest, schema = load_authority(root)
    order, stages = _stage_authority(manifest)
    errors = _schema_errors(result, schema)
    if errors:
        return errors

    stage_id = result["stage_id"]
    stage = stages[stage_id]
    status = result["stage_status"]
    decision = result["decision_state"]
    stage_index = order.index(stage_id)
    recommend_index = order.index("/recommend")
    build_index = order.index("/build-tree")
    implementation_index = order.index("/implementation")

    if result["stage_version"] != stage["stage_version"]:
        errors.append(f"{stage_id}: stage_version does not match Manifest")

    if status == "pass":
        if result["blocking_issues"]:
            errors.append(f"{stage_id}: pass must not retain blocking_issues")
        if result["next_stage"] != stage["next_stage"]:
            errors.append(f"{stage_id}: pass next_stage must be exact Manifest successor")
        if any(value == "fail" for value in result["quality_checks"].values()):
            errors.append(f"{stage_id}: pass contains failed quality checks")
    else:
        if not result["blocking_issues"]:
            errors.append(f"{stage_id}: {status} requires blocking_issues")
        if result["next_stage"] is not None:
            errors.append(f"{stage_id}: {status} must not name next_stage")
        for issue in result["blocking_issues"]:
            if issue["issue_id"] in INFRASTRUCTURE_ONLY_BLOCKERS:
                errors.append(f"{stage_id}: optional audit condition {issue['issue_id']} cannot block a normal Run")

    disposition = result["research_disposition"]
    if stage_id == "/research":
        if disposition is None:
            errors.append("/research: research_disposition is required")
        if disposition == "blocked_by_missing_required_source" and status != "blocked":
            errors.append("/research: missing required source disposition must block")
        if disposition in {"active_lookup_required", "existing_evidence_sufficient", "no_platform_question"} and status == "blocked":
            errors.append(f"/research: disposition {disposition} cannot itself block")
    elif disposition is not None:
        errors.append(f"{stage_id}: research_disposition is only valid for /research")

    if decision["hidden_recommendation"]:
        errors.append(f"{stage_id}: hidden recommendation is forbidden")
    if decision["unknown_converted_to_exact"]:
        errors.append(f"{stage_id}: unknown evidence cannot become an exact value")
    if decision["architecture_drift"]:
        errors.append(f"{stage_id}: architecture drift is forbidden")

    if stage_index < recommend_index:
        if decision["recommendation_made"]:
            errors.append(f"{stage_id}: recommendation is premature")
        if decision["selected_candidate_id"] is not None or decision["selected_candidate_locked"]:
            errors.append(f"{stage_id}: candidate selection is premature")
    else:
        if not decision["recommendation_made"]:
            errors.append(f"{stage_id}: recommendation state must remain visible")
        if not decision["selected_candidate_id"] or not decision["selected_candidate_locked"]:
            errors.append(f"{stage_id}: selected candidate must be identified and locked")

    if stage_index < build_index and decision["build_tree_digest"] is not None:
        errors.append(f"{stage_id}: build-tree selection is premature")
    if stage_index < implementation_index and decision["implementation_tree_digest"] is not None:
        errors.append(f"{stage_id}: implementation selection is premature")

    findings = result["final_audit_findings"]
    if stage_id != "/final-audit" and findings:
        errors.append(f"{stage_id}: final_audit_findings belong to /final-audit")
    if stage_id == "/final-audit" and status == "pass":
        severe = [f["finding_id"] for f in findings if f["severity"] in {"blocker", "high"}]
        if severe:
            errors.append("/final-audit: blocker or high-severity findings prevent pass")
        if result["quality_checks"].get("final_audit_acceptance") != "pass":
            errors.append("/final-audit: pass requires final_audit_acceptance=pass")

    export = result["project_gate_export"]
    if stage_id == "/project-gate-export" and status == "pass":
        if not export or export["canonical_payload_valid"] is not True:
            errors.append("/project-gate-export: canonical Architect payload must validate")
        if not export or export["legacy_export_substituted"] is not False:
            errors.append("/project-gate-export: legacy export substitution is forbidden")
    elif stage_id != "/project-gate-export" and export is not None:
        errors.append(f"{stage_id}: project_gate_export belongs to terminal Stage")

    unknowns = result["carried_unknowns"]
    current_by_id = {item["unknown_id"]: item for item in unknowns}
    if len(current_by_id) != len(unknowns):
        errors.append(f"{stage_id}: duplicate unknown identity")
    for item in unknowns:
        if item["status"] != "active" and not item["evidence_refs"]:
            errors.append(f"{stage_id}: unknown {item['unknown_id']} may close only with evidence")

    if previous_result is not None:
        if result["run_id"] != previous_result["run_id"]:
            errors.append(f"{stage_id}: run_id discontinuity")
        if previous_result["next_stage"] != stage_id:
            errors.append(f"{stage_id}: previous Stage did not name this exact successor")
        prior = previous_result["decision_state"]
        if prior["selected_candidate_locked"]:
            if decision["selected_candidate_id"] != prior["selected_candidate_id"]:
                errors.append(f"{stage_id}: selected_candidate_id changed after lock")
            if not decision["selected_candidate_locked"]:
                errors.append(f"{stage_id}: selected candidate lock was removed")
        if prior["build_tree_digest"] is not None and decision["build_tree_digest"] != prior["build_tree_digest"]:
            errors.append(f"{stage_id}: approved build tree changed downstream")
        if stage_id == "/implementation" and decision["implementation_tree_digest"] != decision["build_tree_digest"]:
            errors.append("/implementation: implementation must preserve the approved tree")
        prior_active = {item["unknown_id"] for item in previous_result["carried_unknowns"] if item["status"] == "active"}
        for unknown_id in prior_active:
            if unknown_id not in current_by_id:
                errors.append(f"{stage_id}: active unknown {unknown_id} disappeared without explicit resolution")

    return errors


def validate_run(results: list[dict[str, Any]], *, root: Path = ROOT, require_terminal: bool = True) -> dict[str, Any]:
    manifest, _ = load_authority(root)
    order, _ = _stage_authority(manifest)
    errors: list[str] = []
    if not results:
        return {"status": "invalid", "errors": ["run: expected a non-empty Stage Result array"]}

    actual = [item.get("stage_id") for item in results]
    expected = order if require_terminal else order[: len(actual)]
    if actual != expected:
        errors.append("run: mandatory Stage order mismatch")

    previous = None
    score_audit_accepted = False
    for result in results:
        errors.extend(validate_stage_result(result, root=root, previous_result=previous))
        if result.get("stage_id") == "/score-audit":
            score_audit_accepted = result.get("stage_status") == "pass" and result.get("quality_checks", {}).get("score_audit_acceptance") == "pass"
        if result.get("stage_id") == "/recommend" and not score_audit_accepted:
            errors.append("/recommend: accepted /score-audit is required before recommendation")
        if result.get("stage_id") in {"/handoff-export", "/project-gate-export"}:
            final = next((item for item in results if item.get("stage_id") == "/final-audit"), None)
            if not final or final.get("stage_status") != "pass":
                errors.append(f"{result.get('stage_id')}: accepted /final-audit is required before handoff")
        previous = result

    if require_terminal:
        if len(results) != len(order):
            errors.append("run: complete regression must visit every mandatory Stage")
        if any(item.get("stage_status") != "pass" for item in results):
            errors.append("run: complete regression contains non-pass Stages")

    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "stages_visited": actual,
        "all_required_stages_visited": actual == order,
        "terminal_stage": order[-1],
    }


def validate_run_file(path: Path, *, root: Path = ROOT) -> dict[str, Any]:
    value = _load(path)
    if not isinstance(value, list):
        return {"status": "invalid", "errors": ["run file must contain a JSON array"]}
    return validate_run(value, root=root)
