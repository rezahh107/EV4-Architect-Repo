"""Active EV4-PCVP carrier construction for the Architect → Project Gate → CE edge.

The immutable EV4-PCVP bundle remains byte-pinned to its original Decision Kernel
snapshot. Official emission is authorized separately by the exact canonical edge
activation merge. Carrier construction stays private to the Runtime-owned terminal
Project Gate transaction; callers cannot supply raw Runtime facts, select a
repository root, or override activation through environment/configuration input.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

POLICY_ID = "EV4-PCVP"
POLICY_VERSION = "1.0.0"
ARCHITECTURE_LOCK_ID = "EV4-PCVP-ROLL-LOCK-20260727-R1"
CANONICAL_REPOSITORY = "rezahh107/EV4-Decision-Kernel"
CANONICAL_COMMIT = "069a50fa243b01fa578a7c1bcb8864d9e796d34b"
ACTIVATION_COMMIT = "ad0e7235929d7f6d847724f6b4d1a6a3c57453db"
ACTIVATION_PATH = "kernel/pcvp/pcvp-activation.v1.json"
ACTIVATION_ID = "EV4-PCVP-ACT-ARCH-PG-CE-20260728-R1"
ACTIVATION_EDGE = "ARCHITECT_TO_PROJECT_GATE_TO_CE"
DISABLED_EDGES = (
    "CE_TO_BUILDER",
    "BUILDER_TO_RESPONSIVE",
    "RESPONSIVE_TO_FINAL",
)
SOURCE_STAGE = "ARCHITECT"
BOUNDARY_READER_STAGE = "PROJECT_GATE"
CONSUMER_STAGE = "CONSTRUCTABILITY_ENGINEER"
ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = Path("contracts/pcvp/architect-producer.lock.json")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_NAMES = (
    "authorization.schema.json",
    "claim.schema.json",
    "effect.schema.json",
    "handoff.schema.json",
)


class PCVPProducerError(RuntimeError):
    """Raised when producer identity, activation, derivation, or validation fails closed."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise PCVPProducerError(
            f"PCVP resource could not be loaded: {path} ({type(exc).__name__})"
        ) from exc


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PCVPProducerError(
            f"PCVP identity input is not canonical JSON: {exc}"
        ) from exc


def _identity(run_id: str, payload_hash: str) -> str:
    digest = hashlib.sha256(
        _canonical_bytes({"run_id": run_id, "payload_hash": payload_hash})
    ).hexdigest()
    return digest[:16].upper()


def _validate_activation_authority_document(document: Any) -> None:
    """Require the exact canonical staged activation and no downstream rollout."""
    if not isinstance(document, dict):
        raise PCVPProducerError("PCVP activation authority must be a JSON object.")
    if document.get("schema_version") != "ev4-pcvp-edge-activation.v1":
        raise PCVPProducerError("PCVP activation schema identity drifted.")
    if document.get("activation_id") != ACTIVATION_ID:
        raise PCVPProducerError("PCVP activation identifier drifted.")
    policy = document.get("policy")
    if policy != {
        "id": POLICY_ID,
        "version": POLICY_VERSION,
        "architecture_lock_id": ARCHITECTURE_LOCK_ID,
    }:
        raise PCVPProducerError("PCVP activation policy identity drifted.")
    if document.get("official_adoption_authorization") is not True:
        raise PCVPProducerError("PCVP official adoption authorization is absent.")
    if document.get("full_rollout_authorized") is not False:
        raise PCVPProducerError("PCVP full rollout must remain unauthorized.")
    if document.get("strict_activation_allowed_for_enabled_scope") is not True:
        raise PCVPProducerError("PCVP enabled scope is not authorized for activation.")
    scope = document.get("activation_scope")
    if not isinstance(scope, dict) or scope.get("enabled_edges") != [ACTIVATION_EDGE]:
        raise PCVPProducerError("PCVP enabled activation edge drifted.")
    if scope.get("disabled_edges") != list(DISABLED_EDGES):
        raise PCVPProducerError("PCVP downstream disabled edges drifted.")
    runtime = document.get("runtime_authorization")
    expected_runtime = {
        "architect_producer_emission": True,
        "architect_to_project_gate": True,
        "project_gate_to_ce": True,
        "ce_to_builder_emission": False,
        "builder_to_responsive_emission": False,
        "responsive_to_final_emission": False,
    }
    if runtime != expected_runtime:
        raise PCVPProducerError("PCVP runtime activation boundary drifted.")
    boundaries = document.get("authority_boundaries")
    if boundaries != {
        "runtime_correctness_created": False,
        "project_gate_pass_created": False,
        "ce_correctness_created": False,
        "production_readiness_created": False,
        "official_verification_replacement": False,
    }:
        raise PCVPProducerError("PCVP authority boundary claims drifted.")


