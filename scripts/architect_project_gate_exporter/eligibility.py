"""Functional handoff eligibility independent of execution context."""
from __future__ import annotations

from typing import Any


def derive_handoff_eligibility(payload: dict[str, Any]) -> dict[str, Any]:
    unresolved = [
        item for item in payload.get("unresolved_evidence", []) if isinstance(item, dict)
    ]
    boundaries = {"architect_stage_payload_acceptance", "ce_transition"}
    blockers = [
        item for item in unresolved
        if boundaries.intersection(item.get("blocks", []))
        or item.get("required_before") in {"project_gate_acceptance", "ce_transition"}
    ]
    if payload.get("payload_status") == "insufficient_evidence":
        blockers = [{"code": "ARCH_PAYLOAD_INSUFFICIENT_EVIDENCE"}, *blockers]
    return {"would_allow": not blockers, "blockers": blockers}
