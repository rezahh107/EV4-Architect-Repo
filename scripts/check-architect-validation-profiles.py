#!/usr/bin/env python3
"""Validate the canonical Architect Manifest/Validation Registry relationship."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from architect_validation_profiles import (  # noqa: E402
    MANIFEST_PATH,
    REGISTRY_PATH,
    exposed_profile,
    load_pipeline_authority,
)


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    registry = json.loads((root / REGISTRY_PATH).read_text(encoding="utf-8"))
    for value, schema_path, label in [
        (manifest, root / "schemas/ev4-architect-pipeline-manifest.v1.schema.json", "manifest"),
        (registry, root / "schemas/architect-stage-validation-profiles.v1.schema.json", "registry"),
    ]:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        for error in sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.absolute_path)):
            path = "/".join(str(part) for part in error.absolute_path)
            errors.append(f"{label}:{path}:{error.message}")
    if errors:
        return errors
    try:
        authority = load_pipeline_authority(root)
    except (KeyError, TypeError, ValueError) as exc:
        return [f"authority:{exc}"]

    if "intermediate_stage_artifact_boundary" in manifest:
        errors.append("manifest:legacy validation capability block remains")
    for stage_id in authority.stage_order:
        profile = exposed_profile(authority, stage_id)
        for source in profile["grounding"]["authoritative_sources"]:
            if not (root / source).is_file():
                errors.append(f"{stage_id}:authoritative source missing:{source}")
        schema_path = profile["artifact"]["schema_path"]
        if profile["validation"]["status"] == "full_transaction_implemented":
            if not (root / schema_path).is_file():
                errors.append(f"{stage_id}:implemented Artifact Schema missing:{schema_path}")
            if profile["grounding"]["unresolved_semantic_decisions"]:
                errors.append(f"{stage_id}:implemented profile has unresolved semantic decisions")

    from architect_validation_generate import generate_transaction  # noqa: PLC0415
    from architect_validation_semantics import SEMANTIC_HANDLERS, receipt_for  # noqa: PLC0415
    from architect_validation_verify import validate_bundle  # noqa: PLC0415

    declared_handlers = {
        profile["validation"]["semantic_handler"]
        for profile in authority.profiles.values()
        if profile["validation"]["status"] == "full_transaction_implemented"
    }
    if declared_handlers != set(SEMANTIC_HANDLERS):
        errors.append(
            "registry:implemented semantic handlers do not exactly match the runtime handler registry"
        )
    declared_receipt_generators = {
        profile["receipt"]["generator"]
        for profile in authority.profiles.values()
        if profile["receipt"]["supported"]
    }
    if declared_receipt_generators != {receipt_for.__name__}:
        errors.append("registry:declared Receipt generators do not match runtime")
    if generate_transaction.__name__ != "generate_transaction" or validate_bundle.__name__ != "validate_bundle":
        errors.append("registry:Bundle generation or independent regeneration entrypoint missing")

    implemented = set(authority.implemented_stage_order)

    artifact_schema = json.loads(
        (root / "schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    schema_stage_versions: dict[str, str] = {}
    for branch in artifact_schema.get("allOf", []):
        try:
            stage_id = branch["if"]["properties"]["stage_id"]["const"]
            version = branch["then"]["properties"]["stage_version"]["const"]
        except (KeyError, TypeError):
            continue
        if stage_id in schema_stage_versions:
            errors.append(f"artifact-schema:duplicate Stage-version branch:{stage_id}")
        schema_stage_versions[stage_id] = version
    expected_stage_versions = {
        stage_id: authority.stage_version(stage_id)
        for stage_id in authority.implemented_stage_order
    }
    if schema_stage_versions != expected_stage_versions:
        errors.append(
            "artifact-schema:Stage-version branches differ from Manifest executable versions"
        )

    def stage_enums(value: object) -> list[set[str]]:
        found: list[set[str]] = []
        if isinstance(value, dict):
            enum = value.get("enum")
            if isinstance(enum, list):
                stages = {item for item in enum if isinstance(item, str) and item.startswith("/")}
                if stages:
                    found.append(stages)
            for child in value.values():
                found.extend(stage_enums(child))
        elif isinstance(value, list):
            for child in value:
                found.extend(stage_enums(child))
        return found

    coverage_schema_paths = [
        "schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json",
        "schemas/ev4-architect-stage-validation-receipt.v1.schema.json",
        "schemas/ev4-architect-validation-failure-event.v1.schema.json",
        "schemas/ev4-stage-boundary-record.v1.schema.json",
        "schemas/ev4-stage-anchor.v1.4.schema.json",
        "schemas/ev4-architect-validation-bundle.v1.2.schema.json",
    ]
    for relative in coverage_schema_paths:
        value = json.loads((root / relative).read_text(encoding="utf-8"))
        for enum in stage_enums(value):
            if enum != implemented:
                errors.append(
                    f"{relative}:executable Stage enum differs from Registry implemented set"
                )

    authority_consumers = sorted((root / "scripts").glob("architect_validation_*.py"))
    authority_consumers.append(root / "scripts/check-architect-bootstrap.py")
    forbidden_assignments = [
        r"\bSTAGE_ORDER\s*=",
        r"\bNEXT_STAGE\s*=",
        r"\bPREDECESSOR\s*=",
        r"\bSTAGE_VERSIONS\s*=",
        r"\bEXPECTED_INITIAL_SEQUENCE\s*=",
        r"\bEXPECTED_FINAL_STAGE\s*=",
    ]
    for source_path in authority_consumers:
        source = source_path.read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            if re.search(pattern, source):
                errors.append(
                    "validator:local topology/version authority reintroduced:"
                    f"{source_path.relative_to(root).as_posix()}:{pattern}"
                )
    return errors


def main() -> int:
    errors = validate()
    print(json.dumps({"status": "valid" if not errors else "invalid", "errors": errors}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
