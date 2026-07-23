"""Non-authorizing validation helpers for conversational Architect Stage Output."""
from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from architect_quality_runtime import (
    CALLER_AUTHORITY_FIELDS,
    evaluate_run,
    load_authority as load_runtime_authority,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("manifests/architect-pipeline-manifest.v1.json")
BASE_SCHEMA_PATH = Path("schemas/architect-conversational-stage-output-base.v1.schema.json")
CONTRACT_PATH = Path("contracts/ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1.md")
RELEASE_UPLOAD_SET_PATH = Path(
    "release/EV4_PROJECT_RELEASE_PACK_v1/CONVERSATIONAL_STAGE_OUTPUT_UPLOAD_SET.v1.json"
)
CONTRACT_ID = "ev4-architect-conversational-stage-output@1.0.0"
BASE_SCHEMA_ID = "ev4-architect-conversational-stage-output-base@1.0.0"
RELEASE_UPLOAD_SET_ID = "ev4-architect-conversational-stage-output-upload-set@1.0.0"
CORE_RELEASE_PATHS = frozenset(
    {
        "release/EV4_PROJECT_RELEASE_PACK_v1/PROJECT_INSTRUCTIONS_FINAL.md",
        "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CORE_CONTRACTS_BUNDLE.md",
        "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_STAGE_PROTOCOLS_BUNDLE.md",
        "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_EXAMPLES_AND_CALIBRATION_BUNDLE.md",
        "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md",
    }
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _base_schema_authority_fields(schema: dict[str, Any]) -> set[str]:
    values = schema.get("$defs", {}).get("caller_authority_field", {}).get("enum")
    if not isinstance(values, list) or not values or any(not isinstance(item, str) for item in values):
        raise ValueError("Conversational Base Schema must declare caller authority fields")
    if len(values) != len(set(values)):
        raise ValueError("Conversational Base Schema caller authority fields must be unique")
    return set(values)


def load_authority(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _load(root / MANIFEST_PATH)
    schema = _load(root / BASE_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    if schema.get("$id") != BASE_SCHEMA_ID:
        raise ValueError("Conversational Stage Output base Schema identity mismatch")
    runtime_manifest, _ = load_runtime_authority(root)
    if manifest != runtime_manifest:
        raise ValueError("Conversational and Runtime Pipeline Manifest views differ")
    schema_fields = _base_schema_authority_fields(schema)
    if schema_fields != CALLER_AUTHORITY_FIELDS:
        missing = sorted(CALLER_AUTHORITY_FIELDS - schema_fields)
        extra = sorted(schema_fields - CALLER_AUTHORITY_FIELDS)
        raise ValueError(
            f"Conversational caller authority boundary drift; missing={missing}, extra={extra}"
        )
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


def repository_trusted_context(*, root: Path = ROOT) -> dict[str, Any]:
    scripts = root / "scripts"
    import sys

    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    base = importlib.import_module("architect_project_gate_exporter.base")
    sha = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    ref = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if not base.SHA40.fullmatch(sha):
        raise ValueError("Exact repository checkout commit SHA is required")
    return {
        "producer_provenance": {
            "repository": base.REPOSITORY,
            "ref": ref or "exact-repository-checkout",
            "commit_sha": sha,
        }
    }


def validate_release_upload_set(*, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    path = root / RELEASE_UPLOAD_SET_PATH
    try:
        upload_set = _load(path)
    except Exception as exc:
        return {
            "status": "invalid",
            "errors": [f"{RELEASE_UPLOAD_SET_PATH}: {type(exc).__name__}: {exc}"],
            "stages_exposed": 0,
        }

    if upload_set.get("upload_set_id") != RELEASE_UPLOAD_SET_ID:
        errors.append("release upload set identity mismatch")
    if upload_set.get("manifest_path") != MANIFEST_PATH.as_posix():
        errors.append("release upload set must expose the exact Pipeline Manifest path")

    contract = upload_set.get("contract", {})
    if contract.get("path") != CONTRACT_PATH.as_posix() or contract.get("identity") != CONTRACT_ID:
        errors.append("release upload set Contract identity mismatch")
    base_schema = upload_set.get("base_schema", {})
    if base_schema.get("path") != BASE_SCHEMA_PATH.as_posix() or base_schema.get("identity") != BASE_SCHEMA_ID:
        errors.append("release upload set Base Schema identity mismatch")

    example_paths = upload_set.get("example_paths")
    minimum_paths = upload_set.get("minimum_upload_paths")
    if not isinstance(example_paths, list) or not example_paths:
        errors.append("release upload set requires explicit conversational example paths")
        example_paths = []
    if not isinstance(minimum_paths, list):
        errors.append("release minimum upload paths must be a unique list")
        minimum_paths = []
    elif any(not isinstance(item, str) or not item for item in minimum_paths):
        errors.append("release minimum upload paths must contain non-empty strings")
        minimum_paths = [
            item for item in minimum_paths if isinstance(item, str) and item
        ]
    elif len(minimum_paths) != len(set(minimum_paths)):
        errors.append("release minimum upload paths must be a unique list")

    minimum_path_set = set(minimum_paths)
    required_non_core_paths = {
        MANIFEST_PATH.as_posix(),
        CONTRACT_PATH.as_posix(),
        BASE_SCHEMA_PATH.as_posix(),
        *example_paths,
    }
    missing_core_paths = sorted(CORE_RELEASE_PATHS - minimum_path_set)
    for item in missing_core_paths:
        errors.append(
            f"release minimum upload set omitted required Core release source: {item}"
        )

    missing_non_core_paths = sorted(required_non_core_paths - minimum_path_set)
    if missing_non_core_paths:
        errors.append(
            f"release minimum upload set omits required sources: {missing_non_core_paths}"
        )

    expected_minimum_paths = CORE_RELEASE_PATHS | required_non_core_paths
    unknown_paths = sorted(minimum_path_set - expected_minimum_paths)
    if unknown_paths:
        errors.append(
            f"release minimum upload set contains unknown replacement source: {unknown_paths}"
        )

    for item in sorted(CORE_RELEASE_PATHS):
        if not (root / item).is_file():
            errors.append(f"release required Core source is missing on disk: {item}")
    for item in sorted(required_non_core_paths):
        if not (root / item).is_file():
            errors.append(f"release minimum upload source is missing: {item}")

    try:
        manifest, schema = load_authority(root)
    except Exception as exc:
        errors.append(f"release authority load failed: {type(exc).__name__}: {exc}")
        manifest, schema = {}, {}

    contract_text = (root / CONTRACT_PATH).read_text(encoding="utf-8")
    if "contract_id: ev4-architect-conversational-stage-output" not in contract_text or "contract_version: 1.0.0" not in contract_text:
        errors.append("release Contract file does not expose the exact Contract identity")
    if schema.get("$id") != BASE_SCHEMA_ID:
        errors.append("release Base Schema file does not expose the exact Schema identity")

    rows = manifest.get("project_execution_stages", [])
    stage_reference: list[dict[str, Any]] = []
    for row in rows:
        stage_id = row.get("stage_id")
        version = row.get("stage_version")
        checks = row.get("required_quality_checks")
        if not stage_id or not version or not isinstance(checks, list) or not checks:
            errors.append(f"release Manifest Stage is incomplete: {stage_id!r}")
            continue
        stage_reference.append(
            {"stage_id": stage_id, "stage_version": version, "required_quality_checks": checks}
        )
        structural_sample = {
            "run_id": "release-upload-set-structural-proof",
            "stage_id": stage_id,
            "stage_version": version,
            "check_evidence": {
                key: {"result": "pass", "reason": "Representative structural record."}
                for key in checks
            },
            "unknown_introductions": [],
            "unknown_resolutions": [],
            "blockers": [],
        }
        structural_errors = validate_base_structure(structural_sample, root=root)
        errors.extend(f"release structural proof {stage_id}: {error}" for error in structural_errors)

    for item in example_paths:
        example_path = root / item
        if not example_path.is_file():
            errors.append(f"release conversational example is missing: {item}")
            continue
        errors.extend(
            f"release example {item}: {error}"
            for error in validate_manifest_consistency(_load(example_path), root=root)
        )

    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "upload_set_id": upload_set.get("upload_set_id"),
        "minimum_upload_files": len(minimum_paths),
        "core_release_files": len(CORE_RELEASE_PATHS),
        "stages_exposed": len(stage_reference),
        "stage_reference": stage_reference,
    }


def validate_repository_vectors(
    *,
    root: Path = ROOT,
    terminal_path: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    examples = sorted((root / "examples/conversational-stage-output").glob("*.json"))
    for path in examples:
        output = _load(path)
        errors.extend(
            f"{path.relative_to(root)}: {error}"
            for error in validate_manifest_consistency(output, root=root)
        )

    release_result = validate_release_upload_set(root=root)
    errors.extend(f"release: {error}" for error in release_result.get("errors", []))

    prefinal_dir = root / "fixtures/conversational-run/valid/minimal-complete-run"
    prefinal = load_output_files(prefinal_dir, root=root)
    resolved_terminal_path = terminal_path or (
        root / "fixtures/conversational-run/valid/terminal/project-gate-export.json"
    )
    terminal = _load(resolved_terminal_path)
    try:
        trusted = repository_trusted_context(root=root)
        complete_result = validate_run_outputs(
            [*prefinal, terminal],
            root=root,
            require_terminal=True,
            trusted_context=trusted,
        )
    except Exception as exc:
        complete_result = {
            "status": "invalid",
            "errors": [f"terminal provenance/runtime setup failed: {type(exc).__name__}: {exc}"],
            "results": [],
        }
    errors.extend(complete_result.get("errors", []))
    terminal_result = complete_result.get("results", [])[-1] if complete_result.get("results") else {}
    terminal_runtime_validated = bool(
        complete_result.get("status") == "valid"
        and terminal_result.get("stage_id") == "/project-gate-export"
        and terminal_result.get("project_gate_export")
    )
    if complete_result.get("status") == "valid" and not terminal_runtime_validated:
        errors.append("terminal: valid full Run must contain derived Project Gate export evidence")

    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "examples_checked": len(examples),
        "prefinal_stages_checked": len(prefinal),
        "terminal_runtime_validated": terminal_runtime_validated,
        "release_upload_set_validated": release_result.get("status") == "valid",
        "stages_visited": complete_result.get("stages_visited", []),
        "authority": {
            "contract": CONTRACT_ID,
            "base_schema": BASE_SCHEMA_ID,
            "continuation": "scripts/architect_quality_runtime.py#evaluate_stage",
        },
    }
