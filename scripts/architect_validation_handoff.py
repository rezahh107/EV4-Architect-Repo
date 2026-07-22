"""Evidence-derived handoff state, Anchors, and carrier checks."""
from architect_validation_carriers import *  # noqa: F401,F403

def unknown_state(artifact: dict[str, Any], unknown_id: str) -> tuple[str, list[str], bool]:
    stage = artifact["stage_id"]
    payload = artifact["payload"]
    if stage == "/decompose":
        for item in payload.get("unknowns", []):
            if item.get("unknown_id") == unknown_id:
                state = "blocked" if item.get("blocking") else "unknown"
                return state, [], bool(item.get("blocking"))
    if stage == "/architectures":
        for item in payload.get("unknown_propagation_ledger", []):
            if item.get("unknown_id") == unknown_id:
                lifecycle = item.get("state")
                refs = sorted(
                    set(item.get("evidence_refs", []))
                    | set(item.get("resolving_evidence_refs", []))
                )
                if lifecycle == "blocking":
                    return "blocked", refs, True
                if lifecycle == "resolved_with_evidence":
                    return "confirmed", refs, False
                if lifecycle in {"not_applicable", "stale"}:
                    return "not_applicable", refs, False
                return "unknown", refs, False
    if stage == "/score-evidence":
        for item in payload.get("uncertainty_register", []):
            if isinstance(item, dict) and item.get("unknown_id") == unknown_id:
                return "unknown", list(item.get("evidence_refs", [])), bool(item.get("blocking", False))
    return "unknown", [], False

def active_unknown_ids(artifact: dict[str, Any]) -> set[str]:
    stage = artifact["stage_id"]
    payload = artifact["payload"]
    if stage == "/decompose":
        return {str(item["unknown_id"]) for item in payload.get("unknowns", [])}
    if stage == "/architectures":
        return {
            str(item["unknown_id"])
            for item in payload.get("unknown_propagation_ledger", [])
            if item.get("state") in ACTIVE_UNKNOWN_STATES or item.get("handling") in ACTIVE_UNKNOWN_STATES
        }
    if stage == "/score-evidence":
        return {
            str(item["unknown_id"])
            for item in payload.get("uncertainty_register", [])
            if isinstance(item, dict) and item.get("unknown_id")
        }
    return set()

def handoff_state_for(
    artifact: dict[str, Any],
    predecessor: dict[str, Any] | None,
    receipt_status: str,
    transition: str,
    authorized: bool,
    repair_target: str | None,
) -> dict[str, Any]:
    current_ids = active_unknown_ids(artifact)
    previous_ids = active_unknown_ids(predecessor) if predecessor else set()
    # Failure and Stage 5 carriers cannot erase active predecessor unknowns merely
    # because the failing/current payload omitted its own uncertainty collection.
    if transition == "repair" or artifact["stage_id"] == "/score-audit":
        current_ids |= previous_ids
    all_ids = sorted(current_ids | previous_ids)
    confidence_delta = []
    critical_unknowns = []
    blocking_items = []
    for unknown_id in all_ids:
        prev_state, prev_refs, prev_blocking = unknown_state(predecessor, unknown_id) if predecessor else ("unknown", [], False)
        cur_state, cur_refs, cur_blocking = unknown_state(artifact, unknown_id)
        if unknown_id not in previous_ids:
            direction = "new_unknown"
        elif unknown_id not in current_ids and cur_refs:
            direction = "resolved"
        elif prev_state != cur_state:
            direction = "increased" if prev_state == "unknown" and cur_state in {"likely", "confirmed"} else "decreased"
        else:
            direction = "unchanged"
        evidence_refs = sorted(set(prev_refs + cur_refs))
        confidence_delta.append(
            {
                "subject_id": unknown_id,
                "subject_type": "unknown",
                "previous_confidence": prev_state if prev_state in CONFIDENCE else "unknown",
                "current_confidence": cur_state if cur_state in CONFIDENCE else "unknown",
                "direction": direction,
                "reason": "derived_from_validated_stage_artifact",
                "evidence_refs": evidence_refs,
                "downstream_impact": "blocks_or_caps_downstream_work" if cur_blocking else "must_remain_visible_downstream",
            }
        )
        if unknown_id in current_ids:
            item = {"unknown_id": unknown_id, "state": cur_state, "evidence_refs": evidence_refs}
            critical_unknowns.append(item)
            if cur_blocking:
                blocking_items.append(item)
    stage = artifact["stage_id"]
    earliest = repair_target or stage
    return {
        "critical_unknowns": critical_unknowns,
        "blocking_items": blocking_items,
        "confidence_delta": confidence_delta,
        "gate_results": {
            "receipt_status": receipt_status,
            "boundary_transition": transition,
            "next_stage_authorized": authorized,
        },
        "audit_flags": ["machine_authorization_forbidden"] if authorized else ["repair_required", "machine_authorization_forbidden"],
        "required_user_confirmations": [],
        "partial_rerun_state": {
            "reusable_until": predecessor["stage_id"] if predecessor and repair_target and stage_index(predecessor["stage_id"]) < stage_index(repair_target) else None,
            "invalidation_triggers": ["artifact_bytes_changed", "upstream_lineage_changed", "diagnostic_ownership_changed"],
            "earliest_safe_rerun_stage": earliest,
            "downstream_payloads_dependent_on_this_stage": EXECUTABLE_STAGES[stage_index(stage) + 1 :],
        },
        "stage_boundary": {
            "allowed_work": [successor_stage(stage)] if authorized else [f"repair:{earliest}"],
            "forbidden_work": ["independent_authorization", "downstream_reconstruction"],
            "stop_conditions": ["bundle_integrity_invalid"] if authorized else ["repair_not_completed", "fresh_validation_missing"],
        },
    }

