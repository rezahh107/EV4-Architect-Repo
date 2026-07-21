"""Deterministic success and failure Bundle generation."""
from architect_validation_handoff import *  # noqa: F401,F403

def generate_transaction(sequence: Path, output: Path, root: Path = ROOT) -> dict[str, Any]:
    result = validate_sequence(sequence, root)
    if output.exists():
        shutil.rmtree(output)
    for folder in ["artifacts", "receipts", "boundaries", "anchors"]:
        (output / folder).mkdir(parents=True, exist_ok=True)
    artifact_entries = []
    receipt_entries = []
    processed_by_stage: dict[str, dict[str, Any]] = {}
    receipt_digests: dict[str, str] = {}
    for item in result["processed"]:
        artifact = item["artifact"]
        stage = artifact["stage_id"]
        prefix = PREFIX[stage]
        artifact_path = output / "artifacts" / f"{prefix}.json"
        artifact_path.write_bytes(item["path"].read_bytes())
        artifact_entries.append(file_entry(f"artifacts/{prefix}.json", artifact, item["digest"], "artifact"))
        receipt_path = output / "receipts" / f"{prefix}.receipt.json"
        write_json(receipt_path, item["receipt"])
        receipt_digest = sha_file(receipt_path)
        receipt_digests[stage] = receipt_digest
        receipt_entries.append(file_entry(f"receipts/{prefix}.receipt.json", item["receipt"], receipt_digest, "receipt"))
        processed_by_stage[stage] = item
    boundary_entries = []
    anchor_entries = []
    failure_event_path = None
    failure_event_digest = None
    if result["run_validation_status"] == "valid":
        for item in result["processed"]:
            artifact = item["artifact"]
            stage = artifact["stage_id"]
            prefix = PREFIX[stage]
            boundary = success_boundary_for(artifact, item["digest"], item["receipt"], receipt_digests[stage])
            boundary_path = output / "boundaries" / f"{prefix}.boundary.json"
            write_json(boundary_path, boundary)
            boundary_digest = sha_file(boundary_path)
            boundary_entries.append(file_entry(f"boundaries/{prefix}.boundary.json", boundary, boundary_digest, "boundary"))
            predecessor = processed_by_stage.get(PREDECESSOR.get(stage, ""), {}).get("artifact")
            anchor = success_anchor_for(artifact, predecessor, boundary, boundary_digest)
            anchor_path = output / "anchors" / f"{prefix}.anchor.json"
            write_json(anchor_path, anchor)
            anchor_entries.append(file_entry(f"anchors/{prefix}.anchor.json", anchor, sha_file(anchor_path), "anchor"))
        authorized_next_stage = NEXT_STAGE[result["processed"][-1]["artifact"]["stage_id"]]
        overall_status = "valid"
        repair_target = None
        authorization_valid = True
    else:
        failing = result["processed"][-1] if result["processed"] else None
        if not failing:
            raise ValueError("Cannot create failure evidence without exact failing Artifact bytes")
        failed_stage = result["failed_stage"]
        event = failure_event_for(result, receipt_digests[failed_stage])
        write_json(output / "failure-event.json", event)
        failure_event_path = "failure-event.json"
        failure_event_digest = sha_file(output / failure_event_path)
        boundary = repair_boundary_for(result, event, failure_event_digest, receipt_digests[failed_stage])
        boundary_path = output / "boundaries" / "repair.boundary.json"
        write_json(boundary_path, boundary)
        boundary_digest = sha_file(boundary_path)
        boundary_entries.append(file_entry("boundaries/repair.boundary.json", boundary, boundary_digest, "boundary"))
        predecessor = processed_by_stage.get(PREDECESSOR.get(failed_stage, ""), {}).get("artifact")
        anchor = repair_anchor_for(result, predecessor, boundary, boundary_digest, event, failure_event_digest)
        anchor_path = output / "anchors" / "repair.anchor.json"
        write_json(anchor_path, anchor)
        anchor_entries.append(file_entry("anchors/repair.anchor.json", anchor, sha_file(anchor_path), "anchor"))
        authorized_next_stage = None
        overall_status = "invalid"
        repair_target = result["repair_target_stage"]
        authorization_valid = False
    run_id = result["processed"][0]["artifact"]["run_id"] if result["processed"] else "unknown"
    manifest = {
        "bundle_schema": BUNDLE_SCHEMA,
        "bundle_id": f"asb-bundle-{run_id}-{overall_status}",
        "run_id": run_id,
        "validator_id": VALIDATOR_ID,
        "validator_version": VALIDATOR_VERSION,
        "determinism_profile": DETERMINISM_PROFILE,
        "stage_sequence": [item["artifact"]["stage_id"] for item in result["processed"]],
        "overall_status": overall_status,
        "bundle_integrity_status": "valid",
        "run_validation_status": result["run_validation_status"],
        "authorization_valid": authorization_valid,
        "authorized_next_stage": authorized_next_stage,
        "repair_target_stage": repair_target,
        "failure_event_path": failure_event_path,
        "failure_event_sha256": failure_event_digest,
        "artifacts": artifact_entries,
        "receipts": receipt_entries,
        "boundaries": boundary_entries,
        "anchors": anchor_entries,
        "bundle_content_digest": "0" * 64,
    }
    manifest["bundle_content_digest"] = manifest_digest(manifest)
    write_json(output / "manifest.json", manifest)
    carrier_diagnostics = validate_generated_carriers(output, root)
    if carrier_diagnostics:
        raise ValueError(json.dumps(carrier_diagnostics, sort_keys=True))
    return {
        "bundle_integrity_status": "valid",
        "run_validation_status": result["run_validation_status"],
        "authorization_valid": authorization_valid,
        "diagnostics": result["diagnostics"],
        "manifest": manifest,
    }

def safe_manifest_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and str(path) == value
