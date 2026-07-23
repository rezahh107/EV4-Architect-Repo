"""Non-authorizing validation helpers for conversational Architect Stage Output."""
from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from architect_quality_runtime import (
    CALLER_AUTHORITY_FIELDS,
    derive_stage_result_authority,
    evaluate_run,
    load_authority as load_runtime_authority,
    validate_authority_documents,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("manifests/architect-pipeline-manifest.v1.json")
STAGE_RESULT_SCHEMA_PATH = Path("schemas/ev4-architect-stage-result.v1.schema.json")
BASE_SCHEMA_PATH = Path("schemas/architect-conversational-stage-output-base.v1.schema.json")
CONTRACT_PATH = Path("contracts/ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1.md")
EXAMPLES_DIRECTORY = Path("examples/conversational-stage-output")
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

T = TypeVar("T")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_source(root: Path, path: Path) -> tuple[Path, str]:
    resolved = path if path.is_absolute() else root / path
    label = str(path) if path.is_absolute() else path.as_posix()
    return resolved, label


def load_required_regular_file(
    root: Path,
    path: Path,
    errors: list[str],
) -> Path | None:
    resolved, label = _resolve_source(root, path)
    if not resolved.exists():
        errors.append(f"{label}: required source is missing")
        return None
    if not resolved.is_file():
        errors.append(f"{label}: required source is not a regular file")
        return None
    return resolved


def load_required_text(
    root: Path,
    path: Path,
    errors: list[str],
) -> str | None:
    resolved = load_required_regular_file(root, path, errors)
    if resolved is None:
        return None
    _, label = _resolve_source(root, path)
    try:
        return resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label}: required source is not valid UTF-8")
    except OSError as exc:
        errors.append(f"{label}: required source could not be read: {type(exc).__name__}: {exc}")
    return None


def load_required_json(
    root: Path,
    path: Path,
    errors: list[str],
    *,
    expected_type: type[T] = dict,
) -> T | None:
    text = load_required_text(root, path, errors)
    if text is None:
        return None
    _, label = _resolve_source(root, path)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(
            f"{label}: invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}"
        )
        return None
    if not isinstance(value, expected_type):
        expected_name = "object" if expected_type is dict else expected_type.__name__
        article = "an" if expected_name == "object" else "a"
        errors.append(f"{label}: JSON root must be {article} {expected_name}")
        return None
    return value


def _object_field(
    value: dict[str, Any],
    key: str,
    *,
    source: Path,
    errors: list[str],
) -> dict[str, Any]:
    field = value.get(key)
    if not isinstance(field, dict):
        errors.append(f"{source.as_posix()}.{key}: required field must be an object")
        return {}
    return field


def _string_list_field(
    value: dict[str, Any],
    key: str,
    *,
    source: Path,
    errors: list[str],
    require_nonempty: bool = True,
) -> list[str]:
    field = value.get(key)
    if not isinstance(field, list):
        errors.append(f"{source.as_posix()}.{key}: required field must be an array")
        return []
    valid: list[str] = []
    for index, item in enumerate(field):
        if not isinstance(item, str):
            errors.append(
                f"{source.as_posix()}.{key}[{index}]: value must be a string"
            )
            continue
        if not item:
            errors.append(
                f"{source.as_posix()}.{key}[{index}]: value must be a non-empty string"
            )
            continue
        valid.append(item)
    duplicates = sorted({item for item in valid if valid.count(item) > 1})
    if duplicates:
        errors.append(
            f"{source.as_posix()}.{key}: duplicate paths are forbidden: {duplicates}"
        )
    if require_nonempty and not valid:
        errors.append(f"{source.as_posix()}.{key}: at least one path is required")
    return valid


def _base_schema_authority_fields(schema: dict[str, Any]) -> set[str]:
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        raise ValueError("Conversational Base Schema.$defs must be an object")
    authority = defs.get("caller_authority_field")
    if not isinstance(authority, dict):
        raise ValueError(
            "Conversational Base Schema must declare caller authority fields"
        )
    values = authority.get("enum")
    if not isinstance(values, list) or not values or any(
        not isinstance(item, str) or not item for item in values
    ):
        raise ValueError(
            "Conversational Base Schema must declare caller authority fields"
        )
    if len(values) != len(set(values)):
        raise ValueError(
            "Conversational Base Schema caller authority fields must be unique"
        )
    return set(values)


