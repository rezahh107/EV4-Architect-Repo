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
    matches = [ref for ref in artifact.get("source_artifacts", []) if ref.get("source_stage") == predecessor_stage]
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

def semantic_diagnostics(
    artifact: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    digests: dict[str, str],
) -> list[dict[str, Any]]:
    stage = artifact["stage_id"]
    payload = artifact["payload"]
    diagnostics: list[dict[str, Any]] = []
    predecessor_stage = PREDECESSOR.get(stage)
    if predecessor_stage and predecessor_stage in artifacts:
        diagnostics.extend(
            validate_source_reference(artifact, artifacts[predecessor_stage], digests[predecessor_stage])
        )
    if stage == "/architectures":
        families = {row.get("family_id") for row in payload.get("architecture_coverage_matrix", [])}
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
        ledger = {row.get("unknown_id"): row for row in payload.get("unknown_propagation_ledger", [])}
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
            if row.get("state") not in ACTIVE_UNKNOWN_STATES or row.get("handling") not in ACTIVE_UNKNOWN_STATES:
                diagnostics.append(
                    diagnostic(
                        "ASB-UNKNOWN-RESOLUTION-UNSUPPORTED",
                        "ASB-R04",
                        stage,
                        f"$/payload/unknown_propagation_ledger/{idx}",
                        "active evidence state",
                        f"state={row.get('state')};handling={row.get('handling')}",
                        stage,
                    )
                )
    elif stage == "/score-evidence":
        upstream = artifacts.get("/architectures")
        if upstream:
            valid_candidates = {row.get("candidate_id") for row in upstream["payload"].get("active_candidates", [])}
            active_unknowns = {
                row.get("unknown_id")
                for row in upstream["payload"].get("unknown_propagation_ledger", [])
                if row.get("state") in ACTIVE_UNKNOWN_STATES or row.get("handling") in ACTIVE_UNKNOWN_STATES
            }
            recorded_unknowns = {
                row.get("unknown_id") for row in payload.get("uncertainty_register", []) if isinstance(row, dict)
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
                    criterion.get("contract_critical") and criterion.get("value") == "?"
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
