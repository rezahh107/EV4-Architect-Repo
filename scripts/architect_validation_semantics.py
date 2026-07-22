"""Artifact lineage and semantic validation."""
from architect_validation_common import *  # noqa: F401,F403


def artifact_ref(artifact: dict[str, Any], digest: str) -> dict[str, Any]:
    return {
        "run_id": artifact["run_id"],
        "artifact_id": artifact["artifact_id"],
        "artifact_schema": artifact["artifact_schema"],
        "artifact_sha256": digest,
        "source_stage": artifact["stage_id"],
    }


def receipt_for(
    artifact: dict[str, Any], digest: str, diagnostics: list[dict[str, Any]]
) -> dict[str, Any]:
    ordered = sort_diagnostics(diagnostics)
    return {
        "receipt_schema": RECEIPT_SCHEMA,
        "receipt_id": f"asb-receipt-{artifact.get('run_id','unknown')}-{artifact.get('artifact_id','unknown')}-{digest[:12]}",
        "run_id": artifact.get("run_id", "unknown"),
        "validator_id": VALIDATOR_ID,
        "validator_version": VALIDATOR_VERSION,
        "artifact_id": artifact.get("artifact_id", "unknown"),
        "artifact_schema": artifact.get("artifact_schema", ARTIFACT_SCHEMA),
        "artifact_sha256": digest,
        "stage_id": artifact.get("stage_id", "/decompose"),
        "status": "valid" if not ordered else "invalid",
        "diagnostics": ordered,
    }


def validate_source_reference(
    artifact: dict[str, Any],
    predecessor: dict[str, Any],
    predecessor_digest: str,
) -> list[dict[str, Any]]:
    stage = artifact["stage_id"]
    predecessor_stage = predecessor["stage_id"]
    expected = artifact_ref(predecessor, predecessor_digest)
    matches = [
        ref
        for ref in artifact.get("source_artifacts", [])
        if ref.get("source_stage") == predecessor_stage
    ]
    if not matches:
        return [
            diagnostic(
                "ASB-SOURCE-REF-MISSING",
                "ASB-R05",
                stage,
                "$/source_artifacts",
                json.dumps(expected, sort_keys=True),
                "missing",
                predecessor_stage,
            )
        ]
    if expected not in matches:
        return [
            diagnostic(
                "ASB-SOURCE-REF-MISMATCH",
                "ASB-R05",
                stage,
                "$/source_artifacts",
                json.dumps(expected, sort_keys=True),
                json.dumps(matches[0], sort_keys=True),
                predecessor_stage,
            )
        ]
    return []


def validate_unknown_lifecycle(row: dict[str, Any], index: int) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    state = row.get("state")
    handling = row.get("handling")
    path = f"$/payload/unknown_propagation_ledger/{index}"
    if state not in UNKNOWN_STATES or handling not in UNKNOWN_STATES or state != handling:
        diagnostics.append(
            diagnostic(
                "ASB-UNKNOWN-RESOLUTION-UNSUPPORTED",
                "ASB-R04",
                "/architectures",
                path,
                "matching supported state and handling",
                f"state={state};handling={handling}",
                "/architectures",
            )
        )
        return diagnostics
    evidence_refs = {
        ref for ref in row.get("evidence_refs", []) if isinstance(ref, str) and ref
    }
    if state == "resolved_with_evidence":
        resolving_refs = row.get("resolving_evidence_refs", [])
        valid_resolving_refs = {
            ref for ref in resolving_refs if isinstance(ref, str) and ref
        } if isinstance(resolving_refs, list) else set()
        if (
            not valid_resolving_refs
            or valid_resolving_refs != set(resolving_refs)
            or not valid_resolving_refs.issubset(evidence_refs)
            or not isinstance(row.get("resolution_reason"), str)
            or not row.get("resolution_reason", "").strip()
        ):
            diagnostics.append(
                diagnostic(
                    "ASB-UNKNOWN-RESOLUTION-EVIDENCE-MISSING",
                    "ASB-R04",
                    "/architectures",
                    path,
                    "non-empty resolution_reason and resolving_evidence_refs declared in evidence_refs",
                    json.dumps(
                        {
                            "resolution_reason": row.get("resolution_reason"),
                            "resolving_evidence_refs": row.get("resolving_evidence_refs"),
                            "evidence_refs": row.get("evidence_refs"),
                        },
                        sort_keys=True,
                    ),
                    "/architectures",
                )
            )
    elif state in {"not_applicable", "stale"}:
        if (
            not evidence_refs
            or not isinstance(row.get("resolution_reason"), str)
            or not row.get("resolution_reason", "").strip()
        ):
            diagnostics.append(
                diagnostic(
                    "ASB-UNKNOWN-RESOLUTION-EVIDENCE-MISSING",
                    "ASB-R04",
                    "/architectures",
                    path,
                    "non-empty resolution_reason and evidence_refs",
                    json.dumps(
                        {
                            "resolution_reason": row.get("resolution_reason"),
                            "evidence_refs": row.get("evidence_refs"),
                        },
                        sort_keys=True,
                    ),
                    "/architectures",
                )
            )
    return diagnostics


