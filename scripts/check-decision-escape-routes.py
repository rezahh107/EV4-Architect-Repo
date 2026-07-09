#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "planning" / "decision-escape-routes.schema.json"
STATE_PATH = REPO_ROOT / "planning" / "DECISION_ESCAPE_ROUTES.yml"
INVALID_CASES_PATH = REPO_ROOT / "fixtures" / "decision-escape-routes" / "invalid" / "cases.json"


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _error_path(error: Any) -> str:
    path = "$"
    for part in error.absolute_path:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def main() -> int:
    schema = _load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    state = _load_yaml(STATE_PATH)
    state_errors = sorted(validator.iter_errors(state), key=lambda error: (_error_path(error), error.message))
    if state_errors:
        for error in state_errors:
            print(f"state invalid: {_error_path(error)}: {error.message}", file=sys.stderr)
        return 1
    print(f"ok: {STATE_PATH.relative_to(REPO_ROOT)}")

    invalid_cases = _load_json(INVALID_CASES_PATH)
    failures = 0
    for case in invalid_cases:
        case_id = case.get("case_id", "<missing case_id>")
        errors = list(validator.iter_errors(case.get("payload")))
        if errors:
            print(f"ok: invalid fixture rejected: {case_id}")
        else:
            failures += 1
            print(f"invalid fixture unexpectedly passed: {case_id}", file=sys.stderr)
    if failures:
        print(f"fixture_failures: {failures}", file=sys.stderr)
        return 1
    print("fixture_failures: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
