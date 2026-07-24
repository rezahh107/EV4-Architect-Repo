"""Canonical Architect Payload semantic validator with shared CSS references."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from architect_css_target_validation import validate_css_target_references

_LEGACY_NAME = "_ev4_architect_stage_payload_validator_base"
_LEGACY_PATH = Path(__file__).resolve().parent / "check_architect_stage_payload_core.py"
_spec = importlib.util.spec_from_file_location(_LEGACY_NAME, _LEGACY_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load Architect Payload validator: {_LEGACY_PATH}")
_base = importlib.util.module_from_spec(_spec)
sys.modules[_LEGACY_NAME] = _base
_spec.loader.exec_module(_base)


class ArchitectPayloadValidator(_base.ArchitectPayloadValidator):
    """Existing Schema/semantic checks plus shared CSS target integrity."""

    def validate_value(self, value: Any):
        result = super().validate_value(value)
        diagnostics = list(result.get("diagnostics", []))
        if any(
            item.get("code") in {"INPUT_NOT_OBJECT", "SCHEMA_VALIDATION_FAILED"}
            for item in diagnostics
            if isinstance(item, dict)
        ):
            return result
        extra = validate_css_target_references(value)
        if not extra:
            return result
        diagnostics.extend(
            {
                "code": item.code,
                "severity": "error",
                "message": item.message,
                "path": item.path or "$",
                "rule_id": "A-R08",
                "details": {"target_node_id": item.message.rsplit(": ", 1)[-1]}
                if item.code == "PAYLOAD_CSS_TARGET_UNKNOWN"
                else {},
            }
            for item in extra
        )
        diagnostics.sort(
            key=lambda item: (
                item.get("path", "$"),
                _base.ORDER.get(item.get("severity", "error"), 0),
                item.get("rule_id") or "",
                item.get("code", ""),
                item.get("message", ""),
            )
        )
        return {"status": "invalid", "diagnostics": diagnostics}


def validate_fixture_suite(repo_root: Path):
    validator = ArchitectPayloadValidator(repo_root)
    reports = []
    failures = 0
    for path, expected in _base.iter_expected(repo_root):
        if path.name == "cases.v1.json":
            data = __import__("json").loads(path.read_text(encoding="utf-8"))
            base_path = (path.parent / data["base_fixture"]).resolve()
            base_value = __import__("json").loads(base_path.read_text(encoding="utf-8"))
            import copy

            for case in data["cases"]:
                payload = copy.deepcopy(base_value)
                for mutation in case.get("mutations", []):
                    if mutation["op"] == "set":
                        _base._set_path(payload, mutation["path"], mutation["value"])
                    elif mutation["op"] == "delete":
                        _base._delete_path(payload, mutation["path"])
                    else:
                        raise ValueError(f"Unsupported mutation op: {mutation['op']}")
                observed = validator.validate_value(payload)
                ok = observed["status"] == expected
                failures += 0 if ok else 1
                reports.append(
                    {
                        "fixture": f"{path.relative_to(repo_root)}#{case['case_id']}",
                        "expected": expected,
                        "actual": observed["status"],
                        "ok": ok,
                        "diagnostic_codes": [
                            item["code"] for item in observed["diagnostics"]
                        ],
                    }
                )
            continue
        observed = validator.validate_file(path)
        ok = observed["status"] == expected
        failures += 0 if ok else 1
        reports.append(
            {
                "fixture": str(path.relative_to(repo_root)),
                "expected": expected,
                "actual": observed["status"],
                "ok": ok,
                "diagnostic_codes": [item["code"] for item in observed["diagnostics"]],
            }
        )
    return failures, reports