def semantic_diagnostics(
    artifact: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    digests: dict[str, str],
) -> list[dict[str, Any]]:
    stage = artifact["stage_id"]
    payload = artifact["payload"]
    diagnostics: list[dict[str, Any]] = []
    predecessor = predecessor_stage(stage)
    if predecessor and predecessor in artifacts:
        diagnostics.extend(
            validate_source_reference(
                artifact, artifacts[predecessor], digests[predecessor]
            )
        )
    if stage == "/architectures":
        families = {
            row.get("family_id")
            for row in payload.get("architecture_coverage_matrix", [])
        }
        missing = sorted({f"A{i:02d}" for i in range(1, 9)} - families)
        if missing:
            diagnostics.append(
                diagnostic(
                    "ASB-COVERAGE-MATRIX-INCOMPLETE",
                    "ASB-R03",
                    stage,
                    "$/payload/architecture_coverage_matrix",
                    "A01-A08",
                    ",".join(missing),
                    stage,
                )
            )
        upstream = artifacts.get("/decompose")
        ledger = {
            row.get("unknown_id"): row
            for row in payload.get("unknown_propagation_ledger", [])
        }
        if upstream:
            for unknown in upstream["payload"].get("unknowns", []):
                unknown_id = unknown.get("unknown_id")
                if unknown_id not in ledger:
                    diagnostics.append(
                        diagnostic(
                            "ASB-UPSTREAM-UNKNOWN-LOST",
                            "ASB-R04",
                            stage,
                            "$/payload/unknown_propagation_ledger",
                            str(unknown_id),
                            "missing",
                            "/decompose",
                        )
                    )
        for idx, row in enumerate(payload.get("unknown_propagation_ledger", [])):
            diagnostics.extend(validate_unknown_lifecycle(row, idx))
    elif stage == "/score-evidence":
        upstream = artifacts.get("/architectures")
        if upstream:
            expected_payload_ref = artifact_ref(
                upstream, digests["/architectures"]
            )
            payload_refs = payload.get("validated_upstream_artifact_refs", [])
            if len(payload_refs) != 1:
                diagnostics.append(
                    diagnostic(
                        "ASB-STAGE3-PAYLOAD-REFERENCE-COUNT",
                        "ASB-R05",
                        stage,
                        "$/payload/validated_upstream_artifact_refs",
                        "exactly one Stage 3 artifact_ref",
                        str(len(payload_refs)),
                        "/architectures",
                    )
                )
            elif payload_refs[0] != expected_payload_ref:
                diagnostics.append(
                    diagnostic(
                        "ASB-STAGE3-PAYLOAD-REFERENCE-MISMATCH",
                        "ASB-R05",
                        stage,
                        "$/payload/validated_upstream_artifact_refs/0",
                        json.dumps(expected_payload_ref, sort_keys=True),
                        json.dumps(payload_refs[0], sort_keys=True),
                        "/architectures",
                    )
                )
            valid_candidates = {
                row.get("candidate_id")
                for row in upstream["payload"].get("active_candidates", [])
            }
            active_unknowns = {
                row.get("unknown_id")
                for row in upstream["payload"].get(
                    "unknown_propagation_ledger", []
                )
                if row.get("state") in ACTIVE_UNKNOWN_STATES
                and row.get("handling") in ACTIVE_UNKNOWN_STATES
            }
            recorded_unknowns = {
                row.get("unknown_id")
                for row in payload.get("uncertainty_register", [])
                if isinstance(row, dict)
            }
            for idx, score in enumerate(payload.get("candidate_scores", [])):
                if score.get("candidate_id") not in valid_candidates:
                    diagnostics.append(
                        diagnostic(
                            "ASB-CANDIDATE-NOT-IN-STAGE3",
                            "ASB-R07",
                            stage,
                            f"$/payload/candidate_scores/{idx}/candidate_id",
                            "candidate from validated /architectures Artifact",
                            str(score.get("candidate_id")),
                            "/architectures",
                        )
                    )
                if score.get("scores_audited") is True:
                    diagnostics.append(
                        diagnostic(
                            "ASB-SCORE-AUDITED-EARLY",
                            "ASB-R08",
                            stage,
                            f"$/payload/candidate_scores/{idx}/scores_audited",
                            "false",
                            "true",
                            stage,
                        )
                    )
                critical_unknown = any(
                    criterion.get("contract_critical")
                    and criterion.get("value") == "?"
                    for criterion in score.get("criteria", [])
                )
                if critical_unknown and score.get("final_total") is not None:
                    diagnostics.append(
                        diagnostic(
                            "ASB-FINAL-TOTAL-WITH-UNKNOWN",
                            "ASB-R05",
                            stage,
                            f"$/payload/candidate_scores/{idx}/final_total",
                            "null",
                            str(score.get("final_total")),
                            stage,
                        )
                    )
            for unknown_id in sorted(active_unknowns - recorded_unknowns):
                diagnostics.append(
                    diagnostic(
                        "ASB-STAGE3-UNKNOWN-DISCARDED",
                        "ASB-R05",
                        stage,
                        "$/payload/uncertainty_register",
                        str(unknown_id),
                        "missing",
                        stage,
                    )
                )
    elif stage == "/score-audit":
        upstream = artifacts.get("/score-evidence")
        if upstream:
            expected = artifact_ref(upstream, digests["/score-evidence"])
            observed = payload.get("validated_stage_4_artifact_ref")
            if observed != expected:
                diagnostics.append(
                    diagnostic(
                        "ASB-STAGE4-REFERENCE-MISMATCH",
                        "ASB-R08",
                        stage,
                        "$/payload/validated_stage_4_artifact_ref",
                        json.dumps(expected, sort_keys=True),
                        json.dumps(observed, sort_keys=True),
                        "/score-evidence",
                    )
                )
    return diagnostics
