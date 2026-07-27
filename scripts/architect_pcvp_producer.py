"""Hard-disabled EV4-PCVP producer for the Architect → Project Gate edge."""
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
SOURCE_STAGE = "ARCHITECT"
BOUNDARY_READER_STAGE = "PROJECT_GATE"
CONSUMER_STAGE = "CONSTRUCTABILITY_ENGINEER"
PRODUCER_EMISSION_ENABLED = False
ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = Path("contracts/pcvp/architect-producer.lock.json")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PCVPProducerError(RuntimeError):
    """Raised when dormant producer identity or derivation fails closed."""


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


def verify_pcvp_resources(repository_root: str | Path = ROOT) -> dict[str, Any]:
    """Verify the immutable Model Policy, profile, and schema byte pins."""
    root = Path(repository_root)
    lock = _load_json(root / LOCK_PATH)
    expected_policy = {
        "id": POLICY_ID,
        "version": POLICY_VERSION,
        "adoption_status": "not_yet_adopted",
        "activation": "NONE",
    }
    if (
        not isinstance(lock, dict)
        or lock.get("schema_version")
        != "ev4-pcvp-architect-producer-lock.v1"
        or lock.get("architecture_lock_id") != ARCHITECTURE_LOCK_ID
        or lock.get("policy") != expected_policy
    ):
        raise PCVPProducerError("PCVP Architect producer lock identity drifted.")

    canonical = lock.get("canonical")
    if not isinstance(canonical, dict) or (
        canonical.get("repository") != CANONICAL_REPOSITORY
        or canonical.get("commit_sha") != CANONICAL_COMMIT
        or canonical.get("bundle_root") != "kernel/pcvp/v1.0.0/bundle"
    ):
        raise PCVPProducerError("PCVP canonical owner or immutable commit drifted.")

    producer = lock.get("producer")
    if not isinstance(producer, dict) or producer != {
        "repository": "rezahh107/EV4-Architect-Repo",
        "source_stage": SOURCE_STAGE,
        "boundary_reader_stage": BOUNDARY_READER_STAGE,
        "consumer_stage": CONSUMER_STAGE,
        "carrier_path": "continuation_assurance",
        "emission_enabled": False,
        "caller_override_allowed": False,
    }:
        raise PCVPProducerError(
            "PCVP producer must remain hard-disabled without caller override."
        )

    verification = lock.get("verification")
    if not isinstance(verification, dict) or verification != {
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
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/"
        "authorization.schema.json",
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/claim.schema.json",
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/effect.schema.json",
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/handoff.schema.json",
    }
    if set(observed) != required_paths:
        raise PCVPProducerError("PCVP resource set drifted.")
    return {
        "architecture_lock_id": ARCHITECTURE_LOCK_ID,
        "canonical_commit": CANONICAL_COMMIT,
        "resource_hashes": dict(sorted(observed.items())),
        "producer_emission": False,
        "adoption_status": "not_yet_adopted",
        "activation_effect": "NONE",
    }


def _validate_carrier(
    document: dict[str, Any], repository_root: str | Path
) -> None:
    root = Path(repository_root)
    vendor = root / "contracts/pcvp/vendor/decision-kernel/v1.0.0"
    schemas: dict[str, dict[str, Any]] = {}
    for name in (
        "authorization.schema.json",
        "claim.schema.json",
        "effect.schema.json",
        "handoff.schema.json",
    ):
        value = _load_json(vendor / name)
        if not isinstance(value, dict):
            raise PCVPProducerError(f"PCVP schema is not an object: {name}")
        Draft202012Validator.check_schema(value)
        schemas[name] = value

    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(
            schema["$id"], Resource.from_contents(schema)
        )
    validator = Draft202012Validator(
        schemas["handoff.schema.json"], registry=registry
    )
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.absolute_path) or "$"
        raise PCVPProducerError(
            f"Generated PCVP carrier failed canonical schema at {path}: "
            f"{first.message}"
        )


def build_continuation_assurance(
    *,
    run_id: str,
    payload_hash: str,
    canonical_payload_valid: bool,
    handoff_allowed: bool,
    source_kind: str,
    unresolved_count: int,
    repository_root: str | Path = ROOT,
) -> dict[str, Any]:
    """Derive a bounded carrier from existing Runtime-owned export facts."""
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

    verify_pcvp_resources(repository_root)
    suffix = _identity(run_id, payload_hash)
    payload_claim_id = f"CLM-ARCH-PAYLOAD-{suffix}"
    downstream_claim_id = f"CLM-ARCH-DOWNSTREAM-{suffix}"
    effect_id = f"EFF-ARCH-HANDOFF-{suffix}"
    authorization_id = f"AUTH-ARCH-HANDOFF-{suffix}"
    scope = (
        "Attach one PCVP carrier to the existing Runtime-authorized Architect "
        "Producer Gate Export for lossless Project Gate transport to CE; no "
        "handoff eligibility or downstream authority may be created or upgraded."
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
            "The existing Runtime authorized this handoff, while downstream "
            "verification remains explicitly unresolved."
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

    document = {
        "continuation_assurance": {
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
    }
    _validate_carrier(document, repository_root)
    return copy.deepcopy(document["continuation_assurance"])


def attach_to_export_if_enabled(
    export: dict[str, Any],
    *,
    run_id: str,
    payload_hash: str,
    canonical_payload_valid: bool,
    handoff_allowed: bool,
    source_kind: str,
    unresolved_count: int,
    repository_root: str | Path = ROOT,
) -> dict[str, Any]:
    """Attach only after a dedicated code change enables producer emission."""
    if not isinstance(export, dict):
        raise PCVPProducerError("Producer Gate Export must be an object.")
    if "continuation_assurance" in export:
        raise PCVPProducerError(
            "Caller-supplied continuation_assurance is forbidden."
        )
    if not PRODUCER_EMISSION_ENABLED:
        return export
    export["continuation_assurance"] = build_continuation_assurance(
        run_id=run_id,
        payload_hash=payload_hash,
        canonical_payload_valid=canonical_payload_valid,
        handoff_allowed=handoff_allowed,
        source_kind=source_kind,
        unresolved_count=unresolved_count,
        repository_root=repository_root,
    )
    return export


__all__ = [
    "ARCHITECTURE_LOCK_ID",
    "BOUNDARY_READER_STAGE",
    "CANONICAL_COMMIT",
    "CANONICAL_REPOSITORY",
    "PCVPProducerError",
    "POLICY_ID",
    "POLICY_VERSION",
    "PRODUCER_EMISSION_ENABLED",
    "attach_to_export_if_enabled",
    "build_continuation_assurance",
    "verify_pcvp_resources",
]
