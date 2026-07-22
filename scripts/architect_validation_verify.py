"""Independent exact-byte Bundle regeneration and verification."""
from architect_validation_generate import *  # noqa: F401,F403

def listed_paths(manifest: dict[str, Any]) -> set[str]:
    result = {"manifest.json"}
    for collection in ["artifacts", "receipts", "boundaries", "anchors"]:
        for item in manifest.get(collection, []):
            result.add(item["path"])
    if manifest.get("failure_event_path"):
        result.add(manifest["failure_event_path"])
    return result

def invalid_bundle_result(
    code: str,
    path: str,
    expected: str,
    observed: str,
    repair_target: str | None = None,
) -> dict[str, Any]:
    repair_target = repair_target or first_implemented_stage()
    return {
        "bundle_integrity_status": "invalid",
        "run_validation_status": "unknown",
        "authorization_valid": False,
        "diagnostics": [
            diagnostic(
                code,
                "ASB-R09",
                "bundle",
                path,
                expected,
                observed,
                repair_target,
            )
        ],
    }


def bundle_manifest_semantic_diagnostics(
    manifest: dict[str, Any], authority: PipelineAuthority
) -> list[dict[str, Any]]:
    fallback = authority.implemented_stage_order[0]
    sequence = manifest.get("stage_sequence", [])
    expected = list(authority.implemented_stage_order[: len(sequence)])
    if sequence != expected:
        return [
            diagnostic(
                "ASB-BUNDLE-STAGE-SEQUENCE-NOT-EXECUTABLE-PREFIX",
                "ASB-R12",
                "bundle",
                "$/stage_sequence",
                json.dumps(expected),
                json.dumps(sequence),
                fallback,
            )
        ]
    if not sequence:
        return [
            diagnostic(
                "ASB-BUNDLE-STAGE-SEQUENCE-EMPTY",
                "ASB-R12",
                "bundle",
                "$/stage_sequence",
                "non-empty executable Stage prefix",
                "empty",
                fallback,
            )
        ]
    for stage in sequence:
        if not authority.is_implemented(stage):
            return [
                diagnostic(
                    "ASB-BUNDLE-STAGE-NOT-IMPLEMENTED",
                    "ASB-R12",
                    stage,
                    "$/stage_sequence",
                    "full_transaction_implemented Validation Profile",
                    authority.profiles[stage]["validation"]["status"],
                    stage,
                )
            ]
    if len(manifest.get("artifacts", [])) != len(sequence) or len(
        manifest.get("receipts", [])
    ) != len(sequence):
        return [
            diagnostic(
                "ASB-BUNDLE-STAGE-CARRIER-COUNT-MISMATCH",
                "ASB-R12",
                "bundle",
                "$",
                str(len(sequence)),
                f"artifacts={len(manifest.get('artifacts', []))};receipts={len(manifest.get('receipts', []))}",
                fallback,
            )
        ]
    if manifest.get("overall_status") == "valid":
        source = sequence[-1]
        successor = authority.successor(source)
        if successor is None or manifest.get("authorized_next_stage") != successor:
            return [
                diagnostic(
                    "ASB-BUNDLE-AUTHORIZED-EDGE-INVALID",
                    "ASB-R12",
                    source,
                    "$/authorized_next_stage",
                    str(successor),
                    str(manifest.get("authorized_next_stage")),
                    source,
                )
            ]
        if not authority.profiles[source]["validation"]["authorization_capable"]:
            return [
                diagnostic(
                    "ASB-BUNDLE-SOURCE-NOT-AUTHORIZATION-CAPABLE",
                    "ASB-R12",
                    source,
                    "$/stage_sequence",
                    "authorization_capable Validation Profile",
                    authority.profiles[source]["validation"]["status"],
                    source,
                )
            ]
        if len(manifest.get("boundaries", [])) != len(sequence) or len(
            manifest.get("anchors", [])
        ) != len(sequence):
            return [
                diagnostic(
                    "ASB-BUNDLE-SUCCESS-CARRIER-COUNT-MISMATCH",
                    "ASB-R12",
                    source,
                    "$",
                    str(len(sequence)),
                    f"boundaries={len(manifest.get('boundaries', []))};anchors={len(manifest.get('anchors', []))}",
                    source,
                )
            ]
    expected_schemas = {
        "artifacts": ARTIFACT_SCHEMA,
        "receipts": RECEIPT_SCHEMA,
        "boundaries": BOUNDARY_SCHEMA,
        "anchors": ANCHOR_SCHEMA,
    }
    for collection, expected_schema in expected_schemas.items():
        for index, entry in enumerate(manifest.get(collection, [])):
            if entry.get("schema") != expected_schema:
                return [
                    diagnostic(
                        "ASB-BUNDLE-CARRIER-SCHEMA-INACTIVE",
                        "ASB-R12",
                        "bundle",
                        f"$/{collection}/{index}/schema",
                        expected_schema,
                        str(entry.get("schema")),
                        fallback,
                    )
                ]
    return []

