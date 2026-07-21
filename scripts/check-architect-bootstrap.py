#!/usr/bin/env python3
"""Fail-closed validation for the EV4 Architect conversation bootstrap contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

BOOTSTRAP_REL = Path("manifests/architect-conversation-bootstrap.v1.json")
SCHEMA_REL = Path("schemas/architect-conversation-bootstrap.v1.schema.json")
PIPELINE_REL = Path("manifests/architect-pipeline-manifest.v1.json")
AGENTS_REL = Path("AGENTS.md")
README_REL = Path("README.md")
STATUS_REL = Path("STATUS.md")
FIRST_RUN_REL = Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md")

RESPONSE_START = "<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_START -->"
RESPONSE_END = "<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_END -->"
ROUTING_START = "<!-- EV4_ARCHITECT_BOOTSTRAP_ROUTING_START -->"
ROUTING_END = "<!-- EV4_ARCHITECT_BOOTSTRAP_ROUTING_END -->"
README_START = "<!-- EV4_ARCHITECT_README_QUICK_START_START -->"
README_END = "<!-- EV4_ARCHITECT_README_QUICK_START_END -->"
FIRST_RUN_FAST_START = "<!-- EV4_ARCHITECT_FIRST_RUN_FAST_START_START -->"
FIRST_RUN_FAST_END = "<!-- EV4_ARCHITECT_FIRST_RUN_FAST_START_END -->"
FINAL_GATE_START = "<!-- EV4_ARCHITECT_FINAL_PROJECT_GATE_START -->"
FINAL_GATE_END = "<!-- EV4_ARCHITECT_FINAL_PROJECT_GATE_END -->"

EXPECTED_CONTRACT_ID = "ev4-architect-conversation-bootstrap"
EXPECTED_CONTRACT_VERSION = "1.1.0"
EXPECTED_OWNER = "rezahh107/EV4-Architect-Repo"
EXPECTED_ACTIVATION_MODE = "new_architect_run"
EXPECTED_INITIAL_SEQUENCE = ["/intake", "/research", "/decompose"]
EXPECTED_FINAL_STAGE = "/project-gate-export"
EXPECTED_TRIGGER_POLICY_ID = "ev4-architect-bootstrap-trigger-policy"
EXPECTED_TRIGGER_POLICY_VERSION = "1.0.0"
EXPECTED_TRIGGERS = [
    "شروع",
    "شروع کن",
    "شروع سکشن جدید",
    "start",
    "begin",
    "start a new section",
]
EXPECTED_PRECONDITION_IDS = [
    "repository_instructions_loaded",
    "no_active_architect_run",
    "no_valid_stage_anchor",
    "no_project_input",
]
EXPECTED_FORBIDDEN_IDS = [
    "run_any_pipeline_stage",
    "recommend_architecture",
    "produce_elementor_tree",
    "invent_exact_values",
    "claim_stage_anchor",
    "claim_builder_or_production_readiness",
]
EXPECTED_ROUTING_ACTIONS = {
    "valid_stage_anchor_present": "continue_from_anchor_without_restarting",
    "latest_stage_output_without_valid_anchor": "request_or_regenerate_required_anchor",
    "explicit_repository_maintenance_request": "repository_maintenance_mode_not_project_run",
}
EXPECTED_INPUT_ACTION = "run_intake_without_repeating_bootstrap_questions"

STALE_OR_CONTRADICTORY_PATTERNS = (
    re.compile(r"Start with /intake and /decompose only\.", re.IGNORECASE),
    re.compile(r"/intake\s*→\s*/decompose"),
    re.compile(r"Do not run\s+`?/project-gate-export`?", re.IGNORECASE),
    re.compile(r"skip\s+`?/research`?", re.IGNORECASE),
)


class ValidationError(RuntimeError):
    """Raised when bootstrap validation fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(root: Path, relative: Path) -> dict[str, Any]:
    path = root / relative
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {relative.as_posix()}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"invalid JSON in {relative.as_posix()}: line {exc.lineno}, column {exc.colno}"
        ) from exc
    require(isinstance(data, dict), f"{relative.as_posix()} must contain a JSON object")
    return data


def read_text(root: Path, relative: Path) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {relative.as_posix()}") from exc


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


