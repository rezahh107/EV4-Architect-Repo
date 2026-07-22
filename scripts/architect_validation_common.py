#!/usr/bin/env python3
"""Deterministic Architect Stage Boundary Validation Transaction.

`validate-run` is the only production generator. `validate-bundle` independently
regenerates a transaction from exact contained artifact bytes. Standalone
artifact and sequence modes are diagnostic-only and never write authority files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_SCHEMA = "ev4-architect-pipeline-stage-artifact@1.1.0"
RECEIPT_SCHEMA = "ev4-architect-stage-validation-receipt@1.1.0"
FAILURE_EVENT_SCHEMA = "ev4-architect-validation-failure-event@1.0.0"
BOUNDARY_SCHEMA = "ev4-stage-boundary-record@1.1.0"
ANCHOR_SCHEMA = "ev4-stage-anchor@1.3.0"
BUNDLE_SCHEMA = "ev4-architect-validation-bundle@1.1.0"
VALIDATOR_ID = "architect-pipeline-stage-boundary-validator"
VALIDATOR_VERSION = "1.2.0"
DETERMINISM_PROFILE = "deterministic_no_timestamps_v2"
PIPELINE_MANIFEST_PATH = ROOT / "manifests/architect-pipeline-manifest.v1.json"
VALIDATION_PROFILES_PATH = ROOT / "manifests/architect-stage-validation-profiles.v1.json"


def _load_validation_authority() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Load the two canonical authorities; neither is duplicated in code."""
    manifest = json.loads(PIPELINE_MANIFEST_PATH.read_text(encoding="utf-8"))
    registry = json.loads(VALIDATION_PROFILES_PATH.read_text(encoding="utf-8"))
    stages = manifest["project_execution_stages"]
    profiles = {profile["stage_id"]: profile for profile in registry["profiles"]}
    manifest_ids = [stage["stage_id"] for stage in stages]
    if len(manifest_ids) != len(set(manifest_ids)) or set(manifest_ids) != set(profiles):
        raise RuntimeError("ASB-VALIDATION-PROFILE-TOPOLOGY-DRIFT")
    return manifest, profiles


PIPELINE_MANIFEST, VALIDATION_PROFILES = _load_validation_authority()
ALL_ORDER = [stage["stage_id"] for stage in PIPELINE_MANIFEST["project_execution_stages"]]
EXECUTABLE_STAGES = tuple(
    stage for stage in ALL_ORDER if VALIDATION_PROFILES[stage]["validation"]["executable"]
)
PREFIX = {
    "/decompose": "decompose",
    "/architectures": "architectures",
    "/score-evidence": "score-evidence",
    "/score-audit": "score-audit",
}
def _manifest_stage(stage_id: str) -> dict[str, Any]:
    return next(stage for stage in PIPELINE_MANIFEST["project_execution_stages"] if stage["stage_id"] == stage_id)


def stage_version(stage_id: str) -> str | None:
    return _manifest_stage(stage_id)["stage_version"] if stage_id in EXECUTABLE_STAGES else None


def successor_stage(stage_id: str) -> str | None:
    return _manifest_stage(stage_id)["next_stage"]


def predecessor_stage(stage_id: str) -> str | None:
    index = ALL_ORDER.index(stage_id)
    return ALL_ORDER[index - 1] if index else None
