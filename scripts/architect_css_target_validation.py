"""Shared CSS target referential validation for Architect Payloads."""
from __future__ import annotations

from collections import deque
from typing import Any

from architect_runtime_errors import RuntimeDiagnostic


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def approved_reachable_node_ids(payload: dict[str, Any]) -> frozenset[str]:
    """Return only approved structure nodes reachable from the declared root."""

    structure = _as_dict(payload.get("approved_structure_model"))
    root_id = structure.get("root_node_id")
    rows = _as_list(structure.get("structure_nodes"))
    by_id = {
        row.get("node_id"): row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("node_id"), str)
        and row.get("node_id")
    }
    if not isinstance(root_id, str) or not root_id or root_id not in by_id:
        return frozenset()
    reachable: set[str] = set()
    queue: deque[str] = deque([root_id])
    while queue:
        node_id = queue.popleft()
        if node_id in reachable or node_id not in by_id:
            continue
        reachable.add(node_id)
        children = by_id[node_id].get("children")
        if isinstance(children, list):
            queue.extend(
                sorted(
                    child
                    for child in children
                    if isinstance(child, str) and child and child in by_id
                )
            )
    return frozenset(reachable)


def validate_css_target_references(payload: Any) -> list[RuntimeDiagnostic]:
    """Validate every CSS target against the reachable approved Build Tree."""

    if not isinstance(payload, dict):
        return []
    approved = approved_reachable_node_ids(payload)
    css = _as_dict(_as_dict(payload.get("architect_intent")).get("scoped_css_intent"))
    needs = _as_list(css.get("css_need_map"))
    diagnostics: list[RuntimeDiagnostic] = []
    for index, item in enumerate(needs):
        if not isinstance(item, dict):
            continue
        path = (
            "$.architect_intent.scoped_css_intent.css_need_map"
            f"[{index}].target_node_id"
        )
        target = item.get("target_node_id")
        if not isinstance(target, str) or not target.strip():
            diagnostics.append(
                RuntimeDiagnostic(
                    "PAYLOAD_CSS_TARGET_REQUIRED",
                    "CSS need target_node_id must be a non-empty approved Build Tree node",
                    path=path,
                    stage_id="/implementation",
                )
            )
        elif target not in approved:
            diagnostics.append(
                RuntimeDiagnostic(
                    "PAYLOAD_CSS_TARGET_UNKNOWN",
                    f"CSS target is not a reachable approved Build Tree node: {target}",
                    path=path,
                    stage_id="/implementation",
                )
            )
    return sorted(
        diagnostics,
        key=lambda item: (item.path or "", item.code, item.message),
    )
