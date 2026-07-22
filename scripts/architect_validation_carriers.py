"""Failure Event, Receipt, and Boundary carrier generation."""
from architect_validation_sequence import *  # noqa: F401,F403

def receipt_ref(receipt: dict[str, Any], digest: str) -> dict[str, Any]:
    return {
        "receipt_id": receipt["receipt_id"],
        "receipt_schema": receipt["receipt_schema"],
        "receipt_sha256": digest,
        "validator_id": receipt["validator_id"],
        "validator_version": receipt["validator_version"],
        "status": receipt["status"],
    }

def failure_event_for(result: dict[str, Any], receipt_digest: str) -> dict[str, Any]:
    failing = result["processed"][-1]
    artifact = failing["artifact"]
    receipt = failing["receipt"]
    failed_stage = result["failed_stage"]
    repair_target = result["repair_target_stage"]
    first_invalid_index = stage_index(repair_target)
    failed_index = stage_index(failed_stage)
    reusable_prefix = EXECUTABLE_STAGES[:first_invalid_index]
    invalidated = EXECUTABLE_STAGES[first_invalid_index : max(failed_index + 1, first_invalid_index + 1)]
    identity_seed = {
        "run_id": artifact["run_id"],
        "failed_stage": failed_stage,
        "repair_target_stage": repair_target,
        "artifact_sha256": failing["digest"],
        "receipt_sha256": receipt_digest,
        "diagnostics": receipt["diagnostics"],
    }
    event_id = f"asb-failure-{artifact['run_id']}-{PREFIX[failed_stage]}-{sha_bytes(canonical_bytes(identity_seed))[:12]}"
    return {
        "failure_event_schema": FAILURE_EVENT_SCHEMA,
        "failure_event_id": event_id,
        "run_id": artifact["run_id"],
        "failed_stage": failed_stage,
        "repair_target_stage": repair_target,
        "failing_artifact": {
            "artifact_id": artifact["artifact_id"],
            "artifact_schema": artifact["artifact_schema"],
            "artifact_sha256": failing["digest"],
            "stage_id": failed_stage,
        },
        "failing_receipt": {
            "receipt_id": receipt["receipt_id"],
            "receipt_schema": receipt["receipt_schema"],
            "receipt_sha256": receipt_digest,
            "validator_id": receipt["validator_id"],
            "validator_version": receipt["validator_version"],
            "status": receipt["status"],
        },
        "diagnostics": [
            {
                "code": item["code"],
                "rule_id": item["rule_id"],
                "stage_id": item["stage_id"],
                "path": item["path"],
                "repair_target_stage": item["repair_target_stage"],
            }
            for item in receipt["diagnostics"]
        ],
        "invalidation_scope": {
            "first_invalid_stage": repair_target,
            "invalidated_downstream_stages": invalidated,
            "reusable_validated_prefix": reusable_prefix,
            "downstream_authorization_revoked": True,
        },
    }

def success_boundary_for(
    artifact: dict[str, Any], artifact_digest: str, receipt: dict[str, Any], receipt_digest: str
) -> dict[str, Any]:
    stage = artifact["stage_id"]
    seed = f"{artifact_digest}:{receipt_digest}:{successor_stage(stage)}".encode()
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "boundary_id": f"asb-boundary-{artifact['run_id']}-{PREFIX[stage]}-{sha_bytes(seed)[:12]}",
        "run_id": artifact["run_id"],
        "transition": "next_stage",
        "source_stage": stage,
        "failed_stage": None,
        "target_stage": successor_stage(stage),
        "repair_target_stage": None,
        "artifact": {
            "artifact_id": artifact["artifact_id"],
            "artifact_schema": artifact["artifact_schema"],
            "artifact_sha256": artifact_digest,
        },
        "receipt": receipt_ref(receipt, receipt_digest),
        "failure_event_ref": None,
        "authorization": {
            "next_stage_authorized": True,
            "authorization_reason": "regenerated_valid_bundle",
        },
    }

def repair_boundary_for(
    result: dict[str, Any], failure_event: dict[str, Any], failure_event_digest: str, receipt_digest: str
) -> dict[str, Any]:
    failing = result["processed"][-1]
    artifact = failing["artifact"]
    receipt = failing["receipt"]
    stage = result["failed_stage"]
    repair = result["repair_target_stage"]
    seed = f"{failing['digest']}:{receipt_digest}:{failure_event_digest}:{repair}".encode()
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "boundary_id": f"asb-repair-{artifact['run_id']}-{PREFIX[stage]}-{sha_bytes(seed)[:12]}",
        "run_id": artifact["run_id"],
        "transition": "repair",
        "source_stage": stage,
        "failed_stage": stage,
        "target_stage": None,
        "repair_target_stage": repair,
        "artifact": {
            "artifact_id": artifact["artifact_id"],
            "artifact_schema": artifact["artifact_schema"],
            "artifact_sha256": failing["digest"],
        },
        "receipt": receipt_ref(receipt, receipt_digest),
        "failure_event_ref": {
            "failure_event_id": failure_event["failure_event_id"],
            "failure_event_schema": failure_event["failure_event_schema"],
            "failure_event_sha256": failure_event_digest,
        },
        "authorization": {
            "next_stage_authorized": False,
            "authorization_reason": "validation_failure_requires_repair",
        },
    }