ACTIVE_UNKNOWN_STATES = {"carried", "score_capped", "blocking", "downstream_only"}
INACTIVE_UNKNOWN_STATES = {"resolved_with_evidence", "not_applicable", "stale"}
UNKNOWN_STATES = ACTIVE_UNKNOWN_STATES | INACTIVE_UNKNOWN_STATES
CONFIDENCE = {"confirmed", "likely", "unknown", "blocked", "not_applicable"}
OUTPUT_OWNERSHIP_SENTINEL = "manifest.json"
SCHEMA_PATHS = {
    "artifact": "schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json",
    "receipt": "schemas/ev4-architect-stage-validation-receipt.v1.schema.json",
    "failure_event": "schemas/ev4-architect-validation-failure-event.v1.schema.json",
    "boundary": "schemas/ev4-stage-boundary-record.v1.schema.json",
    "anchor": "schemas/ev4-stage-anchor.v1.schema.json",
    "bundle": "schemas/ev4-architect-validation-bundle.v1.schema.json",
}
DIAGNOSTIC_OWNERS = {
    "ASB-STAGE-VERSION-MISMATCH": "detected_stage",
    "ASB-SCHEMA-VALIDATION-FAILED": "detected_stage",
    "ASB-RUN-ID-DISCONTINUITY": "detected_stage",
    "ASB-STAGE-SEQUENCE-GAP": "missing_stage",
    "ASB-DUPLICATE-STAGE": "detected_stage",
    "ASB-STAGE-FILE-MISMATCH": "detected_stage",
    "ASB-SOURCE-REF-MISSING": "predecessor_stage",
    "ASB-SOURCE-REF-MISMATCH": "predecessor_stage",
    "ASB-COVERAGE-MATRIX-INCOMPLETE": "/architectures",
    "ASB-UPSTREAM-UNKNOWN-LOST": "/decompose",
    "ASB-UNKNOWN-RESOLUTION-UNSUPPORTED": "/architectures",
    "ASB-UNKNOWN-RESOLUTION-EVIDENCE-MISSING": "/architectures",
    "ASB-STAGE3-PAYLOAD-REFERENCE-COUNT": "/architectures",
    "ASB-STAGE3-PAYLOAD-REFERENCE-MISMATCH": "/architectures",
    "ASB-CANDIDATE-NOT-IN-STAGE3": "/architectures",
    "ASB-STAGE3-UNKNOWN-DISCARDED": "/score-evidence",
    "ASB-SCORE-AUDITED-EARLY": "/score-evidence",
    "ASB-FINAL-TOTAL-WITH-UNKNOWN": "/score-evidence",
    "ASB-STAGE4-REFERENCE-MISMATCH": "/score-evidence",
    "ASB-UNSAFE-OUTPUT-PATH": "detected_stage",
    "ASB-OUTPUT-NOT-VALIDATOR-OWNED": "detected_stage",
}
DIAGNOSTIC_PRIORITY = {
    "ASB-UNSAFE-OUTPUT-PATH": 1,
    "ASB-OUTPUT-NOT-VALIDATOR-OWNED": 2,
    "ASB-STAGE-VERSION-MISMATCH": 5,
    "ASB-SCHEMA-VALIDATION-FAILED": 10,
    "ASB-RUN-ID-DISCONTINUITY": 20,
    "ASB-STAGE-SEQUENCE-GAP": 30,
    "ASB-DUPLICATE-STAGE": 40,
    "ASB-STAGE-FILE-MISMATCH": 50,
    "ASB-SOURCE-REF-MISSING": 60,
    "ASB-SOURCE-REF-MISMATCH": 70,
    "ASB-UPSTREAM-UNKNOWN-LOST": 80,
    "ASB-COVERAGE-MATRIX-INCOMPLETE": 90,
    "ASB-UNKNOWN-RESOLUTION-UNSUPPORTED": 95,
    "ASB-UNKNOWN-RESOLUTION-EVIDENCE-MISSING": 96,
    "ASB-STAGE3-PAYLOAD-REFERENCE-COUNT": 97,
    "ASB-STAGE3-PAYLOAD-REFERENCE-MISMATCH": 98,
    "ASB-CANDIDATE-NOT-IN-STAGE3": 100,
    "ASB-STAGE3-UNKNOWN-DISCARDED": 110,
    "ASB-SCORE-AUDITED-EARLY": 120,
    "ASB-FINAL-TOTAL-WITH-UNKNOWN": 130,
    "ASB-STAGE4-REFERENCE-MISMATCH": 140,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def stage_index(stage: str | None) -> int:
    try:
        return EXECUTABLE_STAGES.index(stage or "")
    except ValueError:
        return len(EXECUTABLE_STAGES) + 1


def diagnostic(
    code: str,
    rule_id: str,
    stage_id: str,
    path: str,
    expected: str,
    observed: str,
    repair_target_stage: str,
) -> dict[str, Any]:
    return {
        "code": code,
        "rule_id": rule_id,
        "stage_id": stage_id,
        "path": path,
        "expected": expected,
        "observed": observed,
        "repair_target_stage": repair_target_stage,
    }


def sort_diagnostics(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            stage_index(item.get("repair_target_stage")),
            DIAGNOSTIC_PRIORITY.get(item.get("code", ""), 999),
            item.get("code", ""),
            stage_index(item.get("stage_id")),
            item.get("path", ""),
        ),
    )


def select_repair_target(items: list[dict[str, Any]], fallback: str) -> str:
    if not items:
        return fallback
    return sort_diagnostics(items)[0]["repair_target_stage"]


def schema_validators(root: Path = ROOT) -> dict[str, Draft202012Validator]:
    validators: dict[str, Draft202012Validator] = {}
    for name, rel in SCHEMA_PATHS.items():
        schema = load_json(root / rel)
        Draft202012Validator.check_schema(schema)
        validators[name] = Draft202012Validator(schema)
    return validators


def schema_diagnostics(
    validator: Draft202012Validator,
    value: Any,
    stage: str,
    base_path: str,
    repair_target: str,
) -> list[dict[str, Any]]:
    result = []
    for error in sorted(validator.iter_errors(value), key=lambda e: list(e.absolute_path)):
        suffix = "".join(f"/{part}" for part in error.absolute_path)
        result.append(
            diagnostic(
                "ASB-SCHEMA-VALIDATION-FAILED",
                "ASB-R01",
                stage,
                f"{base_path}{suffix}",
                error.message,
                "schema_violation",
                repair_target,
            )
        )
    return result