def extract_marked_region(
    document: str,
    *,
    start_marker: str,
    end_marker: str,
    source: Path,
) -> str:
    require(
        document.count(start_marker) == 1 and document.count(end_marker) == 1,
        f"{source.as_posix()} must contain exactly one {start_marker} / {end_marker} pair",
    )
    start = document.index(start_marker) + len(start_marker)
    end = document.index(end_marker, start)
    require(start < end, f"{source.as_posix()} has reversed controlled-section markers")
    return normalize_text(document[start:end])


def extract_marked_fenced_text(
    document: str,
    *,
    start_marker: str,
    end_marker: str,
    source: Path,
) -> str:
    region = extract_marked_region(
        document,
        start_marker=start_marker,
        end_marker=end_marker,
        source=source,
    )
    lines = region.splitlines()
    require(
        len(lines) >= 3 and lines[0].strip() == "```text" and lines[-1].strip() == "```",
        f"{source.as_posix()} controlled text must use exactly one outer ```text fence",
    )
    return normalize_text("\n".join(lines[1:-1]))


def schema_error_message(error: Any) -> str:
    path = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"bootstrap schema violation at {path}: {error.message}"


def validate_schema(bootstrap: dict[str, Any], schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(bootstrap), key=lambda item: list(item.absolute_path))
    require(not errors, schema_error_message(errors[0]) if errors else "bootstrap schema validation failed")


def ordered_ids(items: Any, *, id_key: str, field_name: str) -> list[str]:
    require(isinstance(items, list), f"{field_name} must be an array")
    result: list[str] = []
    for index, item in enumerate(items):
        require(isinstance(item, dict), f"{field_name}[{index}] must be an object")
        value = item.get(id_key)
        require(isinstance(value, str) and value, f"{field_name}[{index}].{id_key} must be a non-empty string")
        result.append(value)
    require(len(result) == len(set(result)), f"{field_name} contains duplicate stable identities")
    return result


def render_agents_routing(bootstrap: dict[str, Any]) -> str:
    input_rule = bootstrap["input_present_behavior"]["trigger_with_screenshot_or_section_description"]
    routing = bootstrap["routing_rules"]
    lines = [
        "trigger_with_screenshot_or_section_description:",
        input_rule["statement"],
        "",
        "valid_stage_anchor_present:",
        routing["valid_stage_anchor_present"]["statement"],
        "",
        "latest_stage_output_without_valid_anchor:",
        routing["latest_stage_output_without_valid_anchor"]["statement"],
        "",
        "explicit_repository_maintenance_request:",
        routing["explicit_repository_maintenance_request"]["statement"],
        "",
        "before_input_forbidden:",
    ]
    for item in bootstrap["before_input_forbidden"]:
        lines.append(f"- {item['operation_id']}: {item['statement']}")
    return "\n".join(lines)


def render_final_gate(bootstrap: dict[str, Any]) -> str:
    return "\n".join(bootstrap["final_project_gate_instruction"]["statement_lines"])


def reject_contradictions(sections: Iterable[tuple[str, str]]) -> None:
    for label, text in sections:
        for pattern in STALE_OR_CONTRADICTORY_PATTERNS:
            match = pattern.search(text)
            if match:
                phrase = match.group(0)
                if phrase.lower().startswith("skip") and "Do not skip" in text:
                    continue
                raise ValidationError(
                    f"contradictory instruction in controlled section {label}: {phrase!r}"
                )


