"""Non-authorizing validation helpers for conversational Architect Stage Output."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from architect_quality_runtime import evaluate_run

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("manifests/architect-pipeline-manifest.v1.json")
BASE_SCHEMA_PATH = Path("schemas/ev4-architect-conversational-stage-output-base.v1.schema.json")
CONTRACT_ID = "ev4-architect-conversational-stage-output@1.0.0"
BASE_SCHEMA_ID = "ev4-architect-conversational-stage-output-base@1.0.0"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_authority(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _load(root / MANIFEST_PATH)
    schema = _load(root / BASE_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    if schema.get("$id") != BASE_SCHEMA_ID:
        raise ValueError("Conversational Stage Output base Schema identity mismatch")
    return manifest, schema


def stage_map(root: Path = ROOT) -> tuple[list[str], dict[str, dict[str, Any]]]:
    manifest, _ = load_authority(root)
    rows = manifest["project_execution_stages"]
    return [row["stage_id"] for row in rows], {row["stage_id"]: row for row in rows}


def validate_base_structure(output: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    _, schema = load_authority(root)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(output),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def validate_manifest_consistency(output: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    errors = validate_base_structure(output, root=root)
    _, stages = stage_map(root)
    stage_id = output.get("stage_id")
    stage = stages.get(stage_id)
    if stage is None:
        return [*errors, f"stage_id: unknown Manifest Stage {stage_id!r}"]
    if output.get("stage_version") != stage["stage_version"]:
        errors.append(
            f"stage_version: expected {stage['stage_version']} for {stage_id}, got {output.get('stage_version')!r}"
        )
    supplied = output.get("check_evidence")
    if isinstance(supplied, dict):
        expected = set(stage.get("required_quality_checks", []))
        actual = set(supplied)
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        if missing:
            errors.append(f"check_evidence: missing Manifest checks {missing}")
        if unknown:
            errors.append(f"check_evidence: unknown or cross-Stage checks {unknown}")
    return errors


def load_output_files(directory: Path, *, root: Path = ROOT) -> list[dict[str, Any]]:
    order, _ = stage_map(root)
    index = {stage_id: position for position, stage_id in enumerate(order)}
    outputs = [_load(path) for path in directory.glob("*.json")]
    if len(outputs) != len({item.get("stage_id") for item in outputs}):
        raise ValueError("Conversational Run fixture contains duplicate stage_id values")
    try:
        return sorted(outputs, key=lambda item: index[item["stage_id"]])
    except KeyError as exc:
        raise ValueError(f"Conversational Run fixture contains unknown Stage: {exc}") from exc


def validate_run_outputs(
    outputs: list[dict[str, Any]],
    *,
    root: Path = ROOT,
    require_terminal: bool = False,
    trusted_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    order, _ = stage_map(root)
    errors: list[str] = []
    for position, output in enumerate(outputs):
        errors.extend(
            f"{output.get('stage_id', position)}: {error}"
            for error in validate_manifest_consistency(output, root=root)
        )
    run_ids = {item.get("run_id") for item in outputs}
    if len(run_ids) != 1:
        errors.append("run: every Stage Output must use one exact run_id")
    actual = [item.get("stage_id") for item in outputs]
    expected = order if require_terminal else order[: len(actual)]
    if actual != expected:
        errors.append("run: mandatory Stage order mismatch")
    if errors:
        return {"status": "invalid", "errors": sorted(set(errors)), "results": []}
    return evaluate_run(
        outputs,
        root=root,
        require_terminal=require_terminal,
        trusted_context=trusted_context,
    )


def validate_repository_vectors(*, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    examples = sorted((root / "examples/conversational-stage-output").glob("*.json"))
    for path in examples:
        output = _load(path)
        errors.extend(f"{path.relative_to(root)}: {error}" for error in validate_manifest_consistency(output, root=root))

    prefinal_dir = root / "fixtures/conversational-run/valid/minimal-complete-run"
    prefinal = load_output_files(prefinal_dir, root=root)
    prefinal_result = validate_run_outputs(prefinal, root=root, require_terminal=False)
    errors.extend(prefinal_result.get("errors", []))
    if prefinal_result.get("status") == "valid":
        state = prefinal_result["run_state"]
        if state.get("current_stage") != "/project-gate-export":
            errors.append("run: valid Prefinal fixture must point to /project-gate-export")

    terminal_path = root / "fixtures/conversational-run/valid/terminal/project-gate-export.json"
    terminal = _load(terminal_path)
    errors.extend(
        f"{terminal_path.relative_to(root)}: {error}"
        for error in validate_manifest_consistency(terminal, root=root)
    )
    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "examples_checked": len(examples),
        "prefinal_stages_checked": len(prefinal),
        "terminal_structure_checked": True,
        "authority": {
            "contract": CONTRACT_ID,
            "base_schema": BASE_SCHEMA_ID,
            "continuation": "scripts/architect_quality_runtime.py#evaluate_stage",
        },
    }
