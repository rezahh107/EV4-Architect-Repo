#!/usr/bin/env python3
"""Validate Architect output contract positive and negative fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ev4-architect-output-contract.v1.schema.json"
FIXTURE_ROOT = ROOT / "fixtures" / "architect-output-contract" / "v1"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fixture_files(kind: str) -> list[Path]:
    folder = FIXTURE_ROOT / kind
    return sorted(folder.glob("*.json"))


def main() -> None:
    schema = load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    valid_files = fixture_files("valid")
    invalid_files = fixture_files("invalid")

    if not valid_files:
        raise AssertionError("No valid Architect contract fixtures found")
    if not invalid_files:
        raise AssertionError("No invalid Architect contract fixtures found")

    for path in valid_files:
        errors = sorted(validator.iter_errors(load_json(path)), key=lambda error: list(error.path))
        if errors:
            messages = "\n".join(f"- {list(error.path)}: {error.message}" for error in errors)
            raise AssertionError(f"Expected valid fixture to pass: {path}\n{messages}")

    for path in invalid_files:
        errors = sorted(validator.iter_errors(load_json(path)), key=lambda error: list(error.path))
        if not errors:
            raise AssertionError(f"Expected invalid fixture to fail: {path}")

    print(f"validated {len(valid_files)} valid and {len(invalid_files)} invalid Architect fixtures")


if __name__ == "__main__":
    main()
