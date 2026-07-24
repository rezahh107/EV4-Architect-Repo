"""Functional handoff eligibility independent of execution context."""
from __future__ import annotations

from typing import Any

from architect_handoff_classification import partition_unresolved_evidence


def derive_handoff_eligibility(payload: dict[str, Any]) -> dict[str, Any]:
    classification = partition_unresolved_evidence(
        payload.get("unresolved_evidence", [])
    )
    blockers = list(classification.transition_blockers)
    if payload.get("payload_status") == "insufficient_evidence" and not blockers:
        blockers = [{"code": "ARCH_PAYLOAD_INSUFFICIENT_EVIDENCE"}]
    return {"would_allow": not blockers, "blockers": blockers}
