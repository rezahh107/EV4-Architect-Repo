"""Canonical classification of unresolved Architect handoff evidence."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

ARCHITECT_TRANSITION_BLOCKS = frozenset(
    {
        "architect_stage_payload_acceptance",
        "ce_transition",
    }
)
ARCHITECT_TRANSITION_DEADLINES = frozenset(
    {
        "project_gate_acceptance",
        "ce_transition",
    }
)


@dataclass(frozen=True)
class HandoffClassification:
    """Stable partition of unresolved evidence without mutating its items."""

    transition_blockers: tuple[Mapping[str, Any], ...]
    downstream_obligations: tuple[Mapping[str, Any], ...]


def _validated_blocks(item: Mapping[str, Any]) -> tuple[str, ...]:
    blocks = item.get("blocks")
    if not isinstance(blocks, list):
        raise TypeError("unresolved evidence blocks must be a list")
    if any(not isinstance(block, str) or not block for block in blocks):
        raise ValueError("unresolved evidence blocks must contain non-empty strings")
    return tuple(blocks)


def _validated_deadline(item: Mapping[str, Any]) -> str:
    deadline = item.get("required_before")
    if not isinstance(deadline, str) or not deadline:
        raise ValueError("unresolved evidence required_before must be a non-empty string")
    return deadline


def blocks_architect_transition(item: Mapping[str, Any]) -> bool:
    """Return whether one unresolved item blocks Payload acceptance or CE transition."""

    if not isinstance(item, Mapping):
        raise TypeError("unresolved evidence item must be a mapping")
    blocks = _validated_blocks(item)
    deadline = _validated_deadline(item)
    return bool(ARCHITECT_TRANSITION_BLOCKS.intersection(blocks)) or (
        deadline in ARCHITECT_TRANSITION_DEADLINES
    )


def partition_unresolved_evidence(
    items: Iterable[Mapping[str, Any]],
) -> HandoffClassification:
    """Partition unresolved evidence while preserving input order and item identity."""

    transition_blockers: list[Mapping[str, Any]] = []
    downstream_obligations: list[Mapping[str, Any]] = []
    for item in items:
        target = (
            transition_blockers
            if blocks_architect_transition(item)
            else downstream_obligations
        )
        target.append(item)
    return HandoffClassification(
        transition_blockers=tuple(transition_blockers),
        downstream_obligations=tuple(downstream_obligations),
    )
