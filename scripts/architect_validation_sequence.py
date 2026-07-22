"""Artifact sequence discovery and validation."""
from architect_validation_semantics import *  # noqa: F401,F403


def discover_sequence(
    sequence_path: Path, authority: PipelineAuthority | None = None
) -> tuple[list[Path], list[dict[str, Any]]]:
    authority = authority or PIPELINE_AUTHORITY
    executable_order = authority.implemented_stage_order
    fallback_stage = executable_order[0]
    diagnostics: list[dict[str, Any]] = []
    by_stage: dict[str, list[Path]] = {}
    for path in sorted(sequence_path.glob("*.json")):
        try:
            value = load_json(path)
        except Exception as exc:
            diagnostics.append(
                diagnostic(
                    "ASB-SCHEMA-VALIDATION-FAILED",
                    "ASB-R01",
                    fallback_stage,
                    f"$/{path.name}",
                    "valid JSON object",
                    type(exc).__name__,
                    fallback_stage,
                )
            )
            continue
        stage = value.get("stage_id") if isinstance(value, dict) else None
        if stage not in authority.stage_records:
            diagnostics.append(
                diagnostic(
                    "ASB-STAGE-FILE-MISMATCH",
                    "ASB-R01",
                    stage or fallback_stage,
                    f"$/{path.name}",
                    "recognized stage_id",
                    str(stage),
                    fallback_stage,
                )
            )
            continue
        if not authority.is_implemented(stage):
            diagnostics.append(
                diagnostic(
                    "ASB-STAGE-VALIDATION-NOT-IMPLEMENTED",
                    "ASB-R12",
                    stage,
                    f"$/{path.name}",
                    "full_transaction_implemented Validation Profile",
                    authority.profiles[stage]["validation"]["status"],
                    stage,
                )
            )
            continue
        expected_name = f"{authority.prefix(stage)}.json"
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
    present = [stage for stage in executable_order if stage in by_stage]
    if present:
        highest = max(authority.implemented_index(stage) for stage in present)
        for missing in executable_order[: highest + 1]:
            if missing not in by_stage:
                detected = executable_order[min(highest, len(executable_order) - 1)]
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
    elif not diagnostics:
        diagnostics.append(
            diagnostic(
                "ASB-STAGE-SEQUENCE-GAP",
                "ASB-R01",
                fallback_stage,
                "$",
                fallback_stage,
                "empty sequence",
                fallback_stage,
            )
        )
    return [by_stage[stage][0] for stage in executable_order if stage in by_stage], sort_diagnostics(diagnostics)


def validate_sequence(sequence: Path, root: Path = ROOT) -> dict[str, Any]:
    authority = pipeline_authority(root)
    validators = schema_validators(root)
    paths, discovery_diagnostics = discover_sequence(sequence, authority)
    if discovery_diagnostics:
        return {
            "run_validation_status": "invalid",
            "authorization_valid": False,
            "diagnostics": discovery_diagnostics,
            "processed": [],
            "failed_stage": discovery_diagnostics[0]["stage_id"],
            "repair_target_stage": select_repair_target(
                discovery_diagnostics, authority.implemented_stage_order[0]
            ),
            "structural_failure": True,
        }
    artifacts: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}
    processed: list[dict[str, Any]] = []
    run_id: str | None = None
    for path in paths:
        raw = path.read_bytes()
        digest = sha_bytes(raw)
        artifact = json.loads(raw.decode("utf-8"))
        stage = artifact.get("stage_id", authority.implemented_stage_order[0])
        diagnostics: list[dict[str, Any]] = []
        expected_version = authority.stage_version(stage)
        if artifact.get("stage_version") != expected_version:
            diagnostics.append(
                diagnostic(
                    "ASB-STAGE-VERSION-MISMATCH",
                    "ASB-R01",
                    stage,
                    "$/stage_version",
                    str(expected_version),
                    str(artifact.get("stage_version")),
                    stage,
                )
            )
        schema_errors = schema_diagnostics(validators["artifact"], artifact, stage, "$", stage)
        if stage == "/score-evidence":
            for item in schema_errors:
                if item["path"].startswith("$/payload/validated_upstream_artifact_refs"):
                    item["repair_target_stage"] = "/architectures"
        diagnostics.extend(schema_errors)
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
            diagnostics.extend(
                semantic_diagnostics(artifact, artifacts, digests, authority)
            )
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
                "structural_failure": False,
            }
        artifacts[stage] = artifact
        digests[stage] = digest
    return {
        "run_validation_status": "valid",
        "authorization_valid": True,
        "diagnostics": [],
        "processed": processed,
        "failed_stage": None,
        "repair_target_stage": None,
        "structural_failure": False,
    }
