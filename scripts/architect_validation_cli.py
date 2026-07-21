"""Fixture, diagnostic, and command-line entrypoints."""
from architect_validation_verify import *  # noqa: F401,F403


def validate_fixture_suite(root: Path = ROOT) -> dict[str, Any]:
    cases = []
    fixture_root = root / "fixtures/architect-pipeline-stage-boundary"
    valid_sequence = fixture_root / "valid/complete-sequence"
    resolved_sequence = fixture_root / "valid/resolved-inactive-unknowns-sequence"
    failure_sequence = fixture_root / "invalid/cross-stage-architectures-to-decompose"
    with tempfile.TemporaryDirectory(prefix="asb-fixtures-") as temp:
        temp_path = Path(temp)
        for case_id, sequence, expected_run, expected_repair in [
            ("SUCCESS", valid_sequence, "valid", None),
            ("RESOLVED_INACTIVE", resolved_sequence, "valid", None),
            ("F03", failure_sequence, "invalid", "/decompose"),
        ]:
            bundle = temp_path / case_id
            generated = generate_transaction(sequence, bundle, root)
            verified = validate_bundle(bundle, root)
            manifest = generated.get("manifest") or {}
            passed = (
                generated["run_validation_status"] == expected_run
                and generated["output_published"] is True
                and verified["bundle_integrity_status"] == "valid"
                and verified["run_validation_status"] == expected_run
                and manifest.get("repair_target_stage") == expected_repair
            )
            cases.append(
                {"case_id": case_id, "passed": passed, "verification": verified}
            )
        for case_id, relative, expected_repair in [
            ("T19", "invalid/T19-missing-stage2", "/decompose"),
            ("T20", "invalid/T20-missing-stage3", "/architectures"),
            ("T21", "invalid/T21-missing-stage4", "/score-evidence"),
            ("T22", "invalid/T22-duplicate-stage2", "/decompose"),
            ("T23", "invalid/T23-stage-file-mismatch", "/architectures"),
        ]:
            sequence = fixture_root / relative
            output = temp_path / f"{case_id}-bundle"
            first = generate_transaction(sequence, output, root)
            second = generate_transaction(sequence, output, root)
            passed = (
                first == second
                and first["bundle_integrity_status"] == "not_produced"
                and first["run_validation_status"] == "invalid"
                and first["authorization_valid"] is False
                and first["output_published"] is False
                and not output.exists()
                and first["diagnostics"][0]["repair_target_stage"] == expected_repair
            )
            cases.append({"case_id": case_id, "passed": passed, "verification": first})
    return {
        "status": "valid" if all(case["passed"] for case in cases) else "invalid",
        "cases": cases,
        "diagnostic_only": True,
        "authorization_valid": False,
        "generated_authorization_files": [],
    }


def diagnostic_artifact(path: Path, root: Path = ROOT) -> dict[str, Any]:
    validators = schema_validators(root)
    try:
        artifact = load_json(path)
        stage = artifact.get("stage_id", "/decompose")
        errors = schema_diagnostics(validators["artifact"], artifact, stage, "$", stage)
        expected_version = STAGE_VERSIONS.get(stage)
        if expected_version and artifact.get("stage_version") != expected_version:
            errors.insert(
                0,
                diagnostic(
                    "ASB-STAGE-VERSION-MISMATCH",
                    "ASB-R01",
                    stage,
                    "$/stage_version",
                    expected_version,
                    str(artifact.get("stage_version")),
                    stage,
                ),
            )
    except Exception as exc:
        errors = [
            diagnostic(
                "ASB-SCHEMA-VALIDATION-FAILED",
                "ASB-R01",
                "/decompose",
                "$",
                "valid Artifact",
                type(exc).__name__,
                "/decompose",
            )
        ]
    stage = artifact.get("stage_id", "/decompose") if "artifact" in locals() else "/decompose"
    return {
        "status": "invalid",
        "diagnostic_only": True,
        "authorization_valid": False,
        "generated_authorization_files": [],
        "diagnostics": errors
        + [
            diagnostic(
                "ASB-STANDALONE-ARTIFACT-NOT-AUTHORITY",
                "ASB-R10",
                stage,
                "$",
                "validate-run transaction",
                "standalone diagnostic",
                stage,
            )
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    run_parser = sub.add_parser("validate-run")
    run_parser.add_argument("--sequence", required=True)
    run_parser.add_argument("--output", required=True)
    run_parser.add_argument("--format", choices=["text", "json"], default="text")
    bundle_parser = sub.add_parser("validate-bundle")
    bundle_parser.add_argument("--bundle", required=True)
    bundle_parser.add_argument("--format", choices=["text", "json"], default="text")
    diagnostic_parser = sub.add_parser("diagnose-artifact")
    diagnostic_parser.add_argument("--artifact", required=True)
    diagnostic_parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    if args.command == "validate-run":
        result = generate_transaction(Path(args.sequence), Path(args.output), ROOT)
        print(
            json.dumps(result, indent=2, sort_keys=True)
            if args.format == "json"
            else result["run_validation_status"]
        )
        return 0 if result["run_validation_status"] == "valid" else 1
    if args.command == "validate-bundle":
        result = validate_bundle(Path(args.bundle), ROOT)
        print(
            json.dumps(result, indent=2, sort_keys=True)
            if args.format == "json"
            else result["bundle_integrity_status"]
        )
        return 0 if result["bundle_integrity_status"] == "valid" else 1
    if args.command == "diagnose-artifact":
        result = diagnostic_artifact(Path(args.artifact), ROOT)
        print(
            json.dumps(result, indent=2, sort_keys=True)
            if args.format == "json"
            else result["status"]
        )
        return 1
    if args.fixtures:
        result = validate_fixture_suite(ROOT)
        print(
            json.dumps(result, indent=2, sort_keys=True)
            if args.format == "json"
            else result["status"]
        )
        return 0 if result["status"] == "valid" else 1
    parser.error("choose validate-run, validate-bundle, diagnose-artifact, or --fixtures")
    return 2