def validate_bundle(bundle: Path, root: Path = ROOT) -> dict[str, Any]:
    authority = pipeline_authority(root)
    fallback_stage = first_implemented_stage(root)
    try:
        manifest = load_json(bundle / "manifest.json")
    except Exception as exc:
        return invalid_bundle_result("ASB-BUNDLE-MANIFEST-MISSING", "$/manifest.json", "valid manifest", type(exc).__name__)
    validators = schema_validators(root)
    schema_errors = schema_diagnostics(
        validators["bundle"], manifest, "bundle", "$", fallback_stage
    )
    if schema_errors:
        return {
            "bundle_integrity_status": "invalid",
            "run_validation_status": "unknown",
            "authorization_valid": False,
            "diagnostics": schema_errors,
        }
    for collection in ["artifacts", "receipts", "boundaries", "anchors"]:
        seen = set()
        for entry in manifest[collection]:
            path = entry["path"]
            if not safe_manifest_path(path):
                return invalid_bundle_result("ASB-BUNDLE-PATH-TRAVERSAL", f"$/{collection}", "safe relative path", path)
            if path in seen:
                return invalid_bundle_result("ASB-BUNDLE-DUPLICATE-PATH", f"$/{collection}", "unique path", path)
            seen.add(path)
    semantic_errors = bundle_manifest_semantic_diagnostics(manifest, authority)
    if semantic_errors:
        return {
            "bundle_integrity_status": "invalid",
            "run_validation_status": "unknown",
            "authorization_valid": False,
            "diagnostics": semantic_errors,
        }
    expected_paths = listed_paths(manifest)
    actual_paths = {str(path.relative_to(bundle).as_posix()) for path in bundle.rglob("*") if path.is_file()}
    if expected_paths != actual_paths:
        return invalid_bundle_result(
            "ASB-BUNDLE-FILE-SET-MISMATCH",
            "$",
            ",".join(sorted(expected_paths)),
            ",".join(sorted(actual_paths)),
        )
    for collection in ["artifacts", "receipts", "boundaries", "anchors"]:
        for entry in manifest[collection]:
            path = bundle / entry["path"]
            observed_digest = sha_file(path)
            if observed_digest != entry["sha256"]:
                return invalid_bundle_result(
                    "ASB-BUNDLE-CARRIER-HASH-MISMATCH",
                    f"$/{entry['path']}",
                    entry["sha256"],
                    observed_digest,
                )
    if manifest.get("failure_event_path"):
        event_digest = sha_file(bundle / manifest["failure_event_path"])
        if event_digest != manifest["failure_event_sha256"]:
            return invalid_bundle_result(
                "ASB-FAILURE-EVENT-HASH-MISMATCH",
                "$/failure_event_sha256",
                manifest["failure_event_sha256"],
                event_digest,
            )
    if manifest_digest(manifest) != manifest["bundle_content_digest"]:
        return invalid_bundle_result(
            "ASB-BUNDLE-CONTENT-DIGEST-MISMATCH",
            "$/bundle_content_digest",
            manifest_digest(manifest),
            manifest["bundle_content_digest"],
        )
    # Validate each carrier before regeneration for stable field-specific diagnostics.
    kind_map = {
        "artifacts": "artifact",
        "receipts": "receipt",
        "boundaries": "boundary",
        "anchors": "anchor",
    }
    failing_artifact_path = None
    if manifest.get("overall_status") == "invalid" and manifest.get("failure_event_path"):
        event = load_json(bundle / manifest["failure_event_path"])
        failing_prefix = authority.prefix(event["failing_artifact"]["stage_id"])
        failing_artifact_path = f"artifacts/{failing_prefix}.json"
    for collection, kind in kind_map.items():
        for entry in manifest[collection]:
            value = load_json(bundle / entry["path"])
            # A truthful failure Bundle must preserve the exact invalid Artifact.
            # Its invalidity is reproduced by the transaction; it is not a Bundle-integrity defect.
            if collection == "artifacts" and entry["path"] == failing_artifact_path:
                continue
            stage = value.get("stage_id") or value.get("source_stage") or "bundle"
            repair = value.get("repair_target_stage") or (
                stage if stage in authority.stage_records else authority.implemented_stage_order[0]
            )
            errors = schema_diagnostics(validators[kind], value, stage, f"$/{entry['path']}", repair)
            if errors:
                return {
                    "bundle_integrity_status": "invalid",
                    "run_validation_status": "unknown",
                    "authorization_valid": False,
                    "diagnostics": errors,
                }
            if collection == "anchors":
                errors = anchor_semantic_diagnostics(
                    value, authority, f"$/{entry['path']}"
                )
                if errors:
                    return {
                        "bundle_integrity_status": "invalid",
                        "run_validation_status": "unknown",
                        "authorization_valid": False,
                        "diagnostics": errors,
                    }
    if manifest.get("failure_event_path"):
        value = load_json(bundle / manifest["failure_event_path"])
        errors = schema_diagnostics(
            validators["failure_event"],
            value,
            value.get("failed_stage", "bundle"),
            "$/failure-event.json",
            value.get("repair_target_stage", fallback_stage),
        )
        if errors:
            return {
                "bundle_integrity_status": "invalid",
                "run_validation_status": "unknown",
                "authorization_valid": False,
                "diagnostics": errors,
            }
    with tempfile.TemporaryDirectory(prefix="asb-verify-") as temp:
        temp_path = Path(temp)
        sequence = temp_path / "sequence"
        regenerated = temp_path / "regenerated"
        sequence.mkdir()
        for entry in manifest["artifacts"]:
            source = bundle / entry["path"]
            target = sequence / Path(entry["path"]).name
            target.write_bytes(source.read_bytes())
        try:
            regenerate_result = generate_transaction(sequence, regenerated, root)
        except Exception as exc:
            return invalid_bundle_result("ASB-BUNDLE-REGENERATION-FAILED", "$", "deterministic regeneration", type(exc).__name__)
        regenerated_paths = {str(path.relative_to(regenerated).as_posix()) for path in regenerated.rglob("*") if path.is_file()}
        if regenerated_paths != actual_paths:
            return invalid_bundle_result(
                "ASB-BUNDLE-REGENERATED-FILE-SET-MISMATCH",
                "$",
                ",".join(sorted(regenerated_paths)),
                ",".join(sorted(actual_paths)),
            )
        for rel in sorted(actual_paths):
            observed = (bundle / rel).read_bytes()
            expected = (regenerated / rel).read_bytes()
            if observed != expected:
                return invalid_bundle_result(
                    "ASB-BUNDLE-CARRIER-BYTE-MISMATCH",
                    f"$/{rel}",
                    sha_bytes(expected),
                    sha_bytes(observed),
                )
    return {
        "bundle_integrity_status": "valid",
        "run_validation_status": regenerate_result["run_validation_status"],
        "authorization_valid": regenerate_result["authorization_valid"],
        "diagnostics": [],
        "manifest": manifest,
        "verification_status": "valid_bundle_verified" if regenerate_result["run_validation_status"] == "valid" else "invalid_bundle_verified",
    }
