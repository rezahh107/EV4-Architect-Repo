#!/usr/bin/env python3
"""Fail-closed validation for the EV4 Architect bootstrap and runtime authority."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

BOOTSTRAP_REL = Path("manifests/architect-conversation-bootstrap.v1.json")
SCHEMA_REL = Path("schemas/architect-conversation-bootstrap.v1.schema.json")
PIPELINE_REL = Path("manifests/architect-pipeline-manifest.v1.json")
ALIGNMENT_REL = Path("contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md")
EXPECTED_TRIGGERS = ["شروع", "شروع کن", "شروع سکشن جدید", "start", "begin", "start a new section"]
EXPECTED_PRECONDITIONS = ["repository_instructions_loaded", "no_active_architect_run", "no_resumable_stage_result", "no_project_input"]
EXPECTED_ROUTING = {
    "resumable_stage_result_present": "continue_from_stage_result_without_restarting",
    "latest_stage_output_without_stage_result": "validate_or_reconstruct_stage_result",
    "explicit_repository_maintenance_request": "repository_maintenance_mode_not_project_run",
}
REQUIRED_ALIGNMENT_TERMS = [
    "active_runtime_role: optional_resume_checkpoint",
    "authorization_role: none",
    "full_transaction_implemented",
    "Stage quality determines progression",
    "final Project Gate boundary remains fail-closed",
]


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{relative} must contain an object")
    return value


def validate_repository(root: Path) -> dict[str, Any]:
    bootstrap = load_json(root, BOOTSTRAP_REL)
    schema = load_json(root, SCHEMA_REL)
    pipeline = load_json(root, PIPELINE_REL)
    alignment = (root / ALIGNMENT_REL).read_text(encoding="utf-8")

    schema_errors = sorted(Draft202012Validator(schema).iter_errors(bootstrap), key=lambda e: list(e.absolute_path))
    require(not schema_errors, f"bootstrap schema violation: {schema_errors[0].message if schema_errors else 'unknown'}")
    require(bootstrap["contract_version"] == "1.2.0", "wrong bootstrap version")
    require(bootstrap["activation"]["accepted_triggers"] == EXPECTED_TRIGGERS, "trigger drift")
    preconditions = [row["precondition_id"] for row in bootstrap["activation"]["preconditions"]]
    require(preconditions == EXPECTED_PRECONDITIONS, "precondition drift")
    require(set(bootstrap["routing_rules"]) == set(EXPECTED_ROUTING), "routing identity drift")
    for key, action_id in EXPECTED_ROUTING.items():
        require(bootstrap["routing_rules"][key]["action_id"] == action_id, f"routing action drift: {key}")

    model = pipeline.get("normal_run_continuation", {})
    require(model.get("model") == "quality_driven", "pipeline is not quality-driven")
    for field in (
        "internal_anchor_required",
        "internal_validation_bundle_required",
        "independent_regeneration_required",
        "validation_profile_required",
        "exact_head_ci_required",
        "pr_review_required",
        "repository_maintenance_required",
    ):
        require(model.get(field) is False, f"normal_run_continuation.{field} must be false")

    stages = pipeline["project_execution_stages"]
    initial = [row["stage_id"] for row in stages[:3]]
    require(initial == bootstrap["initial_sequence"], "bootstrap sequence differs from Manifest")
    require(initial == ["/intake", "/research", "/decompose"], "/research must remain mandatory")
    require(stages[-1]["stage_id"] == pipeline["final_project_gate_export_stage"], "terminal Stage drift")
    for term in REQUIRED_ALIGNMENT_TERMS:
        require(term in alignment, f"alignment contract missing term: {term}")

    return {
        "continuation_model": model["model"],
        "initial_sequence": " → ".join(initial),
        "final_stage": pipeline["final_project_gate_export_stage"],
        "recognized_triggers": len(EXPECTED_TRIGGERS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(validate_repository(args.root.resolve()), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Architect bootstrap validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
