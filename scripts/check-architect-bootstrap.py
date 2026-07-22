#!/usr/bin/env python3
"""Fail-closed validation for EV4 Architect bootstrap and runtime authority."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

BOOTSTRAP_REL = Path("manifests/architect-conversation-bootstrap.v1.json")
SCHEMA_REL = Path("schemas/architect-conversation-bootstrap.v1.schema.json")
PIPELINE_REL = Path("manifests/architect-pipeline-manifest.v1.json")
ALIGNMENT_REL = Path("contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md")
AGENTS_REL = Path("AGENTS.md")
README_REL = Path("README.md")
STATUS_REL = Path("STATUS.md")
OVERRIDES_REL = Path("02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md")
FIRST_RUN_REL = Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md")
PROJECT_INSTRUCTIONS_REL = Path("release/EV4_PROJECT_RELEASE_PACK_v1/PROJECT_INSTRUCTIONS_FINAL.md")
CORE_BUNDLE_REL = Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CORE_CONTRACTS_BUNDLE.md")
PROTOCOLS_REL = Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_STAGE_PROTOCOLS_BUNDLE.md")

EXPECTED_CONTRACT_ID = "ev4-architect-conversation-bootstrap"
EXPECTED_CONTRACT_VERSION = "1.3.0"
EXPECTED_OWNER = "rezahh107/EV4-Architect-Repo"
EXPECTED_TRIGGERS = ["شروع", "شروع کن", "شروع سکشن جدید", "start", "begin", "start a new section"]
EXPECTED_PRECONDITION_IDS = [
    "repository_instructions_loaded",
    "no_active_architect_run",
    "no_resumable_runtime_material",
    "no_project_input",
]
EXPECTED_FORBIDDEN_IDS = [
    "run_any_pipeline_stage",
    "recommend_architecture",
    "produce_elementor_tree",
    "invent_exact_values",
    "trust_serialized_stage_result",
    "claim_builder_or_production_readiness",
]
EXPECTED_ROUTING_ACTIONS = {
    "resumable_stage_result_present": "recompute_from_stage_output_and_run_state",
    "latest_stage_output_without_stage_result": "evaluate_stage_output_with_run_state",
    "explicit_repository_maintenance_request": "repository_maintenance_mode_not_project_run",
}
EXPECTED_INPUT_ACTION = "run_intake_without_repeating_bootstrap_questions"
REQUIRED_FALSE_CONTINUATION_FIELDS = (
    "internal_anchor_required",
    "internal_validation_bundle_required",
    "independent_regeneration_required",
    "validation_profile_required",
    "exact_head_ci_required",
    "pr_review_required",
    "repository_maintenance_required",
)
CONTROLLED_RUNTIME_DOCS = (
    AGENTS_REL,
    README_REL,
    OVERRIDES_REL,
    FIRST_RUN_REL,
    PROJECT_INSTRUCTIONS_REL,
    CORE_BUNDLE_REL,
    PROTOCOLS_REL,
)
FORBIDDEN_ACTIVE_AUTHORIZATION_PATTERNS = (
    re.compile(r"continue only from the anchor's authorized target stage", re.IGNORECASE),
    re.compile(r"request or regenerate the required anchor", re.IGNORECASE),
    re.compile(r"A legal Manifest edge is not authorization", re.IGNORECASE),
    re.compile(r"BLOCKED_VALIDATION_PROFILE"),
    re.compile(r"no current Bundle may claim", re.IGNORECASE),
)
REQUIRED_ALIGNMENT_TERMS = (
    "active_runtime_role: optional_resume_checkpoint",
    "authorization_role: none",
    "full_transaction_implemented",
    "Stage quality determines progression",
    "final Project Gate boundary remains fail-closed",
    "evaluate_stage",
    "serialized Stage Result",
)
NEGATION_MARKERS = (
    "do not",
    "don't",
    "must not",
    "never",
    "forbidden",
    "prohibited",
    "not allowed",
    "نباید",
    "ممنوع",
)


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(root: Path, relative: Path) -> dict[str, Any]:
    try:
        value = json.loads((root / relative).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {relative.as_posix()}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {relative.as_posix()}: line {exc.lineno}, column {exc.colno}") from exc
    require(isinstance(value, dict), f"{relative.as_posix()} must contain a JSON object")
    return value


def read_text(root: Path, relative: Path) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {relative.as_posix()}") from exc


def ordered_ids(items: Any, *, id_key: str, field_name: str) -> list[str]:
    require(isinstance(items, list), f"{field_name} must be an array")
    result: list[str] = []
    for index, item in enumerate(items):
        require(isinstance(item, dict), f"{field_name}[{index}] must be an object")
        value = item.get(id_key)
        require(isinstance(value, str) and value, f"{field_name}[{index}].{id_key} must be non-empty")
        result.append(value)
    require(len(result) == len(set(result)), f"{field_name} contains duplicate identities")
    return result


def _historical_section(section: str) -> bool:
    lowered = section.lower()
    return any(term in lowered for term in ("historical", "history", "archive", "legacy evidence"))


def _negated(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in NEGATION_MARKERS)


def reject_active_shortcuts(label: str, text: str) -> None:
    """Reject active shortcuts while accepting prohibitions and historical quotations."""
    section = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip()
        if not stripped or stripped.startswith(">") or _historical_section(section):
            continue
        normalized = stripped.replace("`", "")
        if re.search(r"/intake\s*→\s*/decompose", normalized, re.IGNORECASE) and not _negated(normalized):
            raise ValidationError(f"contradictory active instruction in {label}: {stripped!r}")
        if re.search(r"\bskip(?:ping)?\s+/research\b", normalized, re.IGNORECASE) and not _negated(normalized):
            raise ValidationError(f"contradictory active instruction in {label}: {stripped!r}")
        if re.search(r"do not run\s+/project-gate-export", normalized, re.IGNORECASE):
            raise ValidationError(f"contradictory active instruction in {label}: {stripped!r}")


def reject_authorization_patterns(label: str, text: str) -> None:
    for pattern in FORBIDDEN_ACTIVE_AUTHORIZATION_PATTERNS:
        match = pattern.search(text)
        if match:
            raise ValidationError(f"contradictory active instruction in {label}: {match.group(0)!r}")


def validate_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    bootstrap = load_json(root, BOOTSTRAP_REL)
    schema = load_json(root, SCHEMA_REL)
    pipeline = load_json(root, PIPELINE_REL)
    alignment = read_text(root, ALIGNMENT_REL)
    docs = {path: read_text(root, path) for path in CONTROLLED_RUNTIME_DOCS}
    status = read_text(root, STATUS_REL)

    schema_errors = sorted(Draft202012Validator(schema).iter_errors(bootstrap), key=lambda item: list(item.absolute_path))
    require(not schema_errors, f"bootstrap schema violation: {schema_errors[0].message if schema_errors else 'unknown'}")
    require(bootstrap["contract_id"] == EXPECTED_CONTRACT_ID, "wrong bootstrap contract_id")
    require(bootstrap["contract_version"] == EXPECTED_CONTRACT_VERSION, "wrong bootstrap contract_version")
    require(bootstrap["owner_repository"] == EXPECTED_OWNER, "wrong bootstrap owner_repository")

    activation = bootstrap["activation"]
    require(activation["mode"] == "new_architect_run", "wrong activation mode")
    require(activation["accepted_triggers"] == EXPECTED_TRIGGERS, "canonical trigger policy drift")
    require(ordered_ids(activation["preconditions"], id_key="precondition_id", field_name="activation.preconditions") == EXPECTED_PRECONDITION_IDS, "bootstrap precondition identity/order drift")
    input_rule = bootstrap["input_present_behavior"]["trigger_with_screenshot_or_section_description"]
    require(input_rule["action_id"] == EXPECTED_INPUT_ACTION, "wrong screenshot-present action")
    routing = bootstrap["routing_rules"]
    require(set(routing) == set(EXPECTED_ROUTING_ACTIONS), "routing rule identity drift")
    for key, action_id in EXPECTED_ROUTING_ACTIONS.items():
        require(routing[key]["action_id"] == action_id, f"wrong routing action for {key}")
    require(ordered_ids(bootstrap["before_input_forbidden"], id_key="operation_id", field_name="before_input_forbidden") == EXPECTED_FORBIDDEN_IDS, "forbidden operation identity/order drift")

    continuation = pipeline.get("normal_run_continuation")
    require(isinstance(continuation, dict), "Manifest missing normal_run_continuation")
    require(continuation.get("model") == "quality_driven", "pipeline continuation model drift")
    require(continuation.get("continuation_authority") == "scripts/architect_quality_runtime.py#evaluate_stage", "canonical evaluator authority drift")
    require(continuation.get("serialized_stage_result_authorizes") is False, "serialized Stage Result must not authorize")
    for field in REQUIRED_FALSE_CONTINUATION_FIELDS:
        require(continuation.get(field) is False, f"normal_run_continuation.{field} must be false")

    stages = pipeline.get("project_execution_stages")
    require(isinstance(stages, list) and len(stages) == 12, "Manifest must preserve 12 mandatory Stages")
    stage_ids = [stage.get("stage_id") for stage in stages]
    require(len(stage_ids) == len(set(stage_ids)), "duplicate Stage identity")
    require(all(stage.get("mandatory") is True for stage in stages), "all project Stages must remain mandatory")
    for index, stage in enumerate(stages):
        require(isinstance(stage.get("required_quality_checks"), list) and stage["required_quality_checks"], f"{stage.get('stage_id')} missing finite required checks")
        require(len(stage["required_quality_checks"]) == len(set(stage["required_quality_checks"])), f"{stage.get('stage_id')} duplicate checks")
        if index < len(stages) - 1:
            require(stage.get("next_stage") == stages[index + 1].get("stage_id"), f"illegal successor at {stage.get('stage_id')}")
    require(stages[-1].get("next_stage") is None, "terminal Stage must have no successor")

    initial = bootstrap["initial_sequence"]
    require(initial == stage_ids[: len(initial)], "bootstrap initial_sequence differs from Manifest prefix")
    require(initial == ["/intake", "/research", "/decompose"], "mandatory /research missing")
    require(bootstrap["first_stage"] == "/intake", "bootstrap first Stage drift")
    final_stage = pipeline["final_project_gate_export_stage"]
    require(final_stage == stage_ids[-1] == "/project-gate-export", "terminal Project Gate identity drift")
    require(bootstrap["final_project_gate_instruction"]["stage_id"] == final_stage, "bootstrap final Stage drift")
    require(bootstrap["final_project_gate_instruction"]["statement_lines"][0] == "Run /project-gate-export.", "final Project Gate instruction must be positive")

    for term in REQUIRED_ALIGNMENT_TERMS:
        require(term in alignment, f"Alignment Contract missing required term: {term}")
    manifest_ref = BOOTSTRAP_REL.as_posix()
    sequence_text = " → ".join(initial)
    input_statement = input_rule["statement"]
    for relative, document in docs.items():
        reject_active_shortcuts(relative.as_posix(), document)
        reject_authorization_patterns(relative.as_posix(), document)
        require("/research" in document, f"{relative} must preserve /research")
        require("/project-gate-export" in document, f"{relative} must preserve terminal export")
    require(manifest_ref in docs[AGENTS_REL], "AGENTS.md must reference bootstrap Manifest")
    require(manifest_ref in docs[README_REL], "README.md must reference bootstrap Manifest")
    require(manifest_ref in docs[FIRST_RUN_REL], "First Run Guide must reference bootstrap Manifest")
    require(sequence_text in docs[AGENTS_REL], "AGENTS.md initial sequence drift")
    require(sequence_text in docs[README_REL], "README initial sequence drift")
    require(sequence_text in docs[FIRST_RUN_REL], "First Run initial sequence drift")
    require(input_statement in docs[FIRST_RUN_REL], "First Run screenshot routing drift")
    require("Do not skip `/research`." in docs[AGENTS_REL], "AGENTS must explicitly prohibit /research skipping")

    require("pull_request: 29" in status and "merge_commit: be9bdea9ae246b1587043f2582c1a950ea2a6ec5" in status and "merge_status: merged" in status, "STATUS.md lost PR #29 merged evidence")
    require("audit_status: merged_observed_not_independently_accepted" in status, "STATUS.md lost ARCH-02 audit status")
    require("pull_request: 30" in status and "reviewed_head_sha: 51e21a2d57adc8086a0d320038aaa80993b2318a" in status, "STATUS.md lost PR #30 evidence")
    require("pull_request: 35" in status and "merge_commit: b433966e44bb89c7949a709728b201ce1d37ac45" in status and "merge_status: merged" in status, "STATUS.md does not reconcile merged PR #35")

    return {
        "continuation_model": continuation["model"],
        "initial_sequence": sequence_text,
        "recognized_triggers": len(EXPECTED_TRIGGERS),
        "forbidden_operations": len(EXPECTED_FORBIDDEN_IDS),
        "final_stage": final_stage,
        "controlled_runtime_docs": len(CONTROLLED_RUNTIME_DOCS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    result = validate_repository(args.root)
    print("Architect bootstrap semantic validation passed.")
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as exc:
        print(f"Architect bootstrap semantic validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
