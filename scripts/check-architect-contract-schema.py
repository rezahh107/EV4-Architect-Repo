#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path(__file__).resolve().parents[1]
path = root / "schemas" / "ev4-architect-output-contract.v1.schema.json"
with path.open("r", encoding="utf-8") as handle:
    schema = json.load(handle)
Draft202012Validator.check_schema(schema)
print("schema ok")