def verify_pcvp_resources(repository_root: str | Path = ROOT) -> dict[str, Any]:
    """Verify immutable bundle bytes plus the exact active Architect edge lock."""
    root = Path(repository_root)
    lock = _load_json(root / LOCK_PATH)
    expected_policy = {
        "id": POLICY_ID,
        "version": POLICY_VERSION,
        "adoption_status": "not_yet_adopted",
        "activation": ACTIVATION_EDGE,
    }
    if (
        not isinstance(lock, dict)
        or lock.get("schema_version") != "ev4-pcvp-architect-producer-lock.v1"
        or lock.get("architecture_lock_id") != ARCHITECTURE_LOCK_ID
        or lock.get("policy") != expected_policy
    ):
        raise PCVPProducerError("PCVP Architect producer lock identity drifted.")

    canonical = lock.get("canonical")
    if not isinstance(canonical, dict) or canonical != {
        "repository": CANONICAL_REPOSITORY,
        "commit_sha": CANONICAL_COMMIT,
        "bundle_root": "kernel/pcvp/v1.0.0/bundle",
    }:
        raise PCVPProducerError("PCVP canonical owner or immutable commit drifted.")

    activation = lock.get("activation_authority")
    if not isinstance(activation, dict) or activation != {
        "repository": CANONICAL_REPOSITORY,
        "commit_sha": ACTIVATION_COMMIT,
        "path": ACTIVATION_PATH,
        "activation_id": ACTIVATION_ID,
        "official_adoption_authorization": True,
        "full_rollout_authorized": False,
        "enabled_edges": [ACTIVATION_EDGE],
        "disabled_edges": list(DISABLED_EDGES),
    }:
        raise PCVPProducerError("PCVP canonical activation authority drifted.")

    producer = lock.get("producer")
    if not isinstance(producer, dict) or producer != {
        "repository": "rezahh107/EV4-Architect-Repo",
        "source_stage": SOURCE_STAGE,
        "boundary_reader_stage": BOUNDARY_READER_STAGE,
        "consumer_stage": CONSUMER_STAGE,
        "carrier_path": "continuation_assurance",
        "emission_enabled": True,
        "caller_override_allowed": False,
    }:
        raise PCVPProducerError(
            "PCVP Architect producer must be enabled only for the locked edge and forbid caller override."
        )

    verification = lock.get("verification")
    if verification != {
        "byte_equality_required": True,
        "compare_against_moving_default_branch": False,
    }:
        raise PCVPProducerError("PCVP immutable-byte verification policy drifted.")

    entries = lock.get("resources")
    if not isinstance(entries, list) or len(entries) != 6:
        raise PCVPProducerError("PCVP lock must cover exactly six resources.")

    observed: dict[str, str] = {}
    canonical_paths: set[str] = set()
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "canonical_path", "sha256"}
            or not isinstance(entry.get("path"), str)
            or not isinstance(entry.get("canonical_path"), str)
            or not isinstance(entry.get("sha256"), str)
            or not SHA256.fullmatch(entry["sha256"])
        ):
            raise PCVPProducerError("PCVP resource lock entry is malformed.")
        path = Path(entry["path"])
        if path.is_absolute() or ".." in path.parts:
            raise PCVPProducerError("PCVP resource path escaped repository scope.")
        try:
            content = (root / path).read_bytes()
        except OSError as exc:
            raise PCVPProducerError(
                f"PCVP resource is unavailable: {path} ({type(exc).__name__})"
            ) from exc
        digest = hashlib.sha256(content).hexdigest()
        if digest != entry["sha256"]:
            raise PCVPProducerError(f"PCVP resource hash mismatch: {path}")
        if entry["path"] in observed:
            raise PCVPProducerError(f"Duplicate PCVP resource path: {path}")
        if entry["canonical_path"] in canonical_paths:
            raise PCVPProducerError(
                f"Duplicate canonical PCVP resource: {entry['canonical_path']}"
            )
        observed[entry["path"]] = digest
        canonical_paths.add(entry["canonical_path"])

    required_paths = {
        "contracts/pcvp/EV4_PCVP_MODEL_POLICY_v1.0.0.md",
        "contracts/pcvp/architect.profile.yaml",
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/authorization.schema.json",
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/claim.schema.json",
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/effect.schema.json",
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/handoff.schema.json",
    }
    if set(observed) != required_paths:
        raise PCVPProducerError("PCVP resource set drifted.")
    return {
        "architecture_lock_id": ARCHITECTURE_LOCK_ID,
        "canonical_commit": CANONICAL_COMMIT,
        "activation_commit": ACTIVATION_COMMIT,
        "activation_id": ACTIVATION_ID,
        "resource_hashes": dict(sorted(observed.items())),
        "producer_emission": True,
        "adoption_status": "official_edge_activation",
        "activation_effect": ACTIVATION_EDGE,
        "disabled_edges": list(DISABLED_EDGES),
        "full_rollout_authorized": False,
    }