def validate_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    bootstrap = load_json(root, BOOTSTRAP_REL)
    schema = load_json(root, SCHEMA_REL)
    pipeline = load_json(root, PIPELINE_REL)
    agents = read_text(root, AGENTS_REL)
    readme = read_text(root, README_REL)
    status = read_text(root, STATUS_REL)
    first_run = read_text(root, FIRST_RUN_REL)

    validate_schema(bootstrap, schema)

    require(bootstrap["contract_id"] == EXPECTED_CONTRACT_ID, "wrong bootstrap contract_id")
    require(bootstrap["contract_version"] == EXPECTED_CONTRACT_VERSION, "wrong bootstrap contract_version")
    require(bootstrap["owner_repository"] == EXPECTED_OWNER, "wrong bootstrap owner_repository")

    activation = bootstrap["activation"]
    require(activation["mode"] == EXPECTED_ACTIVATION_MODE, "wrong bootstrap activation.mode")
    require(activation["trigger_policy_id"] == EXPECTED_TRIGGER_POLICY_ID, "wrong trigger policy identity")
    require(
        activation["trigger_policy_version"] == EXPECTED_TRIGGER_POLICY_VERSION,
        "wrong trigger policy version",
    )
    triggers = activation["accepted_triggers"]
    require(all(isinstance(item, str) and item for item in triggers), "all canonical triggers must be non-empty strings")
    require(triggers == EXPECTED_TRIGGERS, "accepted_triggers must exactly match the canonical trigger policy")
    require(len(triggers) == len(set(triggers)), "accepted_triggers contains duplicates")
    require(
        ordered_ids(activation["preconditions"], id_key="precondition_id", field_name="activation.preconditions")
        == EXPECTED_PRECONDITION_IDS,
        "activation.preconditions must preserve every canonical precondition identity and order",
    )

    input_rule = bootstrap["input_present_behavior"]["trigger_with_screenshot_or_section_description"]
    require(input_rule["action_id"] == EXPECTED_INPUT_ACTION, "wrong screenshot-present bootstrap action")
    routing = bootstrap["routing_rules"]
    require(set(routing) == set(EXPECTED_ROUTING_ACTIONS), "routing_rules keys differ from the canonical set")
    for key, action_id in EXPECTED_ROUTING_ACTIONS.items():
        require(routing[key]["action_id"] == action_id, f"wrong routing action for {key}")

    require(
        ordered_ids(bootstrap["before_input_forbidden"], id_key="operation_id", field_name="before_input_forbidden")
        == EXPECTED_FORBIDDEN_IDS,
        "before_input_forbidden must preserve every canonical operation identity and order",
    )

    stages = pipeline.get("project_execution_stages")
    require(isinstance(stages, list) and len(stages) >= 4, "pipeline manifest must define project stages")
    initial_stages = stages[:3]
    initial_ids = [stage.get("stage_id") if isinstance(stage, dict) else None for stage in initial_stages]
    require(initial_ids == EXPECTED_INITIAL_SEQUENCE, "pipeline initial sequence is not canonical")
    for stage in initial_stages:
        require(stage.get("mandatory") is True, f"initial stage {stage.get('stage_id')} must remain mandatory")
    require(bootstrap["initial_sequence"] == initial_ids, "bootstrap initial_sequence differs from pipeline manifest")
    require(bootstrap["first_stage"] == initial_ids[0], "bootstrap first_stage differs from pipeline manifest")

    final_stage = stages[-1]
    require(isinstance(final_stage, dict), "final pipeline stage must be an object")
    require(final_stage.get("stage_id") == EXPECTED_FINAL_STAGE, "pipeline is missing the final Project Gate stage")
    require(final_stage.get("mandatory") is True, "final Project Gate stage must remain mandatory")
    require(final_stage.get("next_stage") is None, "final Project Gate stage must terminate the project sequence")
    require(
        pipeline.get("final_project_gate_export_stage") == EXPECTED_FINAL_STAGE,
        "pipeline final_project_gate_export_stage is not canonical",
    )
    require(
        bootstrap["final_project_gate_instruction"]["stage_id"] == EXPECTED_FINAL_STAGE,
        "bootstrap final Project Gate stage identity is not canonical",
    )

    response = bootstrap["bootstrap_response"]
    response_agents = extract_marked_fenced_text(
        agents, start_marker=RESPONSE_START, end_marker=RESPONSE_END, source=AGENTS_REL
    )
    response_first_run = extract_marked_fenced_text(
        first_run, start_marker=RESPONSE_START, end_marker=RESPONSE_END, source=FIRST_RUN_REL
    )
    require(response_agents == normalize_text(response), "AGENTS.md bootstrap response differs byte-for-byte")
    require(response_first_run == normalize_text(response), "First Run bootstrap response differs byte-for-byte")

    expected_routing = normalize_text(render_agents_routing(bootstrap))
    actual_routing = extract_marked_fenced_text(
        agents, start_marker=ROUTING_START, end_marker=ROUTING_END, source=AGENTS_REL
    )
    require(actual_routing == expected_routing, "AGENTS.md routing block differs from the machine-readable contract")

    expected_gate = normalize_text(render_final_gate(bootstrap))
    actual_gate_region = extract_marked_region(
        first_run, start_marker=FINAL_GATE_START, end_marker=FINAL_GATE_END, source=FIRST_RUN_REL
    )
    gate_fences = re.findall(r"```text\n(.*?)\n```", actual_gate_region, flags=re.DOTALL)
    require(len(gate_fences) == 1, "Final Project Gate section must contain exactly one ```text instruction block")
    require(normalize_text(gate_fences[0]) == expected_gate, "Final Project Gate instruction is not the positive canonical instruction")
    require(expected_gate.splitlines()[0] == "Run /project-gate-export.", "canonical Project Gate instruction must positively run the stage")

    manifest_ref = BOOTSTRAP_REL.as_posix()
    for label, document in (("AGENTS.md", agents), ("README.md", readme), ("EV4_FIRST_RUN_GUIDE.md", first_run)):
        require(manifest_ref in document, f"{label} must reference the canonical bootstrap manifest")

    sequence_text = " → ".join(EXPECTED_INITIAL_SEQUENCE)
    require(sequence_text in agents, "AGENTS.md must show the canonical initial sequence")
    require(sequence_text in readme, "README.md must show the canonical initial sequence")
    require(sequence_text in first_run, "First Run guide must show the canonical initial sequence")
    require("Do not skip `/research`." in agents, "AGENTS.md must explicitly prohibit skipping /research")

    readme_controlled = extract_marked_region(
        readme, start_marker=README_START, end_marker=README_END, source=README_REL
    )
    first_run_fast = extract_marked_region(
        first_run, start_marker=FIRST_RUN_FAST_START, end_marker=FIRST_RUN_FAST_END, source=FIRST_RUN_REL
    )
    input_statement = input_rule["statement"]
    require(input_statement in readme_controlled, "README Quick Start does not match screenshot-present behavior")
    require(input_statement in first_run_fast, "First Run Fast Start does not match screenshot-present behavior")

    reject_contradictions(
        (
            (
                "AGENTS bootstrap",
                extract_marked_region(
                    agents, start_marker=RESPONSE_START, end_marker=ROUTING_END, source=AGENTS_REL
                ),
            ),
            ("README Quick Start", readme_controlled),
            ("First Run Fast Start", first_run_fast),
            ("First Run Final Project Gate", actual_gate_region),
        )
    )

    ordered_sections = ["## After /intake", "## After /research", "## After /decompose"]
    positions = [first_run.find(section) for section in ordered_sections]
    require(all(position >= 0 for position in positions), "First Run guide is missing an initial continuation section")
    require(positions == sorted(positions), "First Run continuation sections are out of canonical order")

    require(
        "merge_commit: be9bdea9ae246b1587043f2582c1a950ea2a6ec5" in status
        and "pull_request: 29" in status
        and "merge_status: merged" in status,
        "STATUS.md does not reconcile PR #29 with authoritative merged state",
    )
    require(
        "scope_gate: insufficient_evidence" in status
        and "pull_request: 30" in status
        and "reviewed_head_sha: 51e21a2d57adc8086a0d320038aaa80993b2318a" in status,
        "STATUS.md does not preserve the bounded PR #30 scope-gate record",
    )
    require(
        "keep it unmerged" not in status and "repair_pr_merge_status: unmerged" not in status,
        "STATUS.md still contains stale PR #29 unmerged state",
    )

    return {
        "initial_sequence": sequence_text,
        "recognized_triggers": len(triggers),
        "forbidden_operations": len(EXPECTED_FORBIDDEN_IDS),
        "final_stage": EXPECTED_FINAL_STAGE,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to validate.",
    )
    args = parser.parse_args(argv)
    result = validate_repository(args.root)
    print("Architect bootstrap semantic validation passed.")
    print(f"Initial sequence: {result['initial_sequence']}")
    print(f"Recognized triggers: {result['recognized_triggers']}")
    print(f"Stable forbidden operations: {result['forbidden_operations']}")
    print(f"Final stage: {result['final_stage']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as exc:
        print(f"Architect bootstrap semantic validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
