"""Runtime-internal Project Gate artifact construction and contract validation."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from architect_handoff_classification import partition_unresolved_evidence
from architect_runtime_payload_authority import (
    RuntimePayloadAuthorityError,
    _consume_runtime_terminal_payload,
)

from .base import *

_RUNTIME_INPUT_REF = "quality_runtime:runtime_issued_payload"


def validate_payload(root: Path, payload: Any) -> dict[str, Any]:
    path = root / "scripts/check-architect-stage-payload.py"
    spec = importlib.util.spec_from_file_location("architect_payload_validator", path)
    if spec is None or spec.loader is None:
        raise ExportError(
            "ARCH_EXPORT_VALIDATOR_LOAD_FAILED",
            "semantic_validation",
            "Official Architect validator could not be loaded.",
            "repository_owner",
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        result = module.ArchitectPayloadValidator(root).validate_value(payload)
    except Exception as exc:
        raise ExportError(
            "ARCH_EXPORT_VALIDATOR_LOAD_FAILED",
            "semantic_validation",
            f"Official validator failed: {type(exc).__name__}.",
            "repository_owner",
        ) from exc
    if result.get("status") == "invalid":
        codes = [
            item.get("code", "UNKNOWN")
            for item in result.get("diagnostics", [])
            if isinstance(item, dict)
        ]
        raise ExportError(
            "ARCH_EXPORT_ARCHITECT_PAYLOAD_INVALID",
            "semantic_validation",
            f"Official Architect validation failed: {', '.join(codes[:8])}.",
            "architect",
        )
    if result.get("status") not in {"valid", "insufficient_evidence"}:
        raise ExportError(
            "ARCH_EXPORT_VALIDATOR_RESULT_INVALID",
            "semantic_validation",
            "Official Architect validator returned an unsupported status.",
            "repository_owner",
        )
    return result


def _source(source_type: str, reference: str) -> dict[str, str]:
    if source_type in {"repo_path", "schema", "contract"}:
        return {"type": "repo_path", "reference": reference}
    if source_type in {"fixture", "synthetic_fixture"}:
        return {"type": "synthetic_fixture", "reference": reference}
    prefix = "stage_payload:" if source_type == "stage_payload" else ""
    return {"type": "manual_observation", "reference": prefix + reference}


def _evidence(payload: dict[str, Any], payload_hash: str) -> list[dict[str, Any]]:
    output = [
        {
            "id": "architect-stage-payload-canonical",
            "kind": "report",
            "state": "exported",
            "description": "Canonical Runtime-issued Architect Stage Payload.",
            "artifact_hash": {
                "algorithm": "sha256",
                "value": payload_hash,
                "scope": "canonical_json",
            },
            "source": {"type": "manual_observation", "reference": _RUNTIME_INPUT_REF},
            "derivation_rule": {"id": "ev4-canonical-json-sha256", "version": "1.0.0"},
        }
    ]
    kinds = {
        "schema": "schema",
        "fixture": "fixture",
        "synthetic_fixture": "fixture",
        "contract": "document",
        "repo_path": "document",
        "stage_payload": "report",
    }
    for record in payload.get("evidence_register", []):
        source = record.get("source_ref", {})
        source_type = str(source.get("source_type", "manual_observation"))
        output.append(
            {
                "id": str(record.get("evidence_id")),
                "kind": kinds.get(source_type, "other"),
                "state": str(record.get("state")),
                "description": str(record.get("claim")),
                "artifact_hash": {
                    "algorithm": "sha256",
                    "value": digest(record),
                    "scope": "canonical_json",
                },
                "source": _source(
                    source_type,
                    str(source.get("reference", record.get("evidence_id", "unknown"))),
                ),
                "derivation_rule": {
                    "id": "architect-evidence-record-canonicalization",
                    "version": "1.0.0",
                },
            }
        )
    return output


def build_export(
    payload: dict[str, Any],
    git: GitProvenance,
    run_id: str,
    input_ref: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Build only inside the active terminal Runtime transaction.

    Schema-valid dictionaries, copied Runtime Payloads, and caller-provided
    provenance are insufficient. The one-shot capability is issued by the
    canonical assembler during terminal evaluator replay and consumed here.
    """

    run_id = run_id.strip()
    if not run_id:
        raise ExportError(
            "ARCH_EXPORT_RUN_ID_REQUIRED",
            "run_identity",
            "Runtime-derived run_id is required.",
            "repository_owner",
        )
    if input_ref != _RUNTIME_INPUT_REF:
        raise ExportError(
            "ARCH_EXPORT_CALLER_INPUT_REF_FORBIDDEN",
            "runtime_authority",
            "Project Gate provenance is owned by the terminal Runtime transaction.",
            "repository_owner",
        )
    try:
        issuance = _consume_runtime_terminal_payload(payload, run_id=run_id)
    except RuntimePayloadAuthorityError as exc:
        raise ExportError(
            "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED",
            "runtime_authority",
            str(exc),
            "repository_owner",
        ) from exc

    if "continuation_assurance" in payload:
        raise ExportError(
            "ARCH_EXPORT_CALLER_PCVP_CARRIER_FORBIDDEN",
            "runtime_authority",
            "Caller-supplied continuation_assurance is forbidden.",
            "repository_owner",
        )

    payload_hash = digest(payload)
    unresolved = payload.get("unresolved_evidence", [])
    classification = partition_unresolved_evidence(unresolved)
    blockers = list(classification.transition_blockers)
    insufficient = payload.get("payload_status") == "insufficient_evidence"
    synthetic = issuance.synthetic
    allowed = not insufficient and not synthetic and not blockers
    handoff_status = (
        "insufficient_evidence"
        if insufficient
        else "blocked"
        if synthetic or blockers
        else "successful_with_flags"
        if unresolved
        else "successful"
    )
    stage_status = (
        "insufficient_evidence"
        if insufficient
        else "blocked"
        if synthetic or blockers
        else "complete"
    )

    bundle_id = "architect-bundle-" + digest(
        {
            "repository": git.repository,
            "commit": git.commit_sha,
            "run_id": run_id,
            "payload_hash": payload_hash,
        }
    )[:24]
    bundle: dict[str, Any] = {
        "schema_version": BUNDLE_VERSION,
        "bundle_id": bundle_id,
        "stage": "architect",
        "payload_schema": {
            "id": PAYLOAD_ID,
            "version": PAYLOAD_VERSION,
            "owner_repository": REPOSITORY,
        },
        "produced_by": {
            "repository": git.repository,
            "ref": git.ref,
            "commit_sha": git.commit_sha,
        },
        "evidence_status": str(payload.get("payload_status")),
        "payload": {"schema_id": PAYLOAD_ID, "data": payload},
        "evidence": _evidence(payload, payload_hash),
        "provenance": {
            "source": _RUNTIME_INPUT_REF,
            "created_by": "architect_quality_runtime",
        },
        "synthetic": synthetic,
    }
    if insufficient:
        bundle["missing_evidence"] = [
            {
                "id": str(item.get("unresolved_id")),
                "owner": str(item.get("owner")),
                "reason": str(item.get("reason")),
            }
            for item in unresolved
        ]
    bundle_hash = digest(bundle)
    export_id = "architect-export-" + digest(
        {
            "repository": git.repository,
            "commit": git.commit_sha,
            "run_id": run_id,
            "bundle_hash": bundle_hash,
        }
    )[:24]

    diagnostics: list[dict[str, Any]] = []
    reasons: list[dict[str, Any]] = []
    if insufficient:
        diagnostics.append(
            {"code": "ARCH_EXPORT_PAYLOAD_INSUFFICIENT_EVIDENCE", "severity": "error"}
        )
        reasons.append(
            {
                "id": "architect-payload-insufficient-evidence",
                "reason": "Architect payload is explicitly insufficient for handoff.",
            }
        )
    if synthetic:
        diagnostics.append(
            {"code": "ARCH_EXPORT_SYNTHETIC_HANDOFF_FORBIDDEN", "severity": "error"}
        )
        reasons.append(
            {
                "id": "synthetic-run-not-authorized",
                "reason": "Synthetic Runtime execution cannot authorize a real handoff.",
            }
        )
    diagnostics.extend(
        {
            "code": "ARCH_EXPORT_TRANSITION_EVIDENCE_BLOCKED",
            "severity": "error",
            "unresolved_id": item.get("unresolved_id"),
        }
        for item in blockers
    )

    export = {
        "schema_version": EXPORT_VERSION,
        "export_id": export_id,
        "producer": {
            "stage": "architect",
            "repository": git.repository,
            "ref": git.ref,
            "commit_sha": git.commit_sha,
        },
        "pipeline_id": PIPELINE_ID,
        "run_id": run_id,
        "stage_manifest": [
            {
                "stage_id": "/project-gate-export",
                "stage_version": "1.0.0",
                "ordinal": 12,
                "mandatory": True,
                "status": stage_status,
                "output": {
                    "present": True,
                    "artifact_ref": "final_stage_bundle",
                    "artifact_hash": {
                        "algorithm": "sha256",
                        "value": bundle_hash,
                        "scope": "canonical_json",
                    },
                },
                "blockers": diagnostics,
                "unknowns": unresolved,
            }
        ],
        "final_stage_bundle": bundle,
        "handoff": {
            "target": TARGET,
            "status": handoff_status,
            "allowed": allowed,
            "failure_reasons": reasons,
            "blocking_diagnostics": diagnostics,
            "unresolved_evidence": unresolved,
        },
        "validation": {
            "schema_valid": True,
            "semantic_valid": True,
            "validator_id": "ev4-producer-gate-export-validator",
            "validator_version": "1.0.0",
            "diagnostics": (
                [
                    {
                        "code": "ARCH_EXPORT_NONBLOCKING_UNRESOLVED_EVIDENCE",
                        "severity": "warning",
                        "count": len(unresolved),
                    }
                ]
                if unresolved and allowed
                else []
            ),
        },
        "acquisition_mode": {
            "mode": "producer_emitted_gate_artifact",
            "silent_fallback_allowed": False,
        },
    }

    hashes = {
        "payload_hash": payload_hash,
        "bundle_hash": bundle_hash,
        "export_hash": digest(export),
    }
    return export, hashes


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
    bundle_schema = load_json(root / "contracts/project-gate/stage-bundle.v1.schema.json")
    export_schema = load_json(root / "contracts/project-gate/producer-gate-export.v1.schema.json")
    try:
        Draft202012Validator.check_schema(bundle_schema)
        Draft202012Validator.check_schema(export_schema)
        errors = _errors(Draft202012Validator(bundle_schema), export.get("final_stage_bundle"))
        if errors:
            raise ExportError(
                "ARCH_EXPORT_STAGE_BUNDLE_SCHEMA_FAILED",
                "stage_bundle_validation",
                "; ".join(errors[:8]),
                "repository_owner",
            )
        registry = Registry().with_resource(
            bundle_schema["$id"], Resource.from_contents(bundle_schema)
        )
        errors = _errors(Draft202012Validator(export_schema, registry=registry), export)
        if errors:
            raise ExportError(
                "ARCH_EXPORT_PRODUCER_EXPORT_SCHEMA_FAILED",
                "producer_export_validation",
                "; ".join(errors[:8]),
                "repository_owner",
            )
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(
            "ARCH_EXPORT_CONTRACT_VALIDATION_FAILED",
            "contract_validation",
            f"Contract validation failed: {type(exc).__name__}: {exc}.",
            "repository_owner",
        ) from exc


def verify_hashes(export: dict[str, Any], expected: dict[str, str]) -> None:
    observed = {
        "payload_hash": digest(
            export.get("final_stage_bundle", {}).get("payload", {}).get("data")
        ),
        "bundle_hash": digest(export.get("final_stage_bundle")),
        "export_hash": digest(export),
    }
    for key, value in expected.items():
        if observed.get(key) != value:
            raise ExportError(
                "ARCH_EXPORT_HASH_SELF_VERIFICATION_FAILED",
                "hash_self_verification",
                f"{key} changed after construction.",
                "repository_owner",
            )
    recorded = (
        export.get("stage_manifest", [{}])[0]
        .get("output", {})
        .get("artifact_hash", {})
        .get("value")
    )
    if recorded != observed["bundle_hash"]:
        raise ExportError(
            "ARCH_EXPORT_BUNDLE_HASH_MISMATCH",
            "hash_self_verification",
            "Recorded bundle hash does not match final_stage_bundle.",
            "repository_owner",
        )
