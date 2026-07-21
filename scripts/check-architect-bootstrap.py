#!/usr/bin/env python3
"""Validate the EV4 Architect new-run bootstrap contract and documentation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = ROOT / "manifests" / "architect-conversation-bootstrap.v1.json"
PIPELINE_PATH = ROOT / "manifests" / "architect-pipeline-manifest.v1.json"
AGENTS_PATH = ROOT / "AGENTS.md"
README_PATH = ROOT / "README.md"
FIRST_RUN_PATH = ROOT / "release" / "EV4_PROJECT_RELEASE_PACK_v1" / "EV4_FIRST_RUN_GUIDE.md"

START_MARKER = "<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_START -->"
END_MARKER = "<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_END -->"
STALE_FIRST_RUN_TEXT = "Start with /intake and /decompose only."


class ValidationError(RuntimeError):
    """Raised when the bootstrap contract is inconsistent."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"invalid JSON in {path.relative_to(ROOT)}: line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path.relative_to(ROOT)}") from exc


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


def extract_marked_fenced_text(document: str, *, source: Path) -> str:
    if document.count(START_MARKER) != 1 or document.count(END_MARKER) != 1:
        raise ValidationError(
            f"{source.relative_to(ROOT)} must contain exactly one bootstrap response marker pair"
        )

    start = document.index(START_MARKER) + len(START_MARKER)
    end = document.index(END_MARKER, start)
    block = document[start:end].strip()
    lines = block.splitlines()

    if len(lines) < 3 or lines[0].strip() != "```text" or lines[-1].strip() != "```":
        raise ValidationError(
            f"{source.relative_to(ROOT)} bootstrap response must be inside one ```text fence"
        )

    return normalize_text("\n".join(lines[1:-1]))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def main() -> int:
    bootstrap = load_json(BOOTSTRAP_PATH)
    pipeline = load_json(PIPELINE_PATH)
    agents = read_text(AGENTS_PATH)
    readme = read_text(README_PATH)
    first_run = read_text(FIRST_RUN_PATH)

    stages = pipeline.get("project_execution_stages")
    require(isinstance(stages, list) and len(stages) >= 3, "pipeline manifest must define at least three stages")

    initial_pipeline_sequence: list[str] = []
    for index, stage in enumerate(stages[:3], start=1):
        require(isinstance(stage, dict), f"pipeline stage {index} must be an object")
        stage_id = stage.get("stage_id")
        require(isinstance(stage_id, str) and stage_id.startswith("/"), f"pipeline stage {index} has invalid stage_id")
        require(stage.get("mandatory") is True, f"initial pipeline stage {stage_id} must remain mandatory")
        initial_pipeline_sequence.append(stage_id)

    configured_sequence = bootstrap.get("initial_sequence")
    require(
        configured_sequence == initial_pipeline_sequence,
        "bootstrap initial_sequence must exactly match the first three mandatory pipeline stages",
    )
    require(
        bootstrap.get("first_stage") == initial_pipeline_sequence[0],
        "bootstrap first_stage must match the first pipeline stage",
    )

    activation = bootstrap.get("activation")
    require(isinstance(activation, dict), "bootstrap activation must be an object")
    triggers = activation.get("accepted_triggers")
    require(isinstance(triggers, list) and "شروع" in triggers, "bootstrap triggers must include شروع")
    require(len(triggers) == len(set(triggers)), "bootstrap triggers must not contain duplicates")

    response = bootstrap.get("bootstrap_response")
    require(isinstance(response, str) and response.strip(), "bootstrap_response must be a non-empty string")
    sequence_text = " → ".join(initial_pipeline_sequence)
    require(sequence_text in response, "bootstrap_response must display the manifest-derived initial sequence")

    manifest_ref = "manifests/architect-conversation-bootstrap.v1.json"
    require(manifest_ref in agents, "AGENTS.md must reference the canonical bootstrap manifest")
    require(manifest_ref in readme, "README.md must reference the canonical bootstrap manifest")
    require(manifest_ref in first_run, "EV4_FIRST_RUN_GUIDE.md must reference the canonical bootstrap manifest")

    require(
        extract_marked_fenced_text(agents, source=AGENTS_PATH) == normalize_text(response),
        "AGENTS.md bootstrap response differs from the canonical manifest",
    )
    require(
        extract_marked_fenced_text(first_run, source=FIRST_RUN_PATH) == normalize_text(response),
        "EV4_FIRST_RUN_GUIDE.md bootstrap response differs from the canonical manifest",
    )

    require(sequence_text in agents, "AGENTS.md must show the exact initial pipeline sequence")
    require(sequence_text in readme, "README.md must show the exact initial pipeline sequence")
    require(sequence_text in first_run, "EV4_FIRST_RUN_GUIDE.md must show the exact initial pipeline sequence")
    require("Do not skip `/research`." in agents, "AGENTS.md must explicitly forbid skipping /research")
    require(STALE_FIRST_RUN_TEXT not in first_run, "stale First Run instruction still skips /research")

    ordered_sections = ["## After /intake", "## After /research", "## After /decompose"]
    positions = [first_run.find(section) for section in ordered_sections]
    require(
        all(position >= 0 for position in positions),
        "First Run guide must document intake, research, and decompose continuations",
    )
    require(positions == sorted(positions), "First Run continuation sections are out of pipeline order")
    require("/project-gate-export" in first_run, "First Run guide must include the canonical final Project Gate stage")

    forbidden = bootstrap.get("before_input_forbidden")
    require(
        isinstance(forbidden, list) and len(forbidden) >= 5,
        "before_input_forbidden must define fail-closed boundaries",
    )

    print("Architect bootstrap contract validation passed.")
    print(f"Initial sequence: {sequence_text}")
    print(f"Recognized triggers: {len(triggers)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"Architect bootstrap contract validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
