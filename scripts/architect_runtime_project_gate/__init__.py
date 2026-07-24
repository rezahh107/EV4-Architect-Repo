"""Canonical Project Gate validation facade."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from architect_payload_semantic_validator import ArchitectPayloadValidator
from architect_runtime_errors import ProjectGateValidationError, RuntimeDiagnostic

_CORE_NAME = "_ev4_architect_runtime_project_gate_internal"
_CORE_PATH = Path(__file__).resolve().parents[1] / "architect_runtime_project_gate_core.py"
_spec = importlib.util.spec_from_file_location(_CORE_NAME, _CORE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load Architect Project Gate core: {_CORE_PATH}")
_core = importlib.util.module_from_spec(_spec)
sys.modules[_CORE_NAME] = _core
_spec.loader.exec_module(_core)
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


def validate_payload(root: Path, payload: Any) -> dict[str, Any]:
    result = ArchitectPayloadValidator(root).validate_value(payload)
    if result.get("status") == "invalid":
        codes = [
            item.get("code", "UNKNOWN")
            for item in result.get("diagnostics", [])
            if isinstance(item, dict)
        ]
        raise ProjectGateValidationError(
            RuntimeDiagnostic(
                "RUNTIME_ARCHITECT_PAYLOAD_INVALID",
                f"Official Architect validation failed: {', '.join(codes[:8])}",
                stage_id="/project-gate-export",
            )
        )
    if result.get("status") not in {"valid", "insufficient_evidence"}:
        raise ProjectGateValidationError(
            RuntimeDiagnostic(
                "RUNTIME_PAYLOAD_VALIDATOR_RESULT_INVALID",
                "Official Architect validator returned an unsupported status.",
                stage_id="/project-gate-export",
            )
        )
    return result


validate_contracts = _core.validate_contracts
__all__ = ["validate_payload", "validate_contracts"]