def success_anchor_for(
    artifact: dict[str, Any],
    predecessor: dict[str, Any] | None,
    boundary: dict[str, Any],
    boundary_digest: str,
) -> dict[str, Any]:
    stage = artifact["stage_id"]
    return {
        "anchor_schema": ANCHOR_SCHEMA,
        "anchor_id": f"asb-anchor-{artifact['run_id']}-{PREFIX[stage]}-{boundary_digest[:12]}",
        "run_id": artifact["run_id"],
        "anchor_type": "NEXT_STAGE_ANCHOR",
        "source_stage": stage,
        "target_stage": successor_stage(stage),
        "repair_target_stage": None,
        "boundary_ref": {
            "boundary_id": boundary["boundary_id"],
            "boundary_schema": boundary["boundary_schema"],
            "boundary_sha256": boundary_digest,
        },
        "failure_event_ref": None,
        "handoff_state": handoff_state_for(artifact, predecessor, "valid", "next_stage", True, None),
    }

def repair_anchor_for(
    result: dict[str, Any],
    predecessor: dict[str, Any] | None,
    boundary: dict[str, Any],
    boundary_digest: str,
    event: dict[str, Any],
    event_digest: str,
) -> dict[str, Any]:
    artifact = result["processed"][-1]["artifact"]
    stage = result["failed_stage"]
    repair = result["repair_target_stage"]
    return {
        "anchor_schema": ANCHOR_SCHEMA,
        "anchor_id": f"asb-repair-anchor-{artifact['run_id']}-{PREFIX[stage]}-{boundary_digest[:12]}",
        "run_id": artifact["run_id"],
        "anchor_type": "REPAIR_ANCHOR",
        "source_stage": stage,
        "target_stage": None,
        "repair_target_stage": repair,
        "boundary_ref": {
            "boundary_id": boundary["boundary_id"],
            "boundary_schema": boundary["boundary_schema"],
            "boundary_sha256": boundary_digest,
        },
        "failure_event_ref": {
            "failure_event_id": event["failure_event_id"],
            "failure_event_schema": event["failure_event_schema"],
            "failure_event_sha256": event_digest,
        },
        "handoff_state": handoff_state_for(artifact, predecessor, "invalid", "repair", False, repair),
    }

def file_entry(path: str, value: dict[str, Any], digest: str, kind: str) -> dict[str, Any]:
    identity_key = {
        "artifact": ("artifact_id", "artifact_schema"),
        "receipt": ("receipt_id", "receipt_schema"),
        "boundary": ("boundary_id", "boundary_schema"),
        "anchor": ("anchor_id", "anchor_schema"),
    }[kind]
    id_key, schema_key = identity_key
    return {"path": path, "sha256": digest, "id": value[id_key], "schema": value[schema_key]}

def manifest_digest(manifest: dict[str, Any]) -> str:
    clone = json.loads(json.dumps(manifest))
    clone["bundle_content_digest"] = "0" * 64
    return sha_bytes(canonical_bytes(clone))

def validate_generated_carriers(output: Path, root: Path = ROOT) -> list[dict[str, Any]]:
    validators = schema_validators(root)
    diagnostics: list[dict[str, Any]] = []
    manifest = load_json(output / "manifest.json")
    diagnostics.extend(schema_diagnostics(validators["bundle"], manifest, "bundle", "$", "/decompose"))
    mappings = [
        ("receipt", "receipts", "*.receipt.json"),
        ("failure_event", ".", "failure-event.json"),
        ("boundary", "boundaries", "*.boundary.json"),
        ("anchor", "anchors", "*.anchor.json"),
    ]
    for kind, folder, pattern in mappings:
        for path in (output / folder).glob(pattern):
            value = load_json(path)
            stage = value.get("stage_id") or value.get("source_stage") or value.get("failed_stage") or "bundle"
            repair = value.get("repair_target_stage") or (stage if stage in EXECUTABLE_STAGES else "/decompose")
            diagnostics.extend(schema_diagnostics(validators[kind], value, stage, f"$/{path.relative_to(output)}", repair))
    return sort_diagnostics(diagnostics)
