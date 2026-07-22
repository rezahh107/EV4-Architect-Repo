"""Canonical Pipeline Manifest and Validation Profiles Registry loader.

The Manifest owns topology and Stage versions.  The Registry owns executable
validation capability.  This module derives runtime views from both; it does
not contain an independently maintained Stage table.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path("manifests/architect-pipeline-manifest.v1.json")
REGISTRY_PATH = Path("manifests/architect-stage-validation-profiles.v1.json")


@dataclass(frozen=True)
class PipelineAuthority:
    manifest: dict[str, Any]
    registry: dict[str, Any]
    stage_order: tuple[str, ...]
    stage_records: dict[str, dict[str, Any]]
    profiles: dict[str, dict[str, Any]]
    implemented_stage_order: tuple[str, ...]
    terminal_stage: str

    def stage_version(self, stage_id: str) -> str:
        return self.stage_records[stage_id]["stage_version"]

    def predecessor(self, stage_id: str) -> str | None:
        index = self.stage_order.index(stage_id)
        return self.stage_order[index - 1] if index else None

    def successor(self, stage_id: str) -> str | None:
        return self.stage_records[stage_id]["next_stage"]

    def stage_index(self, stage_id: str | None) -> int:
        try:
            return self.stage_order.index(stage_id or "")
        except ValueError:
            return len(self.stage_order) + 1

    def implemented_index(self, stage_id: str | None) -> int:
        try:
            return self.implemented_stage_order.index(stage_id or "")
        except ValueError:
            return len(self.implemented_stage_order) + 1

    def prefix(self, stage_id: str) -> str:
        if stage_id not in self.stage_records:
            raise KeyError(stage_id)
        return stage_id.removeprefix("/")

    def is_implemented(self, stage_id: str) -> bool:
        return self.profiles[stage_id]["validation"]["status"] == "full_transaction_implemented"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_pipeline_authority(root: Path) -> PipelineAuthority:
    manifest = _read_json(root / MANIFEST_PATH)
    registry = _read_json(root / REGISTRY_PATH)
    stages = manifest.get("project_execution_stages", [])
    if not stages:
        raise ValueError("Manifest must declare project_execution_stages")

    stage_order = tuple(stage.get("stage_id") for stage in stages)
    if any(not isinstance(stage, str) for stage in stage_order) or len(set(stage_order)) != len(stage_order):
        raise ValueError("Manifest Stage identities must be unique strings")
    expected_ordinals = list(range(1, len(stages) + 1))
    if [stage.get("ordinal") for stage in stages] != expected_ordinals:
        raise ValueError("Manifest ordinals must be complete and ordered")
    for index, stage in enumerate(stages):
        expected_successor = stage_order[index + 1] if index + 1 < len(stage_order) else None
        if stage.get("next_stage") != expected_successor:
            raise ValueError(f"Manifest next_stage drift for {stage_order[index]}")
    terminal = stage_order[-1]
    if manifest.get("final_project_gate_export_stage") != terminal:
        raise ValueError("Manifest terminal Stage does not match final_project_gate_export_stage")

    profile_rows = registry.get("profiles", [])
    profile_ids = [row.get("stage_id") for row in profile_rows]
    if len(profile_ids) != len(set(profile_ids)):
        raise ValueError("Registry Stage identities must be unique")
    if set(profile_ids) != set(stage_order):
        raise ValueError("Manifest and Registry Stage sets differ")
    profiles = {row["stage_id"]: row for row in profile_rows}

    implemented: list[str] = []
    for stage_id in stage_order:
        profile = profiles[stage_id]
        validation = profile["validation"]
        receipt = profile["receipt"]
        bundle = profile["bundle"]
        repair = profile["repair"]
        status = validation["status"]
        unresolved = profile["grounding"]["unresolved_semantic_decisions"]
        if status == "full_transaction_implemented":
            if not all(
                [
                    validation["executable"],
                    validation["authorization_capable"],
                    receipt["supported"],
                    bundle["supported"],
                    bundle["independent_regeneration"],
                    repair["ownership_status"] == "deterministic",
                    profile["artifact"]["schema_path"] != "not_implemented",
                    validation["semantic_handler"] != "not_implemented",
                ]
            ):
                raise ValueError(f"Implemented profile is incomplete: {stage_id}")
            if unresolved:
                raise ValueError(
                    f"Implemented profile retains unresolved semantic decisions: {stage_id}"
                )
            implemented.append(stage_id)
        elif any(
            [
                validation["executable"],
                validation["authorization_capable"],
                receipt["supported"],
                bundle["supported"],
                bundle["independent_regeneration"],
            ]
        ):
            raise ValueError(f"Non-implemented profile claims executable authority: {stage_id}")
        if status == "blocked_missing_semantics" and not unresolved:
            raise ValueError(
                f"Blocked-missing-semantics profile must name missing decisions: {stage_id}"
            )
        if status == "terminal" and stage_id != terminal:
            raise ValueError(f"Only the Manifest terminal Stage may use terminal status: {stage_id}")
        if status != "terminal" and stage_id == terminal:
            raise ValueError("Manifest terminal Stage must use terminal validation status")

    if implemented:
        implemented_indices = [stage_order.index(stage_id) for stage_id in implemented]
        expected_indices = list(
            range(implemented_indices[0], implemented_indices[-1] + 1)
        )
        if implemented_indices != expected_indices:
            raise ValueError(
                "Implemented Validation Profiles must form one contiguous Manifest segment"
            )

    return PipelineAuthority(
        manifest=manifest,
        registry=registry,
        stage_order=stage_order,
        stage_records={row["stage_id"]: row for row in stages},
        profiles=profiles,
        implemented_stage_order=tuple(implemented),
        terminal_stage=terminal,
    )


def exposed_profile(authority: PipelineAuthority, stage_id: str) -> dict[str, Any]:
    """Return one Registry profile with topology deterministically exposed."""
    stage = authority.stage_records[stage_id]
    return {
        **authority.profiles[stage_id],
        "ordinal": stage["ordinal"],
        "mandatory": stage["mandatory"],
        "stage_version": stage["stage_version"],
        "terminal": stage_id == authority.terminal_stage,
        "topology": {
            "predecessor": authority.predecessor(stage_id),
            "successor": authority.successor(stage_id),
        },
    }