def _verify_forbidden_set_sync(
    base_schema: dict[str, Any],
    stage_result_schema: dict[str, Any],
) -> set[str]:
    derived = set(
        derive_stage_result_authority(
            stage_result_schema
        ).forbidden_top_level_stage_output_fields
    )
    mirrored = _base_schema_authority_fields(base_schema)
    if mirrored != derived:
        missing = sorted(derived - mirrored)
        extra = sorted(mirrored - derived)
        raise ValueError(
            "Stage Result fields require evaluator-owned or shared classification "
            f"mirror update; missing={missing}, extra={extra}"
        )
    return derived


def load_authority(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest, stage_result_schema = load_runtime_authority(root)
    schema = _load(root / BASE_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    if schema.get("$id") != BASE_SCHEMA_ID:
        raise ValueError("Conversational Stage Output base Schema identity mismatch")
    _verify_forbidden_set_sync(schema, stage_result_schema)
    if set(CALLER_AUTHORITY_FIELDS) != _base_schema_authority_fields(schema):
        raise ValueError("Imported Runtime caller authority boundary differs from Base Schema")
    return manifest, schema


def _stage_map_from_manifest(
    manifest: dict[str, Any],
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    rows = manifest.get("project_execution_stages")
    if not isinstance(rows, list):
        raise ValueError("Pipeline Manifest.project_execution_stages must be an array")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Pipeline Manifest Stage entries must be objects")
    return [row["stage_id"] for row in rows], {
        row["stage_id"]: row for row in rows
    }


def stage_map(root: Path = ROOT) -> tuple[list[str], dict[str, dict[str, Any]]]:
    manifest, _ = load_authority(root)
    return _stage_map_from_manifest(manifest)


def _validate_base_structure_with_schema(
    output: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(output),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def validate_base_structure(
    output: dict[str, Any],
    *,
    root: Path = ROOT,
) -> list[str]:
    _, schema = load_authority(root)
    return _validate_base_structure_with_schema(output, schema)


def _validate_manifest_consistency_with_authority(
    output: dict[str, Any],
    *,
    manifest: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    errors = _validate_base_structure_with_schema(output, schema)
    _, stages = _stage_map_from_manifest(manifest)
    stage_id = output.get("stage_id")
    stage = stages.get(stage_id)
    if stage is None:
        return [*errors, f"stage_id: unknown Manifest Stage {stage_id!r}"]
    if output.get("stage_version") != stage.get("stage_version"):
        errors.append(
            "stage_version: expected "
            f"{stage.get('stage_version')} for {stage_id}, "
            f"got {output.get('stage_version')!r}"
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
            errors.append(
                f"check_evidence: unknown or cross-Stage checks {unknown}"
            )
    return errors


def validate_manifest_consistency(
    output: dict[str, Any],
    *,
    root: Path = ROOT,
) -> list[str]:
    manifest, schema = load_authority(root)
    return _validate_manifest_consistency_with_authority(
        output,
        manifest=manifest,
        schema=schema,
    )


def load_output_files(
    directory: Path,
    *,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    order, _ = stage_map(root)
    index = {stage_id: position for position, stage_id in enumerate(order)}
    outputs = [_load(path) for path in directory.glob("*.json")]
    if len(outputs) != len({item.get("stage_id") for item in outputs}):
        raise ValueError("Conversational Run fixture contains duplicate stage_id values")
    try:
        return sorted(outputs, key=lambda item: index[item["stage_id"]])
    except KeyError as exc:
        raise ValueError(
            f"Conversational Run fixture contains unknown Stage: {exc}"
        ) from exc


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


def canonical_example_paths(
    *,
    root: Path = ROOT,
    errors: list[str] | None = None,
) -> list[str]:
    diagnostics = errors if errors is not None else []
    directory = root / EXAMPLES_DIRECTORY
    if not directory.exists():
        diagnostics.append(
            f"{EXAMPLES_DIRECTORY.as_posix()}: canonical example directory is missing"
        )
        return []
    if not directory.is_dir():
        diagnostics.append(
            f"{EXAMPLES_DIRECTORY.as_posix()}: canonical example source is not a directory"
        )
        return []
    paths = sorted(
        path.relative_to(root).as_posix()
        for path in directory.glob("*.json")
        if path.is_file()
    )
    if not paths:
        diagnostics.append(
            f"{EXAMPLES_DIRECTORY.as_posix()}: canonical example inventory is empty"
        )
    return paths


def _is_safe_example_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.parent.as_posix() == EXAMPLES_DIRECTORY.as_posix()
        and path.suffix == ".json"
    )


def _release_result(
    *,
    errors: list[str],
    upload_set: dict[str, Any] | None,
    minimum_paths: list[str],
    canonical_examples: list[str],
    stage_reference: list[dict[str, Any]],
    examples_checked: int,
) -> dict[str, Any]:
    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "upload_set_id": upload_set.get("upload_set_id") if upload_set else None,
        "minimum_upload_files": len(minimum_paths),
        "core_release_files": len(CORE_RELEASE_PATHS),
        "canonical_example_files": len(canonical_examples),
        "examples_checked": examples_checked,
        "stages_exposed": len(stage_reference),
        "stage_reference": stage_reference,
    }


def validate_release_upload_set(*, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    upload_set = load_required_json(
        root,
        RELEASE_UPLOAD_SET_PATH,
        errors,
        expected_type=dict,
    )
    if upload_set is None:
        return _release_result(
            errors=errors,
            upload_set=None,
            minimum_paths=[],
            canonical_examples=[],
            stage_reference=[],
            examples_checked=0,
        )

    if upload_set.get("upload_set_id") != RELEASE_UPLOAD_SET_ID:
        errors.append("release upload set identity mismatch")
    manifest_path_value = upload_set.get("manifest_path")
    if not isinstance(manifest_path_value, str):
        errors.append(
            f"{RELEASE_UPLOAD_SET_PATH.as_posix()}.manifest_path: required field must be a string"
        )
    elif manifest_path_value != MANIFEST_PATH.as_posix():
        errors.append(
            "release upload set must expose the exact Pipeline Manifest path"
        )

    contract = _object_field(
        upload_set,
        "contract",
        source=RELEASE_UPLOAD_SET_PATH,
        errors=errors,
    )
    if contract and (
        contract.get("path") != CONTRACT_PATH.as_posix()
        or contract.get("identity") != CONTRACT_ID
    ):
        errors.append("release upload set Contract identity mismatch")
    base_schema_ref = _object_field(
        upload_set,
        "base_schema",
        source=RELEASE_UPLOAD_SET_PATH,
        errors=errors,
    )
    if base_schema_ref and (
        base_schema_ref.get("path") != BASE_SCHEMA_PATH.as_posix()
        or base_schema_ref.get("identity") != BASE_SCHEMA_ID
    ):
        errors.append("release upload set Base Schema identity mismatch")

    canonical_examples = canonical_example_paths(root=root, errors=errors)
    example_paths = _string_list_field(
        upload_set,
        "example_paths",
        source=RELEASE_UPLOAD_SET_PATH,
        errors=errors,
    )
    for item in example_paths:
        if not _is_safe_example_path(item):
            errors.append(
                f"release example path is outside the canonical examples directory: {item}"
            )
        resolved = root / item
        if not resolved.is_file():
            errors.append(f"release listed example is missing on disk: {item}")

    canonical_example_set = set(canonical_examples)
    listed_example_set = set(example_paths)
    missing_mirror = sorted(canonical_example_set - listed_example_set)
    extra_mirror = sorted(listed_example_set - canonical_example_set)
    if missing_mirror:
        errors.append(
            f"release example mirror omits canonical repository examples: {missing_mirror}"
        )
    if extra_mirror:
        errors.append(
            f"release example mirror contains non-canonical examples: {extra_mirror}"
        )

    minimum_paths = _string_list_field(
        upload_set,
        "minimum_upload_paths",
        source=RELEASE_UPLOAD_SET_PATH,
        errors=errors,
    )
    raw_minimum_paths = upload_set.get("minimum_upload_paths")
    if isinstance(raw_minimum_paths, list) and all(isinstance(item, str) for item in raw_minimum_paths):
        if len(raw_minimum_paths) != len(set(raw_minimum_paths)):
            errors.append("release minimum upload paths must be a unique list")
    minimum_path_set = set(minimum_paths)
    required_non_core_paths = {
        MANIFEST_PATH.as_posix(),
        CONTRACT_PATH.as_posix(),
        BASE_SCHEMA_PATH.as_posix(),
        *canonical_examples,
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

    manifest = load_required_json(
        root,
        MANIFEST_PATH,
        errors,
        expected_type=dict,
    )
    contract_text = load_required_text(root, CONTRACT_PATH, errors)
    base_schema = load_required_json(
        root,
        BASE_SCHEMA_PATH,
        errors,
        expected_type=dict,
    )
    stage_result_schema = load_required_json(
        root,
        STAGE_RESULT_SCHEMA_PATH,
        errors,
        expected_type=dict,
    )

    authority_valid = False
    if manifest is not None and stage_result_schema is not None:
        try:
            validate_authority_documents(manifest, stage_result_schema)
            authority_valid = True
        except (ValueError, SchemaError) as exc:
            errors.append(
                f"release Runtime authority is invalid: {type(exc).__name__}: {exc}"
            )

    base_schema_valid = False
    if base_schema is not None:
        try:
            Draft202012Validator.check_schema(base_schema)
            base_schema_valid = True
        except SchemaError as exc:
            errors.append(
                f"{BASE_SCHEMA_PATH.as_posix()}: invalid JSON Schema: {exc.message}"
            )
        if base_schema.get("$id") != BASE_SCHEMA_ID:
            errors.append(
                "release Base Schema file does not expose the exact Schema identity"
            )

    if base_schema is not None and stage_result_schema is not None:
        try:
            _verify_forbidden_set_sync(base_schema, stage_result_schema)
        except ValueError as exc:
            errors.append(f"release caller authority boundary drift: {exc}")

    if contract_text is not None and (
        "contract_id: ev4-architect-conversational-stage-output" not in contract_text
        or "contract_version: 1.0.0" not in contract_text
    ):
        errors.append(
            "release Contract file does not expose the exact Contract identity"
        )

    stage_reference: list[dict[str, Any]] = []
    if authority_valid and manifest is not None:
        rows = manifest.get("project_execution_stages")
        if not isinstance(rows, list):
            errors.append(
                "Pipeline Manifest.project_execution_stages must be an array"
            )
            rows = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(
                    f"Pipeline Manifest.project_execution_stages[{index}] must be an object"
                )
                continue
            stage_id = row.get("stage_id")
            version = row.get("stage_version")
            checks = row.get("required_quality_checks")
            if (
                not isinstance(stage_id, str)
                or not stage_id
                or not isinstance(version, str)
                or not version
                or not isinstance(checks, list)
                or not checks
                or any(not isinstance(key, str) or not key for key in checks)
            ):
                errors.append(
                    f"release Manifest Stage is incomplete: {stage_id!r}"
                )
                continue
            stage_reference.append(
                {
                    "stage_id": stage_id,
                    "stage_version": version,
                    "required_quality_checks": checks,
                }
            )
            if base_schema_valid and base_schema is not None:
                structural_sample = {
                    "run_id": "release-upload-set-structural-proof",
                    "stage_id": stage_id,
                    "stage_version": version,
                    "check_evidence": {
                        key: {
                            "result": "pass",
                            "reason": "Representative structural record.",
                        }
                        for key in checks
                    },
                    "unknown_introductions": [],
                    "unknown_resolutions": [],
                    "blockers": [],
                }
                structural_errors = _validate_base_structure_with_schema(
                    structural_sample,
                    base_schema,
                )
                errors.extend(
                    f"release structural proof {stage_id}: {error}"
                    for error in structural_errors
                )

    examples_checked = 0
    for item in canonical_examples:
        output = load_required_json(
            root,
            Path(item),
            errors,
            expected_type=dict,
        )
        if output is None:
            continue
        examples_checked += 1
        if authority_valid and base_schema_valid and manifest and base_schema:
            errors.extend(
                f"release example {item}: {error}"
                for error in _validate_manifest_consistency_with_authority(
                    output,
                    manifest=manifest,
                    schema=base_schema,
                )
            )

    return _release_result(
        errors=errors,
        upload_set=upload_set,
        minimum_paths=minimum_paths,
        canonical_examples=canonical_examples,
        stage_reference=stage_reference,
        examples_checked=examples_checked,
    )


def validate_repository_vectors(
    *,
    root: Path = ROOT,
    terminal_path: Path | None = None,
) -> dict[str, Any]:
    release_result = validate_release_upload_set(root=root)
    if release_result.get("status") != "valid":
        return {
            "status": "invalid",
            "errors": [
                f"release: {error}"
                for error in release_result.get("errors", [])
            ],
            "examples_checked": release_result.get("examples_checked", 0),
            "prefinal_stages_checked": 0,
            "terminal_runtime_validated": False,
            "release_upload_set_validated": False,
            "stages_visited": [],
            "authority": {
                "contract": CONTRACT_ID,
                "base_schema": BASE_SCHEMA_ID,
                "continuation": "scripts/architect_quality_runtime.py#evaluate_stage",
            },
        }

    errors: list[str] = []
    prefinal_dir = root / "fixtures/conversational-run/valid/minimal-complete-run"
    prefinal = load_output_files(prefinal_dir, root=root)
    resolved_terminal_path = terminal_path or Path(
        "fixtures/conversational-run/valid/terminal/project-gate-export.json"
    )
    terminal = load_required_json(
        root,
        resolved_terminal_path,
        errors,
        expected_type=dict,
    )
    if terminal is None:
        return {
            "status": "invalid",
            "errors": sorted(set(errors)),
            "examples_checked": release_result.get("examples_checked", 0),
            "prefinal_stages_checked": len(prefinal),
            "terminal_runtime_validated": False,
            "release_upload_set_validated": True,
            "stages_visited": [],
            "authority": {
                "contract": CONTRACT_ID,
                "base_schema": BASE_SCHEMA_ID,
                "continuation": "scripts/architect_quality_runtime.py#evaluate_stage",
            },
        }

    try:
        trusted = repository_trusted_context(root=root)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        complete_result = {
            "status": "invalid",
            "errors": [
                "terminal provenance/runtime setup failed: "
                f"{type(exc).__name__}: {exc}"
            ],
            "results": [],
        }
    else:
        complete_result = validate_run_outputs(
            [*prefinal, terminal],
            root=root,
            require_terminal=True,
            trusted_context=trusted,
        )

    errors.extend(complete_result.get("errors", []))
    terminal_result = (
        complete_result.get("results", [])[-1]
        if complete_result.get("results")
        else {}
    )
    terminal_runtime_validated = bool(
        complete_result.get("status") == "valid"
        and terminal_result.get("stage_id") == "/project-gate-export"
        and terminal_result.get("project_gate_export")
    )
    if complete_result.get("status") == "valid" and not terminal_runtime_validated:
        errors.append(
            "terminal: valid full Run must contain derived Project Gate export evidence"
        )

    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "examples_checked": release_result.get("examples_checked", 0),
        "prefinal_stages_checked": len(prefinal),
        "terminal_runtime_validated": terminal_runtime_validated,
        "release_upload_set_validated": True,
        "stages_visited": complete_result.get("stages_visited", []),
        "authority": {
            "contract": CONTRACT_ID,
            "base_schema": BASE_SCHEMA_ID,
            "continuation": "scripts/architect_quality_runtime.py#evaluate_stage",
        },
    }
