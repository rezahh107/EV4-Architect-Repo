"""Single evaluator-derived quality Runtime for the EV4 Architect pipeline."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from jsonschema import Draft202012Validator

from architect_runtime_errors import (
    ArchitectRuntimeExpectedError,
    ProjectGateValidationError,
    RunSequenceValidationError,
    RuntimeDiagnostic,
    RuntimeEnvironmentError,
    StageOutputValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifests/architect-pipeline-manifest.v1.json"
SCHEMA_PATH = ROOT / "schemas/ev4-architect-stage-result.v1.schema.json"
BASE_STAGE_OUTPUT_SCHEMA_PATH = ROOT / "schemas/architect-conversational-stage-output-base.v1.schema.json"
RUNTIME_INTERFACE_ID = "ev4-architect-quality-runtime@2.0.0"
INFRA_BLOCKERS = {
    "ANCHOR_MISSING", "VALIDATION_BUNDLE_MISSING", "INDEPENDENT_REGENERATION_MISSING",
    "VALIDATION_PROFILE_INCOMPLETE", "EXACT_HEAD_CI_UNAVAILABLE",
    "PR_REVIEW_UNAVAILABLE", "REPOSITORY_MAINTENANCE_REQUIRED",
}
STAGE_OUTPUT_SHARED_STAGE_RESULT_FIELDS = frozenset(
    {"run_id", "stage_id", "stage_version", "research_disposition", "final_audit_findings"}
)
EVALUATOR_DERIVED_NESTED_DEFS = ("decision_state", "runtime_context", "project_gate_export")
EXPLICIT_LEGACY_AUTHORITY_ALIASES = frozenset(
    {
        "status", "checks", "implementation_digest", "continuation_authorized",
        "official_pass", "official_digest", "project_gate_payload", "synthetic",
        "source_kind", "producer_provenance",
    }
)
RESOLUTION_TYPES = {"user_confirmation", "authoritative_source", "validated_artifact", "not_applicable"}
SOURCE_KINDS = {"live_conversation", "fixture", "example", "test_vector"}


@dataclass(frozen=True)
class StageResultAuthorityClassification:
    shared_stage_output_fields: frozenset[str]
    evaluator_owned_top_level_fields: frozenset[str]
    evaluator_derived_nested_fields: frozenset[str]
    explicit_legacy_authority_aliases: frozenset[str]
    forbidden_top_level_stage_output_fields: frozenset[str]


@dataclass(frozen=True)
class RunContext:
    source_kind: Literal["live_conversation", "fixture", "example", "test_vector"]
    verified_evidence_refs: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        diagnostics: list[RuntimeDiagnostic] = []
        if self.source_kind not in SOURCE_KINDS:
            diagnostics.append(RuntimeDiagnostic(
                "RUNTIME_SOURCE_KIND_INVALID",
                f"Unsupported RunContext.source_kind: {self.source_kind!r}",
                path="RunContext.source_kind",
            ))
        if any(not isinstance(item, str) or not item for item in self.verified_evidence_refs):
            diagnostics.append(RuntimeDiagnostic(
                "RUNTIME_EVIDENCE_REFS_INVALID",
                "RunContext.verified_evidence_refs must contain non-empty strings",
                path="RunContext.verified_evidence_refs",
            ))
        if diagnostics:
            raise RuntimeEnvironmentError(diagnostics)

    @property
    def synthetic(self) -> bool:
        return self.source_kind != "live_conversation"


class GitProvider(Protocol):
    def provenance(self, root: Path) -> Any: ...


class SubprocessGitProvider:
    """Read producer identity only from the actual checkout."""

    def _run(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            encoding="utf-8", check=False,
        )

    def _git(self, root: Path, *args: str) -> str:
        completed = self._run(root, *args)
        if completed.returncode:
            raise RuntimeEnvironmentError(RuntimeDiagnostic(
                "RUNTIME_GIT_COMMAND_FAILED",
                completed.stderr.strip() or completed.stdout.strip() or f"git {' '.join(args)} failed",
                path="git",
            ))
        return completed.stdout.strip()

    def provenance(self, root: Path) -> Any:
        scripts = root / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        base = importlib.import_module("architect_project_gate_exporter.base")
        top = Path(self._git(root, "rev-parse", "--show-toplevel")).resolve()
        if top != root.resolve():
            raise RuntimeEnvironmentError(RuntimeDiagnostic(
                "RUNTIME_GIT_ROOT_MISMATCH", "Runtime Git provider requires the repository root"
            ))
        remote = self._git(root, "remote", "get-url", "origin")
        repository = None
        for pattern in (
            r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?",
            r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?",
            r"ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?",
        ):
            match = re.fullmatch(pattern, remote.strip())
            if match:
                repository = match.group(1).removesuffix(".git")
                break
        if (repository or "").lower() != base.REPOSITORY.lower():
            raise RuntimeEnvironmentError(RuntimeDiagnostic(
                "RUNTIME_GIT_REPOSITORY_MISMATCH",
                f"Runtime Git provider expected {base.REPOSITORY}, observed {remote!r}",
            ))
        symbolic = self._run(root, "symbolic-ref", "--quiet", "--short", "HEAD")
        ref = symbolic.stdout.strip() if symbolic.returncode == 0 else "detached-exact-head"
        sha = self._git(root, "rev-parse", "HEAD")
        if not base.SHA40.fullmatch(sha):
            raise RuntimeEnvironmentError(RuntimeDiagnostic(
                "RUNTIME_GIT_HEAD_INVALID", "Runtime Git provider requires a full HEAD SHA"
            ))
        dirty = self._git(root, "-c", "core.quotepath=false", "status", "--porcelain=v1", "--untracked-files=all")
        if dirty:
            raise RuntimeEnvironmentError(RuntimeDiagnostic(
                "RUNTIME_GIT_CHECKOUT_DIRTY", "Runtime Git provider requires a clean checkout"
            ))
        return base.GitProvenance(base.REPOSITORY, ref, sha)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _schema_properties(value: Any, *, location: str) -> frozenset[str]:
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be a JSON object")
    properties = value.get("properties")
    if not isinstance(properties, dict):
        raise ValueError(f"{location}.properties must be a JSON object")
    if any(not isinstance(key, str) or not key for key in properties):
        raise ValueError(f"{location}.properties keys must be non-empty strings")
    return frozenset(properties)


def derive_stage_result_authority(schema: dict[str, Any]) -> StageResultAuthorityClassification:
    top_level = _schema_properties(schema, location="Stage Result Schema")
    missing_shared = STAGE_OUTPUT_SHARED_STAGE_RESULT_FIELDS - top_level
    if missing_shared:
        raise ValueError("Stage Result shared Stage Output fields are missing from the Schema: " f"{sorted(missing_shared)}")
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        raise ValueError("Stage Result Schema.$defs must be a JSON object")
    nested_fields: set[str] = set()
    for name in EVALUATOR_DERIVED_NESTED_DEFS:
        if name not in defs:
            raise ValueError(f"Stage Result Schema.$defs.{name} is required for authority classification")
        nested_fields.update(_schema_properties(defs[name], location=f"Stage Result Schema.$defs.{name}"))
    evaluator_top_level = top_level - STAGE_OUTPUT_SHARED_STAGE_RESULT_FIELDS
    forbidden = (evaluator_top_level | frozenset(nested_fields) | EXPLICIT_LEGACY_AUTHORITY_ALIASES) - STAGE_OUTPUT_SHARED_STAGE_RESULT_FIELDS
    return StageResultAuthorityClassification(
        shared_stage_output_fields=STAGE_OUTPUT_SHARED_STAGE_RESULT_FIELDS,
        evaluator_owned_top_level_fields=frozenset(evaluator_top_level),
        evaluator_derived_nested_fields=frozenset(nested_fields),
        explicit_legacy_authority_aliases=EXPLICIT_LEGACY_AUTHORITY_ALIASES,
        forbidden_top_level_stage_output_fields=frozenset(forbidden),
    )


def _validate_caller_authority_classification(schema: dict[str, Any]) -> None:
    classification = derive_stage_result_authority(schema)
    overlap = classification.shared_stage_output_fields & classification.forbidden_top_level_stage_output_fields
    if overlap:
        raise ValueError(f"Stage Result fields cannot be both shared and evaluator-owned: {sorted(overlap)}")


def _base_schema_authority_fields(schema: dict[str, Any]) -> frozenset[str]:
    values = schema.get("$defs", {}).get("caller_authority_field", {}).get("enum")
    if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values) or len(values) != len(set(values)):
        raise ValueError("Conversational Base Schema caller authority mirror is invalid")
    return frozenset(values)


def validate_authority_documents(manifest: dict[str, Any], schema: dict[str, Any]) -> StageResultAuthorityClassification:
    if not isinstance(manifest, dict):
        raise ValueError("Pipeline Manifest must be a JSON object")
    if not isinstance(schema, dict):
        raise ValueError("Stage Result Schema must be a JSON object")
    Draft202012Validator.check_schema(schema)
    model = manifest.get("normal_run_continuation", {})
    if not isinstance(model, dict):
        raise ValueError("normal_run_continuation must be a JSON object")
    if model.get("model") != "quality_driven":
        raise ValueError("quality_driven continuation is required")
    if model.get("serialized_stage_result_authorizes") is not False:
        raise ValueError("serialized Stage Results must not authorize continuation")
    for key in ("internal_anchor_required", "internal_validation_bundle_required", "independent_regeneration_required", "validation_profile_required", "exact_head_ci_required", "pr_review_required", "repository_maintenance_required"):
        if model.get(key) is not False:
            raise ValueError(f"normal_run_continuation.{key} must be false")
    if model.get("stage_result_schema") != schema.get("$id"):
        raise ValueError("Stage Result schema identity mismatch")
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    claim_guard = importlib.import_module("architect_stage_claim_guard")
    claim_guard.validate_manifest_check_classification(manifest)
    _validate_caller_authority_classification(schema)
    return derive_stage_result_authority(schema)


def load_authority(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _load(root / MANIFEST_PATH.relative_to(ROOT))
    schema = _load(root / SCHEMA_PATH.relative_to(ROOT))
    validate_authority_documents(manifest, schema)
    return manifest, schema


def load_stage_output_schema(root: Path, result_schema: dict[str, Any]) -> dict[str, Any]:
    schema = _load(root / BASE_STAGE_OUTPUT_SCHEMA_PATH.relative_to(ROOT))
    Draft202012Validator.check_schema(schema)
    derived = derive_stage_result_authority(result_schema).forbidden_top_level_stage_output_fields
    mirrored = _base_schema_authority_fields(schema)
    if derived != mirrored:
        raise ValueError("Runtime and Base Schema forbidden sets differ; classification mirror update required: " f"missing={sorted(derived - mirrored)}, extra={sorted(mirrored - derived)}")
    return schema


CALLER_AUTHORITY_FIELDS = derive_stage_result_authority(_load(SCHEMA_PATH)).forbidden_top_level_stage_output_fields


def _stage_map(manifest: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    rows = manifest["project_execution_stages"]
    return [row["stage_id"] for row in rows], {row["stage_id"]: row for row in rows}


def initial_run_state(run_id: str, *, root: Path = ROOT) -> dict[str, Any]:
    order, _ = _stage_map(load_authority(root)[0])
    return {"run_id": run_id, "current_stage": order[0], "completed_stages": [], "unknown_ledger": [], "selected_candidate_id": None, "selected_candidate_locked": False, "build_tree_digest": None, "implementation_digest": None, "evaluated_stage_outputs": [], "derived_stage_results": []}


def _issue(issue_id: str, reason: str, repair_stage: str | None, kind: str = "quality") -> dict[str, Any]:
    return {"issue_id": issue_id, "reason": reason, "repair_stage": repair_stage, "_kind": kind}


def _schema_diagnostics(stage_output: Any, schema: dict[str, Any], stage_id: str) -> list[RuntimeDiagnostic]:
    found = sorted(Draft202012Validator(schema).iter_errors(stage_output), key=lambda error: ([str(item) for item in error.absolute_path], error.message))
    return [RuntimeDiagnostic("RUNTIME_STAGE_OUTPUT_SCHEMA_INVALID", error.message, path=".".join(map(str, error.absolute_path)) or "<root>", stage_id=stage_id) for error in found]


def _apply_unknowns(output: dict[str, Any], state: dict[str, Any], stage: dict[str, Any], run_context: RunContext, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ledger = copy.deepcopy(state.get("unknown_ledger", []))
    by_id = {item["unknown_id"]: item for item in ledger}
    for item in output.get("unknown_introductions", []):
        uid = item.get("unknown_id") if isinstance(item, dict) else None
        statement = item.get("statement") if isinstance(item, dict) else None
        if not uid or not str(statement or "").strip() or uid in by_id:
            issues.append(_issue("RUNTIME_UNKNOWN_INTRODUCTION_INVALID", "Unknown identity must be new and have a statement", stage["stage_id"]))
            continue
        record = {"unknown_id": uid, "statement": statement, "status": "active", "introduced_at_stage": stage["stage_id"], "downstream_critical": bool(item.get("downstream_critical")), "evidence_refs": [], "resolution": None}
        ledger.append(record)
        by_id[uid] = record
    for change in output.get("unknown_resolutions", []):
        if not isinstance(change, dict):
            issues.append(_issue("RUNTIME_UNKNOWN_RESOLUTION_INVALID", "Unknown resolution must be an object", stage["stage_id"]))
            continue
        uid, kind, note = change.get("unknown_id"), change.get("resolution_type"), change.get("note")
        record = by_id.get(uid)
        if not record or record["status"] != "active" or kind not in RESOLUTION_TYPES or not str(note or "").strip():
            issues.append(_issue("RUNTIME_UNKNOWN_RESOLUTION_INVALID", f"Invalid explicit resolution for {uid}", stage["stage_id"]))
            continue
        if kind == "not_applicable" and not stage.get("allow_not_applicable_unknown_resolution"):
            issues.append(_issue("RUNTIME_UNKNOWN_NOT_APPLICABLE_FORBIDDEN", f"not_applicable is forbidden at {stage['stage_id']}", stage["stage_id"]))
            continue
        ref = change.get("evidence_ref")
        if record.get("downstream_critical") and (not isinstance(ref, str) or ref not in run_context.verified_evidence_refs):
            issues.append(_issue("RUNTIME_CRITICAL_UNKNOWN_EVIDENCE_REQUIRED", f"Resolvable evidence is required for {uid}", stage["stage_id"]))
            continue
        record["status"] = "not_applicable" if kind == "not_applicable" else "resolved_with_evidence"
        record["evidence_refs"] = [ref] if ref else []
        record["resolution"] = {"resolution_type": kind, "note": note, "resolved_at_stage": stage["stage_id"], "evidence_ref": ref}
    return ledger


def _producer_provenance(root: Path, git_provider: GitProvider | None) -> Any:
    return (git_provider or SubprocessGitProvider()).provenance(root)


def _expected_issues(exc: ArchitectRuntimeExpectedError, stage_id: str) -> list[dict[str, Any]]:
    return [_issue(item.code, item.message, item.stage_id or stage_id) for item in exc.diagnostics]


def _evaluate_project_gate(output: dict[str, Any], state: dict[str, Any], root: Path, run_context: RunContext, git_provider: GitProvider | None, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    contracts = importlib.import_module("architect_project_gate_exporter.contracts")
    runtime_gate = importlib.import_module("architect_runtime_project_gate")
    eligibility_module = importlib.import_module("architect_project_gate_exporter.eligibility")
    assembler = importlib.import_module("architect_runtime_payload_assembler")
    try:
        payload = assembler.assemble_architect_stage_payload(run_state=state, source_kind=run_context.source_kind)
        validation = runtime_gate.validate_payload(root, payload)
        eligibility = eligibility_module.derive_handoff_eligibility(payload)
        export, hashes = contracts.build_export(payload, _producer_provenance(root, git_provider), state["run_id"], "quality_runtime:runtime_issued_payload")
        runtime_gate.validate_contracts(root, export)
        contracts.verify_hashes(export, hashes)
        allowed = export.get("handoff", {}).get("allowed") is True
        if export.get("run_id") != state["run_id"]:
            raise ProjectGateValidationError(RuntimeDiagnostic("RUNTIME_PROJECT_GATE_RUN_MISMATCH", "Generated export belongs to another Run", stage_id="/project-gate-export"))
        if run_context.synthetic and allowed:
            raise ProjectGateValidationError(RuntimeDiagnostic("RUNTIME_SYNTHETIC_HANDOFF_ALLOWED", "Synthetic Runtime context produced an allowed real handoff", stage_id="/project-gate-export"))
        if not run_context.synthetic and eligibility["would_allow"] and not allowed:
            raise ProjectGateValidationError(RuntimeDiagnostic("RUNTIME_ELIGIBLE_LIVE_HANDOFF_BLOCKED", "Eligible live Runtime context did not produce an allowed handoff", stage_id="/project-gate-export"))
    except ArchitectRuntimeExpectedError as exc:
        issues.extend(_expected_issues(exc, "/project-gate-export"))
        return None
    except contracts.ExportError as exc:
        issues.append(_issue(exc.code, exc.reason, "/project-gate-export"))
        return None
    return {"canonical_payload_valid": True, "legacy_export_substituted": False, "source_payload_digest": "sha256:" + hashes["payload_hash"], "export_digest": "sha256:" + hashes["export_hash"], "validator_identity": "ev4-producer-gate-export-validator@1.0.0", "validation_result": validation["status"], "export_id": export["export_id"], "runtime_issued_payload": payload, "functional_eligibility": eligibility, "execution_context": {"source_kind": run_context.source_kind, "synthetic": run_context.synthetic}, "handoff_allowed": allowed}


def evaluate_stage(stage_id: str, stage_output: dict[str, Any], run_state: dict[str, Any], *, root: Path = ROOT, run_context: RunContext | None = None, git_provider: GitProvider | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    context = run_context or RunContext(source_kind="live_conversation")
    manifest, result_schema = load_authority(root)
    stage_output_schema = load_stage_output_schema(root, result_schema)
    authority = derive_stage_result_authority(result_schema)
    _, stages = _stage_map(manifest)
    stage = stages.get(stage_id)
    if not stage or run_state.get("current_stage") != stage_id:
        raise RunSequenceValidationError(RuntimeDiagnostic("RUNTIME_STAGE_SEQUENCE_MISMATCH", "Run State and Stage do not match", stage_id=stage_id))
    diagnostics = _schema_diagnostics(stage_output, stage_output_schema, stage_id)
    if isinstance(stage_output, dict):
        for field in sorted(authority.forbidden_top_level_stage_output_fields.intersection(stage_output)):
            code = "RUNTIME_CALLER_PROJECT_GATE_PAYLOAD_FORBIDDEN" if field == "project_gate_payload" else "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
            diagnostics.append(RuntimeDiagnostic(code, f"Caller-authored authority field is forbidden: {field}", path=field, stage_id=stage_id))
        if stage_output.get("run_id") != run_state.get("run_id") or stage_output.get("stage_id") != stage_id:
            diagnostics.append(RuntimeDiagnostic("RUNTIME_STAGE_OUTPUT_IDENTITY_MISMATCH", "Stage Output identity mismatch", stage_id=stage_id))
        if stage_output.get("stage_version") != stage.get("stage_version"):
            diagnostics.append(RuntimeDiagnostic("RUNTIME_STAGE_OUTPUT_VERSION_MISMATCH", "Stage Output version mismatch", stage_id=stage_id))
    if diagnostics:
        raise StageOutputValidationError(diagnostics)
    issues: list[dict[str, Any]] = []
    for item in stage_output.get("blockers", []):
        if isinstance(item, dict) and item.get("issue_id") not in INFRA_BLOCKERS:
            issues.append(_issue(str(item.get("issue_id")), str(item.get("reason")), item.get("repair_stage", stage_id), str(item.get("kind", "quality"))))
    next_state = copy.deepcopy(run_state)
    next_state["unknown_ledger"] = _apply_unknowns(stage_output, next_state, stage, context, issues)
    selected = next_state.get("selected_candidate_id")
    locked = bool(next_state.get("selected_candidate_locked"))
    decision = stage_output.get("decision_input") if isinstance(stage_output.get("decision_input"), dict) else {}
    if stage_id != "/recommend" and locked and decision.get("selected_candidate_id", selected) != selected:
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
    if stage_id == "/build-tree" and content is not None:
        build_digest = _digest(content)
        next_state["build_tree_digest"] = build_digest
    if stage_id == "/implementation" and isinstance(content, dict):
        approved = content.get("approved_build_tree")
        if isinstance(approved, dict):
            approved_digest = _digest(approved)
        implementation_digest = _digest(content)
        next_state["implementation_digest"] = implementation_digest
    findings = stage_output.get("final_audit_findings", [])
    if stage_id != "/final-audit" and findings:
        issues.append(_issue("RUNTIME_FINAL_AUDIT_WRONG_STAGE", "Final Audit findings belong only to /final-audit", stage_id))
    if stage_id in {"/final-audit", "/handoff-export", "/project-gate-export"} and any(isinstance(item, dict) and item.get("status") == "active" and item.get("downstream_critical") for item in next_state.get("unknown_ledger", [])):
        issues.append(_issue("RUNTIME_CRITICAL_UNKNOWN_ACTIVE", "A downstream-critical unknown remains active", stage_id))
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    claim_guard = importlib.import_module("architect_stage_claim_guard")
    guard_state = dict(next_state)
    guard_state["_digest_function"] = _digest
    guard = claim_guard.evaluate_claims(stage_output=stage_output, run_state=guard_state, stage=stage)
    issues.extend(_issue(item["issue_id"], item["reason"], item.get("repair_stage", stage_id)) for item in guard.issues)
    checks = dict(guard.quality_checks)
    project_gate_export = None
    if stage_id == "/project-gate-export" and not issues:
        if run_context is None:
            issues.append(_issue("RUNTIME_RUN_CONTEXT_REQUIRED", "The terminal Stage requires an explicit Runtime-owned RunContext", stage_id))
        else:
            project_gate_export = _evaluate_project_gate(stage_output, next_state, root, context, git_provider, issues)
            checks = {key: "pass" if project_gate_export else "fail" for key in stage["required_quality_checks"]}
    if stage_id == "/recommend" and not issues:
        candidate = decision.get("selected_candidate_id")
        selected, locked = candidate, True
        next_state["selected_candidate_id"] = candidate
        next_state["selected_candidate_locked"] = True
    else:
        selected = next_state.get("selected_candidate_id")
        locked = bool(next_state.get("selected_candidate_locked"))
    public_issues = [{"issue_id": item["issue_id"], "reason": item["reason"], "repair_stage": item["repair_stage"]} for item in issues if item["issue_id"] not in INFRA_BLOCKERS]
    status = "pass" if not public_issues else "needs_input" if issues and all(item.get("_kind") == "user_input" for item in issues) else "blocked"
    next_stage = stage["next_stage"] if status == "pass" else None
    carried_unknowns: list[dict[str, Any]] = []
    for item in next_state.get("unknown_ledger", []):
        value = {"unknown_id": item["unknown_id"], "statement": item["statement"], "status": item["status"], "evidence_refs": item.get("evidence_refs", []), "downstream_critical": bool(item.get("downstream_critical"))}
        if item.get("resolution") is not None:
            value["resolution"] = item["resolution"]
        carried_unknowns.append(value)
    result = {
        "stage_result_schema": result_schema["$id"],
        "run_id": run_state["run_id"],
        "stage_id": stage_id,
        "stage_version": stage["stage_version"],
        "stage_status": status,
        "quality_check_basis": guard.evaluation_basis,
        "blocking_issues": public_issues,
        "carried_unknowns": carried_unknowns,
        "quality_checks": checks,
        "next_stage": next_stage,
        "research_disposition": stage_output.get("research_disposition") if stage_id == "/research" else None,
        "decision_state": {"recommendation_made": locked, "hidden_recommendation": False, "unknown_converted_to_exact": False, "selected_candidate_id": selected, "selected_candidate_locked": locked, "build_tree_digest": build_digest, "approved_build_tree_digest": approved_digest, "implementation_tree_digest": implementation_digest, "architecture_drift": False},
        "runtime_context": {"anchor_present": False, "validation_bundle_present": False, "independent_regeneration_executed": False, "validation_profile_status": "not_required_for_normal_run", "exact_head_ci_available": False, "pr_review_available": False, "repository_maintenance_required": False, "source_kind": context.source_kind, "synthetic": context.synthetic, "legacy_check_results_ignored": list(guard.legacy_result_fields_ignored)},
        "final_audit_findings": findings if stage_id == "/final-audit" else [],
        "project_gate_export": project_gate_export,
        "evaluation_mode": stage["evaluation_mode"],
        "evaluated_stage_output_digest": _digest(stage_output),
    }
    if status == "pass":
        result["completion_class"] = claim_guard.REASONING_COMPLETE if stage_id in claim_guard.REASONING_STAGES else claim_guard.VALIDATED_PASS
    schema_errors = sorted(Draft202012Validator(result_schema).iter_errors(result), key=lambda error: list(error.absolute_path))
    if schema_errors:
        raise AssertionError("Derived Stage Result schema failure: " + schema_errors[0].message)
    if status == "pass":
        next_state["completed_stages"] = [*run_state.get("completed_stages", []), stage_id]
        next_state["current_stage"] = next_stage
        next_state["evaluated_stage_outputs"] = [*run_state.get("evaluated_stage_outputs", []), copy.deepcopy(stage_output)]
        next_state["derived_stage_results"] = [*run_state.get("derived_stage_results", []), copy.deepcopy(result)]
    else:
        next_state = copy.deepcopy(run_state)
    return result, next_state


def _invalid_run(errors: list[str], results: list[dict[str, Any]], state: dict[str, Any] | None, order: list[str]) -> dict[str, Any]:
    return {"status": "invalid", "errors": sorted(set(errors)), "results": results, "stages_visited": [item["stage_id"] for item in results], "all_required_stages_visited": [item["stage_id"] for item in results] == order, "terminal_stage": order[-1], "run_state": state}


def evaluate_run(outputs: list[dict[str, Any]], *, run_context: RunContext, root: Path = ROOT, require_terminal: bool = True, git_provider: GitProvider | None = None) -> dict[str, Any]:
    manifest, _ = load_authority(root)
    order, _ = _stage_map(manifest)
    results: list[dict[str, Any]] = []
    state: dict[str, Any] | None = None
    try:
        if not outputs:
            raise RunSequenceValidationError(RuntimeDiagnostic("RUNTIME_RUN_EMPTY", "Stage Output array is empty", path="run"))
        actual = [item.get("stage_id") if isinstance(item, dict) else None for item in outputs]
        expected = order if require_terminal else order[: len(actual)]
        if actual != expected:
            raise RunSequenceValidationError(RuntimeDiagnostic("RUNTIME_STAGE_ORDER_MISMATCH", "Mandatory Stage order mismatch", path="run"))
        state = initial_run_state(outputs[0].get("run_id"), root=root)
        for output in outputs:
            result, state = evaluate_stage(output["stage_id"], output, state, root=root, run_context=run_context, git_provider=git_provider)
            results.append(result)
            if result["stage_status"] != "pass":
                errors = [f"{result['stage_id']}: {item['issue_id']}" for item in result["blocking_issues"]]
                if require_terminal and len(results) != len(order):
                    errors.append("run: complete regression must visit every mandatory Stage")
                return _invalid_run(errors, results, state, order)
    except ArchitectRuntimeExpectedError as exc:
        errors = [item.render() for item in exc.diagnostics]
        if require_terminal and len(results) != len(order):
            errors.append("run: complete regression must visit every mandatory Stage")
        return _invalid_run(errors, results, state, order)
    return {"status": "valid", "errors": [], "results": results, "stages_visited": [item["stage_id"] for item in results], "all_required_stages_visited": [item["stage_id"] for item in results] == order, "terminal_stage": order[-1], "run_state": state}


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
    state["evaluated_stage_outputs"] = [item for item in state.get("evaluated_stage_outputs", []) if item.get("stage_id") in order and order.index(item["stage_id"]) < index]
    state["derived_stage_results"] = [item for item in state.get("derived_stage_results", []) if item.get("stage_id") in order and order.index(item["stage_id"]) < index]
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
    return {"earliest_rerun_stage": earliest_stage, "invalidated_stages": invalidated, "preserved_state": state, "reactivated_unknowns": reactivated, "candidate_lock_invalidated": candidate_invalidated}