def _load_schemas(repository_root: Path) -> dict[str, dict[str, Any]]:
    verify_pcvp_resources(repository_root)
    vendor = repository_root / "contracts/pcvp/vendor/decision-kernel/v1.0.0"
    schemas: dict[str, dict[str, Any]] = {}
    for name in _SCHEMA_NAMES:
        value = _load_json(vendor / name)
        if not isinstance(value, dict):
            raise PCVPProducerError(f"PCVP schema is not an object: {name}")
        try:
            Draft202012Validator.check_schema(value)
        except Exception as exc:
            raise PCVPProducerError(
                f"PCVP schema is invalid: {name} ({type(exc).__name__})"
            ) from exc
        schemas[name] = value
    return schemas


def _diagnostic(layer: str, code: str, subject: str, detail: str) -> dict[str, str]:
    return {"layer": layer, "code": code, "subject": subject, "detail": detail}


def _schema_diagnostics(
    document: dict[str, Any], repository_root: Path
) -> list[dict[str, str]]:
    schemas = _load_schemas(repository_root)
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(
            schema["$id"], Resource.from_contents(schema)
        )
    validator = Draft202012Validator(
        schemas["handoff.schema.json"], registry=registry
    )
    diagnostics: list[dict[str, str]] = []
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.validator or "",
            error.message,
        ),
    )
    for error in errors:
        path = "/" + "/".join(str(part) for part in error.absolute_path)
        diagnostics.append(
            _diagnostic(
                "JSON_SCHEMA",
                f"PCVP_SCHEMA_{str(error.validator).upper()}",
                path or "/",
                error.message,
            )
        )
    return diagnostics


