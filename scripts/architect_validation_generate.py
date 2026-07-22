"""Deterministic success and failure Bundle generation."""
from architect_validation_handoff import *  # noqa: F401,F403


def preflight_result(
    code: str,
    path: str,
    expected: str,
    observed: str,
    diagnostics: list[dict[str, Any]] | None = None,
    repair_target: str | None = None,
) -> dict[str, Any]:
    repair_target = repair_target or first_implemented_stage()
    items = diagnostics or [
        diagnostic(code, "ASB-R11", repair_target, path, expected, observed, repair_target)
    ]
    return {
        "bundle_integrity_status": "not_produced",
        "run_validation_status": "invalid",
        "authorization_valid": False,
        "output_published": False,
        "diagnostics": sort_diagnostics(items),
        "manifest": None,
    }


def _path_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _owned_output_directory(output: Path) -> bool:
    if output.is_symlink() or not output.is_dir():
        return False
    sentinel = output / OUTPUT_OWNERSHIP_SENTINEL
    try:
        manifest = load_json(sentinel)
    except Exception:
        return False
    return (
        manifest.get("bundle_schema") == BUNDLE_SCHEMA
        and manifest.get("validator_id") == VALIDATOR_ID
        and manifest.get("determinism_profile") == DETERMINISM_PROFILE
    )


def validate_output_target(
    sequence: Path, output: Path, root: Path = ROOT
) -> list[dict[str, Any]]:
    fallback_stage = first_implemented_stage(root)
    diagnostics: list[dict[str, Any]] = []
    try:
        sequence_resolved = sequence.resolve(strict=True)
    except Exception as exc:
        return [
            diagnostic(
                "ASB-UNSAFE-OUTPUT-PATH",
                "ASB-R11",
                fallback_stage,
                "$/sequence",
                "existing Sequence directory",
                type(exc).__name__,
                fallback_stage,
            )
        ]
    output_resolved = output.resolve(strict=False)
    root_resolved = root.resolve(strict=True)
    filesystem_root = Path(output_resolved.anchor)
    if output_resolved == filesystem_root:
        diagnostics.append(
            diagnostic(
                "ASB-UNSAFE-OUTPUT-PATH",
                "ASB-R11",
                fallback_stage,
                "$/output",
                "non-filesystem-root output",
                str(output_resolved),
                fallback_stage,
            )
        )
    if output_resolved == root_resolved:
        diagnostics.append(
            diagnostic(
                "ASB-UNSAFE-OUTPUT-PATH",
                "ASB-R11",
                fallback_stage,
                "$/output",
                "output distinct from repository root",
                str(output_resolved),
                fallback_stage,
            )
        )
    if _path_overlap(sequence_resolved, output_resolved):
        diagnostics.append(
            diagnostic(
                "ASB-UNSAFE-OUTPUT-PATH",
                "ASB-R11",
                fallback_stage,
                "$/output",
                "output disjoint from Sequence directory",
                str(output_resolved),
                fallback_stage,
            )
        )
    if output.exists() and not _owned_output_directory(output):
        diagnostics.append(
            diagnostic(
                "ASB-OUTPUT-NOT-VALIDATOR-OWNED",
                "ASB-R11",
                fallback_stage,
                "$/output",
                f"existing directory with exact {OUTPUT_OWNERSHIP_SENTINEL} ownership sentinel",
                str(output_resolved),
                fallback_stage,
            )
        )
    return sort_diagnostics(diagnostics)


