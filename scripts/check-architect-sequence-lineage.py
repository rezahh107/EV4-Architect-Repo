#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_LINEAGE_FIELDS = [
    "decision_family",
    "decision_card_ref",
    "selected_option",
    "rejected_options",
    "evidence_refs",
    "evidence_state",
]


def _load_payload_validator(repo_root: Path):
    script = repo_root / "scripts" / "check-architect-stage-payload.py"
    spec = importlib.util.spec_from_file_location("architect_payload_validator", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules["architect_payload_validator"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.ArchitectPayloadValidator(repo_root)


def _path_tokens(path: str) -> list[str | int]:
    return [int(part) if part.isdigit() else part for part in path.split(".") if part]


def _set_path(value: dict[str, Any], path: str, new_value: Any) -> None:
    current: Any = value
    parts = _path_tokens(path)
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = new_value


def _delete_path(value: dict[str, Any], path: str) -> None:
    current: Any = value
    parts = _path_tokens(path)
    for part in parts[:-1]:
        current = current[part]
    del current[parts[-1]]


def _load_step_payload(repo_root: Path, sequence_path: Path, step: dict[str, Any]) -> dict[str, Any]:
    if "payload" in step:
        return copy.deepcopy(step["payload"])
    payload_path = sequence_path.parent / step["payload_path"]
    if not payload_path.is_absolute():
        payload_path = payload_path.resolve()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    for mutation in step.get("mutations", []):
        if mutation["op"] == "set":
            _set_path(payload, mutation["path"], mutation["value"])
        elif mutation["op"] == "delete":
            _delete_path(payload, mutation["path"])
        else:
            raise ValueError(f"Unsupported mutation op: {mutation['op']}")
    return payload


def _lineage_snapshot(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = payload.get("kernel_decision_records")
    if not isinstance(records, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    consumer_stage = payload.get("payload_identity", {}).get("stage")
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("decision_family"), str):
            continue
        item = {field: record.get(field) for field in REQUIRED_LINEAGE_FIELDS}
        item["consumer_stage"] = consumer_stage
        out[record["decision_family"]] = item
    return out


def validate_sequence(repo_root: Path, sequence_path: Path) -> dict[str, Any]:
    data = json.loads(sequence_path.read_text(encoding="utf-8"))
    validator = _load_payload_validator(repo_root)
    diagnostics: list[dict[str, Any]] = []
    baseline: dict[str, dict[str, Any]] | None = None
    baseline_step = None

    for index, step in enumerate(data.get("steps", [])):
        payload = _load_step_payload(repo_root, sequence_path, step)
        step_name = step.get("step_id", f"step-{index}")
        result = validator.validate_value(payload)
        if result["status"] == "invalid":
            diagnostics.append({
                "code": "ARCH-SEQUENCE-PAYLOAD-INVALID",
                "path": f"$.steps[{index}]",
                "message": "Sequence step payload must pass Architect Stage Payload validation before lineage comparison.",
                "step_id": step_name,
                "payload_diagnostic_codes": [item["code"] for item in result["diagnostics"]],
            })
            continue

        current = _lineage_snapshot(payload)
        for family, lineage in current.items():
            for field in [*REQUIRED_LINEAGE_FIELDS, "consumer_stage"]:
                value = lineage.get(field)
                if value in (None, "") or value == []:
                    diagnostics.append({
                        "code": "ARCH-SEQUENCE-LINEAGE-FIELD-MISSING",
                        "path": f"$.steps[{index}].kernel_decision_records.{family}.{field}",
                        "message": "Kernel decision lineage field must be preserved across Architect sequence steps.",
                        "step_id": step_name,
                        "decision_family": family,
                        "field": field,
                    })
        if baseline is None:
            baseline = current
            baseline_step = step_name
            continue
        for family, expected in baseline.items():
            actual = current.get(family)
            if actual is None:
                diagnostics.append({
                    "code": "ARCH-SEQUENCE-LINEAGE-RECORD-MISSING",
                    "path": f"$.steps[{index}].kernel_decision_records",
                    "message": "Kernel decision record present in the initial Architect step is missing from a later Architect step.",
                    "step_id": step_name,
                    "baseline_step_id": baseline_step,
                    "decision_family": family,
                })
                continue
            for field, expected_value in expected.items():
                if actual.get(field) != expected_value:
                    diagnostics.append({
                        "code": "ARCH-SEQUENCE-LINEAGE-DRIFT",
                        "path": f"$.steps[{index}].kernel_decision_records.{family}.{field}",
                        "message": "Kernel decision lineage changed across Architect sequence steps without a new inspected decision record.",
                        "step_id": step_name,
                        "baseline_step_id": baseline_step,
                        "decision_family": family,
                        "field": field,
                    })
    return {"status": "invalid" if diagnostics else "valid", "diagnostics": diagnostics}


def iter_sequence_fixtures(repo_root: Path):
    root = repo_root / "fixtures" / "architect-stage-payload" / "sequence"
    for expected_dir, expected_status in [("valid", "valid"), ("invalid", "invalid")]:
        for path in sorted((root / expected_dir).glob("*.json")):
            yield path, expected_status


def validate_sequence_suite(repo_root: Path) -> tuple[int, list[dict[str, Any]]]:
    reports = []
    failures = 0
    for path, expected in iter_sequence_fixtures(repo_root):
        result = validate_sequence(repo_root, path)
        ok = result["status"] == expected
        failures += 0 if ok else 1
        reports.append({
            "fixture": str(path.relative_to(repo_root)),
            "expected": expected,
            "actual": result["status"],
            "ok": ok,
            "diagnostic_codes": [item["code"] for item in result["diagnostics"]],
        })
    return failures, reports


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd(), type=Path)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--expect", choices=["valid", "invalid"])
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.file:
        path = args.file if args.file.is_absolute() else repo_root / args.file
        result = validate_sequence(repo_root, path)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) if args.format == "json" else f"status: {result['status']}")
        if args.expect:
            return 0 if result["status"] == args.expect else 1
        return 0 if result["status"] == "valid" else 1
    failures, reports = validate_sequence_suite(repo_root)
    if args.format == "json":
        print(json.dumps({"failures": failures, "reports": reports}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        for report in reports:
            print(f"{'ok' if report['ok'] else 'FAIL'}: {report['fixture']} expected={report['expected']} actual={report['actual']} codes={','.join(report['diagnostic_codes'])}")
        print(f"sequence_fixture_failures: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
