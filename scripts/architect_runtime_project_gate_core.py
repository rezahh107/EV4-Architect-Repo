"""Typed Project Gate validation boundary used by the Architect Runtime."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from architect_runtime_errors import ProjectGateValidationError, RuntimeDiagnostic, RuntimeEnvironmentError


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeEnvironmentError(RuntimeDiagnostic(
            "RUNTIME_PROJECT_GATE_SOURCE_INVALID",
            f"Required Project Gate source could not be loaded: {type(exc).__name__}: {exc}",
            path=str(path),
        )) from exc


def validate_payload(root: Path, payload: Any) -> dict[str, Any]:
    path = root / "scripts/check-architect-stage-payload.py"
    spec = importlib.util.spec_from_file_location("architect_runtime_payload_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeEnvironmentError(RuntimeDiagnostic(
            "RUNTIME_PAYLOAD_VALIDATOR_LOAD_FAILED",
            "Official Architect Payload validator could not be loaded.",
            path=str(path),
        ))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.ArchitectPayloadValidator(root).validate_value(payload)
    if result.get("status") == "invalid":
        codes = [
            item.get("code", "UNKNOWN")
            for item in result.get("diagnostics", [])
            if isinstance(item, dict)
        ]
        raise ProjectGateValidationError(RuntimeDiagnostic(
            "RUNTIME_ARCHITECT_PAYLOAD_INVALID",
            f"Official Architect validation failed: {', '.join(codes[:8])}",
            stage_id="/project-gate-export",
        ))
    if result.get("status") not in {"valid", "insufficient_evidence"}:
        raise ProjectGateValidationError(RuntimeDiagnostic(
            "RUNTIME_PAYLOAD_VALIDATOR_RESULT_INVALID",
            "Official Architect validator returned an unsupported status.",
            stage_id="/project-gate-export",
        ))
    return result


def _errors(validator: Draft202012Validator, value: Any) -> list[str]:
    found = sorted(
        validator.iter_errors(value),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    return [
        f"{'/'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
        for error in found
    ]


def validate_contracts(root: Path, export: dict[str, Any]) -> None:
    bundle_schema = _load_json(root / "contracts/project-gate/stage-bundle.v1.schema.json")
    export_schema = _load_json(root / "contracts/project-gate/producer-gate-export.v1.schema.json")
    Draft202012Validator.check_schema(bundle_schema)
    Draft202012Validator.check_schema(export_schema)
    errors = _errors(Draft202012Validator(bundle_schema), export.get("final_stage_bundle"))
    if errors:
        raise ProjectGateValidationError(RuntimeDiagnostic(
            "RUNTIME_STAGE_BUNDLE_SCHEMA_FAILED", "; ".join(errors[:8]),
            stage_id="/project-gate-export",
        ))
    registry = Registry().with_resource(
        bundle_schema["$id"], Resource.from_contents(bundle_schema)
    )
    errors = _errors(Draft202012Validator(export_schema, registry=registry), export)
    if errors:
        raise ProjectGateValidationError(RuntimeDiagnostic(
            "RUNTIME_PRODUCER_EXPORT_SCHEMA_FAILED", "; ".join(errors[:8]),
            stage_id="/project-gate-export",
        ))