def _render_transaction(
    result: dict[str, Any], sequence: Path, output: Path, root: Path
) -> dict[str, Any]:
    authority = pipeline_authority(root)
    for folder in ["artifacts", "receipts", "boundaries", "anchors"]:
        (output / folder).mkdir(parents=True, exist_ok=True)
    artifact_entries = []
    receipt_entries = []
    processed_by_stage: dict[str, dict[str, Any]] = {}
    receipt_digests: dict[str, str] = {}
    for item in result["processed"]:
        artifact = item["artifact"]
        stage = artifact["stage_id"]
        prefix = authority.prefix(stage)
        artifact_path = output / "artifacts" / f"{prefix}.json"
        artifact_path.write_bytes(item["path"].read_bytes())
        artifact_entries.append(
            file_entry(
                f"artifacts/{prefix}.json", artifact, item["digest"], "artifact"
            )
        )
        receipt_path = output / "receipts" / f"{prefix}.receipt.json"
        write_json(receipt_path, item["receipt"])
        receipt_digest = sha_file(receipt_path)
        receipt_digests[stage] = receipt_digest
        receipt_entries.append(
            file_entry(
                f"receipts/{prefix}.receipt.json",
                item["receipt"],
                receipt_digest,
                "receipt",
            )
        )
        processed_by_stage[stage] = item
    boundary_entries = []
    anchor_entries = []
    failure_event_path = None
    failure_event_digest = None
    if result["run_validation_status"] == "valid":
        for item in result["processed"]:
            artifact = item["artifact"]
            stage = artifact["stage_id"]
            prefix = authority.prefix(stage)
            boundary = success_boundary_for(
                artifact, item["digest"], item["receipt"], receipt_digests[stage]
            )
            boundary_path = output / "boundaries" / f"{prefix}.boundary.json"
            write_json(boundary_path, boundary)
            boundary_digest = sha_file(boundary_path)
            boundary_entries.append(
                file_entry(
                    f"boundaries/{prefix}.boundary.json",
                    boundary,
                    boundary_digest,
                    "boundary",
                )
            )
            predecessor = processed_by_stage.get(
                authority.predecessor(stage) or "", {}
            ).get("artifact")
            anchor = success_anchor_for(
                artifact, predecessor, boundary, boundary_digest
            )
            anchor_path = output / "anchors" / f"{prefix}.anchor.json"
            write_json(anchor_path, anchor)
            anchor_entries.append(
                file_entry(
                    f"anchors/{prefix}.anchor.json",
                    anchor,
                    sha_file(anchor_path),
                    "anchor",
                )
            )
        authorized_next_stage = authority.successor(
            result["processed"][-1]["artifact"]["stage_id"]
        )
        overall_status = "valid"
        repair_target = None
        authorization_valid = True
    else:
        failing = result["processed"][-1]
        failed_stage = result["failed_stage"]
        event = failure_event_for(result, receipt_digests[failed_stage])
        write_json(output / "failure-event.json", event)
        failure_event_path = "failure-event.json"
        failure_event_digest = sha_file(output / failure_event_path)
        boundary = repair_boundary_for(
            result, event, failure_event_digest, receipt_digests[failed_stage]
        )
        boundary_path = output / "boundaries" / "repair.boundary.json"
        write_json(boundary_path, boundary)
        boundary_digest = sha_file(boundary_path)
        boundary_entries.append(
            file_entry(
                "boundaries/repair.boundary.json",
                boundary,
                boundary_digest,
                "boundary",
            )
        )
        predecessor = processed_by_stage.get(
            authority.predecessor(failed_stage) or "", {}
        ).get("artifact")
        anchor = repair_anchor_for(
            result,
            predecessor,
            boundary,
            boundary_digest,
            event,
            failure_event_digest,
        )
        anchor_path = output / "anchors" / "repair.anchor.json"
        write_json(anchor_path, anchor)
        anchor_entries.append(
            file_entry(
                "anchors/repair.anchor.json",
                anchor,
                sha_file(anchor_path),
                "anchor",
            )
        )
        authorized_next_stage = None
        overall_status = "invalid"
        repair_target = result["repair_target_stage"]
        authorization_valid = False
    run_id = result["processed"][0]["artifact"]["run_id"]
    manifest = {
        "bundle_schema": BUNDLE_SCHEMA,
        "bundle_id": f"asb-bundle-{run_id}-{overall_status}",
        "run_id": run_id,
        "validator_id": VALIDATOR_ID,
        "validator_version": VALIDATOR_VERSION,
        "determinism_profile": DETERMINISM_PROFILE,
        "stage_sequence": [
            item["artifact"]["stage_id"] for item in result["processed"]
        ],
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
    write_json(output / OUTPUT_OWNERSHIP_SENTINEL, manifest)
    carrier_diagnostics = validate_generated_carriers(output, root)
    if carrier_diagnostics:
        raise ValueError(json.dumps(carrier_diagnostics, sort_keys=True))
    return {
        "bundle_integrity_status": "valid",
        "run_validation_status": result["run_validation_status"],
        "authorization_valid": authorization_valid,
        "output_published": True,
        "diagnostics": result["diagnostics"],
        "manifest": manifest,
    }


def _publish_atomically(temp_output: Path, output: Path) -> None:
    backup: Path | None = None
    published = False
    try:
        if output.exists():
            backup = Path(
                tempfile.mkdtemp(
                    prefix=f".{output.name}.asb-backup-", dir=str(output.parent)
                )
            )
            backup.rmdir()
            output.rename(backup)
        temp_output.rename(output)
        published = True
    except Exception:
        if not published and backup is not None and backup.exists() and not output.exists():
            backup.rename(output)
        raise
    finally:
        if published and backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def generate_transaction(
    sequence: Path, output: Path, root: Path = ROOT
) -> dict[str, Any]:
    path_diagnostics = validate_output_target(sequence, output, root)
    if path_diagnostics:
        return preflight_result(
            path_diagnostics[0]["code"],
            path_diagnostics[0]["path"],
            path_diagnostics[0]["expected"],
            path_diagnostics[0]["observed"],
            diagnostics=path_diagnostics,
            repair_target=path_diagnostics[0]["repair_target_stage"],
        )
    result = validate_sequence(sequence, root)
    if result.get("structural_failure"):
        return preflight_result(
            result["diagnostics"][0]["code"],
            result["diagnostics"][0]["path"],
            result["diagnostics"][0]["expected"],
            result["diagnostics"][0]["observed"],
            diagnostics=result["diagnostics"],
            repair_target=result["repair_target_stage"],
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.asb-tmp-", dir=str(output.parent))
    )
    try:
        rendered = _render_transaction(result, sequence, temp_output, root)
        _publish_atomically(temp_output, output)
        return rendered
    except Exception:
        if temp_output.exists():
            shutil.rmtree(temp_output)
        raise


def safe_manifest_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and not path.is_absolute()
        and ".." not in path.parts
        and str(path) == value
    )
