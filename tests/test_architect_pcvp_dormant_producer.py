from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from architect_pcvp_producer import (  # noqa: E402
    PCVPProducerError,
    PRODUCER_EMISSION_ENABLED,
    attach_to_export_if_enabled,
    build_continuation_assurance,
    verify_pcvp_resources,
)

PAYLOAD_HASH = "a" * 64


def _build(**changes: object) -> dict:
    values: dict[str, object] = {
        "run_id": "run-pcvp-architect-001",
        "payload_hash": PAYLOAD_HASH,
        "canonical_payload_valid": True,
        "handoff_allowed": True,
        "source_kind": "live_conversation",
        "unresolved_count": 0,
        "repository_root": ROOT,
    }
    values.update(changes)
    return build_continuation_assurance(**values)


def test_resources_are_exactly_pinned_and_emission_is_hard_disabled() -> None:
    result = verify_pcvp_resources(ROOT)
    assert result["producer_emission"] is False
    assert result["adoption_status"] == "not_yet_adopted"
    assert result["activation_effect"] == "NONE"
    assert len(result["resource_hashes"]) == 6
    assert PRODUCER_EMISSION_ENABLED is False


def test_dormant_export_path_preserves_existing_bytes_and_identity() -> None:
    export = {
        "schema_version": "producer-gate-export.v1",
        "run_id": "run-pcvp-architect-001",
        "handoff": {"allowed": True},
    }
    before = copy.deepcopy(export)
    observed = attach_to_export_if_enabled(
        export,
        run_id=export["run_id"],
        payload_hash=PAYLOAD_HASH,
        canonical_payload_valid=True,
        handoff_allowed=True,
        source_kind="live_conversation",
        unresolved_count=0,
        repository_root=ROOT,
    )
    assert observed is export
    assert observed == before
    assert "continuation_assurance" not in observed


def test_explicit_derivation_is_yellow_and_does_not_upgrade_downstream() -> None:
    carrier = _build()
    assert carrier["policy_id"] == "EV4-PCVP"
    assert carrier["policy_version"] == "1.0.0"
    assert carrier["source_stage"] == "ARCHITECT"
    assert carrier["effects"][0]["continuation_state"] == "CONTINUE"
    assert carrier["authorizations"][0]["basis"] == "NOT_REQUIRED"
    assert carrier["authorizations"][0]["stage_scope"] == {
        "from": "ARCHITECT",
        "through": "CONSTRUCTABILITY_ENGINEER",
    }
    assert carrier["stage_summary"]["owner_projection"] == "YELLOW"
    assert (
        carrier["stage_summary"]["yellow_substate"]
        == "CONTINUATION_AVAILABLE"
    )
    downstream = carrier["claims"][1]
    assert downstream["verification_state"] == "UNVERIFIED"
    assert not downstream["evidence_refs"]


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        (
            {"canonical_payload_valid": False},
            "MATERIAL_CONTRADICTION",
        ),
        (
            {
                "handoff_allowed": False,
                "source_kind": "fixture",
            },
            "EXTERNAL_VERIFICATION_REQUIRED",
        ),
    ],
)
def test_blocked_runtime_boundary_cannot_be_upgraded(
    changes: dict[str, object], reason: str
) -> None:
    carrier = _build(**changes)
    effect = carrier["effects"][0]
    assert effect["continuation_state"] == "BLOCKED"
    assert effect["authorization_ref"] is None
    assert effect["blocker_reason"] == reason
    assert carrier["authorizations"] == []
    assert carrier["stage_summary"]["owner_projection"] == "RED"


def test_derivation_is_stable_and_rejects_caller_carrier() -> None:
    first = _build()
    second = _build()
    assert json.dumps(first, sort_keys=True) == json.dumps(
        second, sort_keys=True
    )
    export = {"continuation_assurance": first}
    with pytest.raises(PCVPProducerError, match="Caller-supplied"):
        attach_to_export_if_enabled(
            export,
            run_id="run-pcvp-architect-001",
            payload_hash=PAYLOAD_HASH,
            canonical_payload_valid=True,
            handoff_allowed=True,
            source_kind="live_conversation",
            unresolved_count=0,
            repository_root=ROOT,
        )
