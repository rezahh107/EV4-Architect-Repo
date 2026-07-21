"""Artifact sequence discovery and validation."""
from architect_validation_semantics import *  # noqa: F401,F403

def discover_sequence(sequence_path: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    diagnostics: list[dict[str, Any]] = []
    by_stage: dict[str, list[Path]] = {}
    for path in sorted(sequence_path.glob("*.json")):
        try:
            value = load_json(path)
        except Exception as exc:  # deterministic type-only diagnostic
            diagnostics.append(
                diagnostic(
                    "ASB-SCHEMA-VALIDATION-FAILED",
                    "ASB-R01",
                    "/decompose",
                    f"$/{path.name}",
                    "valid JSON object",
                    type(exc).__name__,
                    "/decompose",
                )
            )
            continue
        stage = value.get("stage_id") if isinstance(value, dict) else None
        if stage not in ORDER:
            diagnostics.append(
                diagnostic(
                    "ASB-STAGE-FILE-MISMATCH",
                    "ASB-R01",
                    stage or "/decompose",
                    f"$/{path.name}",
                    "recognized stage_id",
                    str(stage),
                    stage if stage in ORDER else "/decompose",
                )
            )
            continue
        expected_name = f"{PREFIX[stage]}.json"
        if path.name != expected_name:
            diagnostics.append(
                diagnostic(
                    "ASB-STAGE-FILE-MISMATCH",
                    "ASB-R01",
                    stage,
                    f"$/{path.name}",
                    expected_name,
                    path.name,
                    stage,
                )
            )
        by_stage.setdefault(stage, []).append(path)
    for stage, paths in by_stage.items():
        if len(paths) > 1:
            diagnostics.append(
                diagnostic(
                    "ASB-DUPLICATE-STAGE",
                    "ASB-R01",
                    stage,
                    "$",
                    "one Artifact per Stage",
                    ",".join(path.name for path in paths),
                    stage,
                )
            )
    present = [stage for stage in ORDER if stage in by_stage]
    if present:
        highest = max(stage_index(stage) for stage in present)
        for missing in ORDER[: highest + 1]:
            if missing not in by_stage:
                detected = ORDER[min(highest, len(ORDER) - 1)]
                diagnostics.append(
                    diagnostic(
                        "ASB-STAGE-SEQUENCE-GAP",
                        "ASB-R01",
                        detected,
                        "$",
                        missing,
                        "missing",
                        missing,
                    )
                )
    return [by_stage[stage][0] for stage in ORDER if stage in by_stage], sort_diagnostics(diagnostics)

def validate_sequence(sequence: Path, root: Path = ROOT) -> dict[str, Any]:
    validators = schema_validators(root)
    paths, discovery_diagnostics = discover_sequence(sequence)
    if discovery_diagnostics:
        return {
            "run_validation_status": "invalid",
            "authorization_valid": False,
            "diagnostics": discovery_diagnostics,
            "processed": [],
            "failed_stage": discovery_diagnostics[0]["stage_id"],
            "repair_target_stage": select_repair_target(discovery_diagnostics, "/decompose"),
        }
    artifacts: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}
    processed: list[dict[str, Any]] = []
    run_id: str | None = None
    for path in paths:
        raw = path.read_bytes()
        digest = sha_bytes(raw)
        artifact = json.loads(raw.decode("utf-8"))
        stage = artifact.get("stage_id", "/decompose")
        diagnostics = schema_diagnostics(validators["artifact"], artifact, stage, "$", stage)
        if run_id is None:
            run_id = artifact.get("run_id")
        elif artifact.get("run_id") != run_id:
            diagnostics.append(
                diagnostic(
                    "ASB-RUN-ID-DISCONTINUITY",
                    "ASB-R06",
                    stage,
                    "$/run_id",
                    str(run_id),
                    str(artifact.get("run_id")),
                    stage,
                )
            )
        if not diagnostics:
            diagnostics.extend(semantic_diagnostics(artifact, artifacts, digests))
        receipt = receipt_for(artifact, digest, diagnostics)
        processed.append({"path": path, "artifact": artifact, "digest": digest, "receipt": receipt})
        if diagnostics:
            return {
                "run_validation_status": "invalid",
                "authorization_valid": False,
                "diagnostics": sort_diagnostics(diagnostics),
                "processed": processed,
                "failed_stage": stage,
                "repair_target_stage": select_repair_target(diagnostics, stage),
            }
        artifacts[stage] = artifact
        digests[stage] = digest
    if not processed:
        diagnostics = [
            diagnostic(
                "ASB-STAGE-SEQUENCE-GAP",
                "ASB-R01",
                "/decompose",
                "$",
                "/decompose",
                "empty sequence",
                "/decompose",
            )
        ]
        return {
            "run_validation_status": "insufficient_evidence",
            "authorization_valid": False,
            "diagnostics": diagnostics,
            "processed": [],
            "failed_stage": "/decompose",
            "repair_target_stage": "/decompose",
        }
    return {
        "run_validation_status": "valid",
        "authorization_valid": True,
        "diagnostics": [],
        "processed": processed,
        "failed_stage": None,
        "repair_target_stage": None,
    }