def _cross_record_and_semantic_diagnostics(
    document: dict[str, Any],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    carrier = document["continuation_assurance"]
    claims = carrier["claims"]
    effects = carrier["effects"]
    authorizations = carrier["authorizations"]
    summary = carrier["stage_summary"]
    cross_record: list[dict[str, str]] = []
    semantic_policy: list[dict[str, str]] = []

    claims_by_id = {item["claim_id"]: item for item in claims}
    effects_by_id = {item["effect_id"]: item for item in effects}
    authorizations_by_id = {
        item["authorization_id"]: item for item in authorizations
    }
    all_ids = [
        *(item["claim_id"] for item in claims),
        *(item["effect_id"] for item in effects),
        *(item["authorization_id"] for item in authorizations),
    ]
    if len(set(all_ids)) != len(all_ids):
        cross_record.append(
            _diagnostic(
                "CROSS_RECORD",
                "PCVP_ID_NOT_GLOBALLY_UNIQUE",
                "continuation_assurance",
                "Claim, Effect and Authorization identifiers must be globally unique within the carrier.",
            )
        )

    for claim in claims:
        for dependency_id in claim["dependency_refs"]:
            if dependency_id not in claims_by_id:
                cross_record.append(
                    _diagnostic(
                        "CROSS_RECORD",
                        "PCVP_CLAIM_DEPENDENCY_UNRESOLVED",
                        claim["claim_id"],
                        dependency_id,
                    )
                )

    for effect in effects:
        for claim_id in effect["depends_on_claim_ids"]:
            if claim_id not in claims_by_id:
                cross_record.append(
                    _diagnostic(
                        "CROSS_RECORD",
                        "PCVP_EFFECT_CLAIM_REF_UNRESOLVED",
                        effect["effect_id"],
                        claim_id,
                    )
                )

        authorization = (
            None
            if effect["authorization_ref"] is None
            else authorizations_by_id.get(effect["authorization_ref"])
        )
        if effect["authorization_ref"] is not None and authorization is None:
            cross_record.append(
                _diagnostic(
                    "CROSS_RECORD",
                    "PCVP_EFFECT_AUTH_REF_UNRESOLVED",
                    effect["effect_id"],
                    effect["authorization_ref"],
                )
            )
        if authorization is not None:
            if authorization["status"] != "ACTIVE":
                cross_record.append(
                    _diagnostic(
                        "CROSS_RECORD",
                        "PCVP_EFFECT_AUTH_NOT_ACTIVE",
                        effect["effect_id"],
                        authorization["authorization_id"],
                    )
                )
            covered = (
                effect["effect_id"] in authorization["allowed_effect_ids"]
                or effect["effect_class"]
                in authorization["allowed_effect_classes"]
            )
            if not covered:
                cross_record.append(
                    _diagnostic(
                        "CROSS_RECORD",
                        "PCVP_EFFECT_AUTH_NOT_COVERING",
                        effect["effect_id"],
                        authorization["authorization_id"],
                    )
                )
            if authorization["permitted_scope"] != effect["permitted_scope"]:
                cross_record.append(
                    _diagnostic(
                        "CROSS_RECORD",
                        "PCVP_EFFECT_AUTH_SCOPE_MISMATCH",
                        effect["effect_id"],
                        authorization["authorization_id"],
                    )
                )
            if (
                authorization["basis"] == "SAFE_REVERSIBLE_DEFAULT"
                and effect["effect_class"]
                in {"EXTERNAL_MUTATION", "IRREVERSIBLE_OR_AUTHORITY_BEARING"}
            ):
                semantic_policy.append(
                    _diagnostic(
                        "SEMANTIC_POLICY",
                        "PCVP_SAFE_DEFAULT_FORBIDDEN_EFFECT",
                        effect["effect_id"],
                        effect["effect_class"],
                    )
                )

        dependent_claims = [
            claims_by_id[claim_id]
            for claim_id in effect["depends_on_claim_ids"]
            if claim_id in claims_by_id
        ]
        contradicted_critical = any(
            claim["criticality"] == "CRITICAL"
            and claim["applicability_state"] == "APPLICABLE"
            and claim["verification_state"] == "CONTRADICTED"
            for claim in dependent_claims
        )
        if contradicted_critical and effect["continuation_state"] != "BLOCKED":
            semantic_policy.append(
                _diagnostic(
                    "SEMANTIC_POLICY",
                    "PCVP_CONTRADICTED_CRITICAL_EFFECT_NOT_BLOCKED",
                    effect["effect_id"],
                    effect["continuation_state"],
                )
            )

    current_effect = effects_by_id.get(summary["current_effect_id"])
    if current_effect is None:
        cross_record.append(
            _diagnostic(
                "CROSS_RECORD",
                "PCVP_SUMMARY_EFFECT_REF_UNRESOLVED",
                "stage_summary",
                summary["current_effect_id"],
            )
        )
        return cross_record, semantic_policy

    current_dependencies = set(current_effect["depends_on_claim_ids"])
    for claim_id in summary["derived_from_claim_ids"]:
        if claim_id not in claims_by_id:
            cross_record.append(
                _diagnostic(
                    "CROSS_RECORD",
                    "PCVP_SUMMARY_CLAIM_REF_UNRESOLVED",
                    "stage_summary",
                    claim_id,
                )
            )
        elif claim_id not in current_dependencies:
            cross_record.append(
                _diagnostic(
                    "CROSS_RECORD",
                    "PCVP_SUMMARY_CLAIM_NOT_EFFECT_DEPENDENCY",
                    "stage_summary",
                    claim_id,
                )
            )

    dependent_claims = [
        claims_by_id[claim_id]
        for claim_id in current_effect["depends_on_claim_ids"]
        if claim_id in claims_by_id
    ]
    critical_contradicted = any(
        claim["criticality"] == "CRITICAL"
        and claim["applicability_state"] == "APPLICABLE"
        and claim["verification_state"] == "CONTRADICTED"
        for claim in dependent_claims
    )
    any_contradicted = any(
        claim["verification_state"] == "CONTRADICTED"
        for claim in dependent_claims
    )
    critical_applicable_not_verified = any(
        claim["criticality"] == "CRITICAL"
        and claim["applicability_state"] == "APPLICABLE"
        and claim["verification_state"] != "VERIFIED"
        for claim in dependent_claims
    )
    material_applicability_undetermined = any(
        claim["criticality"] in {"CRITICAL", "MATERIAL"}
        and claim["applicability_state"] == "UNDETERMINED"
        for claim in dependent_claims
    )
    applicable_unverified = any(
        claim["applicability_state"] == "APPLICABLE"
        and claim["verification_state"] == "UNVERIFIED"
        for claim in dependent_claims
    )

    if summary["owner_projection"] == "GREEN" and (
        current_effect["continuation_state"] != "CONTINUE"
        or critical_applicable_not_verified
        or applicable_unverified
        or any_contradicted
        or material_applicability_undetermined
    ):
        semantic_policy.append(
            _diagnostic(
                "SEMANTIC_POLICY",
                "PCVP_GREEN_PROJECTION_INVALID",
                "stage_summary",
                current_effect["effect_id"],
            )
        )

    if summary["owner_projection"] == "YELLOW":
        expected_substate = (
            "CONTINUATION_AVAILABLE"
            if current_effect["continuation_state"] == "CONTINUE"
            else "OWNER_CHOICE_REQUIRED"
            if current_effect["continuation_state"] == "AUTHORIZATION_REQUIRED"
            else None
        )
        if (
            expected_substate is None
            or summary["yellow_substate"] != expected_substate
            or (
                not applicable_unverified
                and current_effect["continuation_state"]
                != "AUTHORIZATION_REQUIRED"
            )
            or critical_contradicted
        ):
            semantic_policy.append(
                _diagnostic(
                    "SEMANTIC_POLICY",
                    "PCVP_YELLOW_PROJECTION_INVALID",
                    "stage_summary",
                    current_effect["effect_id"],
                )
            )

    if (
        summary["owner_projection"] == "RED"
        and current_effect["continuation_state"] != "BLOCKED"
    ):
        semantic_policy.append(
            _diagnostic(
                "SEMANTIC_POLICY",
                "PCVP_RED_WITH_NON_BLOCKED_EFFECT",
                "stage_summary",
                current_effect["effect_id"],
            )
        )

    if (
        current_effect["continuation_state"] == "BLOCKED"
        or critical_contradicted
    ) and summary["owner_projection"] != "RED":
        semantic_policy.append(
            _diagnostic(
                "SEMANTIC_POLICY",
                "PCVP_REQUIRED_RED_PROJECTION_MISSING",
                "stage_summary",
                current_effect["effect_id"],
            )
        )

    return cross_record, semantic_policy


def _evaluate_carrier_document(
    document: dict[str, Any], repository_root: str | Path = ROOT
) -> dict[str, Any]:
    """Evaluate one carrier with the pinned canonical layer ordering."""
    root = Path(repository_root)
    schema_diagnostics = _schema_diagnostics(document, root)
    if schema_diagnostics:
        return {
            "observed_layer": "JSON_SCHEMA",
            "accepted": False,
            "diagnostics": schema_diagnostics,
        }
    cross_record, semantic_policy = _cross_record_and_semantic_diagnostics(document)
    if cross_record:
        return {
            "observed_layer": "CROSS_RECORD",
            "accepted": False,
            "diagnostics": cross_record,
        }
    if semantic_policy:
        return {
            "observed_layer": "SEMANTIC_POLICY",
            "accepted": False,
            "diagnostics": semantic_policy,
        }
    return {"observed_layer": "ACCEPT", "accepted": True, "diagnostics": []}


def _validate_carrier(
    document: dict[str, Any], repository_root: str | Path = ROOT
) -> None:
    result = _evaluate_carrier_document(document, repository_root)
    if result["accepted"]:
        return
    first = result["diagnostics"][0]
    raise PCVPProducerError(
        "PCVP carrier failed canonical validation "
        f"at {result['observed_layer']}: {first['code']} "
        f"({first['subject']}: {first['detail']})"
    )


def _format_continuation_assurance_candidate(
    *,
    run_id: str,
    payload_hash: str,
    canonical_payload_valid: bool,
    handoff_allowed: bool,
    source_kind: str,
    unresolved_count: int,
) -> dict[str, Any]:
    """Format carrier data exclusively from already-derived Runtime facts."""
    if not isinstance(run_id, str) or not run_id.strip():
        raise PCVPProducerError("Runtime-derived run_id is required.")
    if not isinstance(payload_hash, str) or not SHA256.fullmatch(payload_hash):
        raise PCVPProducerError("Canonical payload SHA-256 is required.")
    if source_kind not in {
        "live_conversation",
        "fixture",
        "example",
        "test_vector",
    }:
        raise PCVPProducerError("Unsupported Runtime source_kind.")
    if (
        not isinstance(canonical_payload_valid, bool)
        or not isinstance(handoff_allowed, bool)
        or isinstance(unresolved_count, bool)
        or not isinstance(unresolved_count, int)
        or unresolved_count < 0
    ):
        raise PCVPProducerError("Runtime export facts are malformed.")

    suffix = _identity(run_id, payload_hash)
    payload_claim_id = f"CLM-ARCH-PAYLOAD-{suffix}"
    downstream_claim_id = f"CLM-ARCH-DOWNSTREAM-{suffix}"
    effect_id = f"EFF-ARCH-HANDOFF-{suffix}"
    authorization_id = f"AUTH-ARCH-HANDOFF-{suffix}"
    scope = (
        "Describe one validated PCVP carrier for lossless Project Gate transport "
        "to CE. The carrier cannot upgrade CE, Builder, Responsive, production, "
        "or any other downstream authority claim."
    )

    claims = [
        {
            "claim_id": payload_claim_id,
            "statement": (
                "The canonical Architect Stage Payload passed the existing "
                "Runtime-owned schema and semantic boundary."
            ),
            "criticality": "CRITICAL",
            "applicability_state": "APPLICABLE",
            "verification_state": (
                "VERIFIED" if canonical_payload_valid else "CONTRADICTED"
            ),
            "lifecycle_state": (
                "COMPLETE" if canonical_payload_valid else "ACTIVE"
            ),
            "evidence_refs": (
                [f"sha256:{payload_hash}"] if canonical_payload_valid else []
            ),
            "dependency_refs": [],
            "assumption_refs": [],
        },
        {
            "claim_id": downstream_claim_id,
            "statement": (
                "Constructability, Builder execution, Responsive completion, "
                "and production readiness remain unverified downstream."
            ),
            "criticality": "MATERIAL",
            "applicability_state": "APPLICABLE",
            "verification_state": "UNVERIFIED",
            "lifecycle_state": "ACTIVE",
            "evidence_refs": [],
            "dependency_refs": [payload_claim_id],
            "assumption_refs": [],
        },
    ]

    blocked = not canonical_payload_valid or not handoff_allowed
    if blocked:
        effect = {
            "effect_id": effect_id,
            "effect_class": "EXTERNAL_MUTATION",
            "depends_on_claim_ids": [payload_claim_id, downstream_claim_id],
            "continuation_state": "BLOCKED",
            "authorization_ref": None,
            "blocker_reason": (
                "MATERIAL_CONTRADICTION"
                if not canonical_payload_valid
                else "EXTERNAL_VERIFICATION_REQUIRED"
            ),
            "permitted_scope": None,
        }
        authorizations: list[dict[str, Any]] = []
        projection = "RED"
        yellow_substate = None
        derivation_reason = (
            "The existing Runtime did not authorize the Architect handoff."
        )
    else:
        effect = {
            "effect_id": effect_id,
            "effect_class": "EXTERNAL_MUTATION",
            "depends_on_claim_ids": [payload_claim_id, downstream_claim_id],
            "continuation_state": "CONTINUE",
            "authorization_ref": authorization_id,
            "blocker_reason": None,
            "permitted_scope": scope,
        }
        authorizations = [
            {
                "authorization_id": authorization_id,
                "basis": "NOT_REQUIRED",
                "status": "ACTIVE",
                "allowed_effect_ids": [effect_id],
                "allowed_effect_classes": [],
                "bound_unknown_ids": [f"UNRES-ARCH-DOWNSTREAM-{suffix}"],
                "bound_assumption_ids": [],
                "stage_scope": {
                    "from": SOURCE_STAGE,
                    "through": CONSUMER_STAGE,
                },
                "permitted_scope": scope,
                "valid_until_events": [
                    "NEW_MATERIAL_BLOCKER",
                    "OWNER_REVOCATION",
                    "CONTRADICTING_EVIDENCE",
                    "SCOPE_EXPANSION",
                    "AUTHORITY_CHANGE",
                    "SESSION_BOUNDARY_WITHOUT_VALID_HANDOFF",
                ],
            }
        ]
        projection = "YELLOW"
        yellow_substate = "CONTINUATION_AVAILABLE"
        derivation_reason = (
            "The existing Runtime authorized this Architect-to-Project-Gate "
            "handoff while downstream verification remains explicitly unresolved."
        )

    unresolved_items = [
        {
            "id": f"UNRES-ARCH-DOWNSTREAM-{suffix}",
            "class": "VERIFICATION_PATH_UNAVAILABLE",
            "statement": (
                "Downstream CE, Builder, Responsive, and production claims "
                "have not been verified by their owning authorities."
            ),
            "impact": (
                "The carrier may describe only the bounded Architect handoff; "
                "it cannot upgrade downstream claims."
            ),
        }
    ]
    if blocked:
        unresolved_items.append(
            {
                "id": f"UNRES-ARCH-HANDOFF-{suffix}",
                "class": (
                    "MATERIAL_CONTRADICTION"
                    if not canonical_payload_valid
                    else "VERIFICATION_PATH_UNAVAILABLE"
                ),
                "statement": (
                    "The canonical Architect handoff is not currently "
                    "authorized by the existing Runtime boundary."
                ),
                "impact": (
                    "No PCVP carrier may authorize or bypass the blocked "
                    "Producer Gate Export."
                ),
            }
        )
    if unresolved_count:
        unresolved_items.append(
            {
                "id": f"UNRES-ARCH-PAYLOAD-{suffix}",
                "class": "UPSTREAM_GENERATABLE",
                "statement": (
                    f"The Architect Payload carries {unresolved_count} "
                    "explicit unresolved evidence item(s)."
                ),
                "impact": (
                    "Only the existing Runtime classification controls whether "
                    "the handoff can proceed."
                ),
            }
        )

    return copy.deepcopy(
        {
            "policy_id": POLICY_ID,
            "policy_version": POLICY_VERSION,
            "source_stage": SOURCE_STAGE,
            "claims": claims,
            "effects": [effect],
            "authorizations": authorizations,
            "unresolved_items": unresolved_items,
            "stage_summary": {
                "owner_projection": projection,
                "yellow_substate": yellow_substate,
                "derived_from_claim_ids": [
                    payload_claim_id,
                    downstream_claim_id,
                ],
                "current_effect_id": effect_id,
                "lifecycle_state": "ACTIVE",
                "derivation_reason": derivation_reason,
            },
        }
    )


def _build_runtime_continuation_assurance(
    *,
    run_id: str,
    payload_hash: str,
    canonical_payload_valid: bool,
    handoff_allowed: bool,
    source_kind: str,
    unresolved_count: int,
) -> dict[str, Any]:
    """Build and canonically validate the official Runtime-owned carrier.

    This helper is intentionally private and has no repository-root/config/env
    override. The active Runtime Authority Manifest records this module because
    the terminal exporter depends on it directly.
    """
    verify_pcvp_resources(ROOT)
    carrier = _format_continuation_assurance_candidate(
        run_id=run_id,
        payload_hash=payload_hash,
        canonical_payload_valid=canonical_payload_valid,
        handoff_allowed=handoff_allowed,
        source_kind=source_kind,
        unresolved_count=unresolved_count,
    )
    _validate_carrier({"continuation_assurance": carrier}, ROOT)
    return copy.deepcopy(carrier)


__all__ = [
    "ACTIVATION_COMMIT",
    "ACTIVATION_EDGE",
    "ACTIVATION_ID",
    "ARCHITECTURE_LOCK_ID",
    "BOUNDARY_READER_STAGE",
    "CANONICAL_COMMIT",
    "CANONICAL_REPOSITORY",
    "PCVPProducerError",
    "POLICY_ID",
    "POLICY_VERSION",
    "verify_pcvp_resources",
]
