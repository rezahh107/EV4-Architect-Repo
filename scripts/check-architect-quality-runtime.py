#!/usr/bin/env python3
"""Validate the canonical quality-first Architect runtime fixture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from architect_quality_runtime import ROOT, validate_run_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run",
        type=Path,
        default=ROOT / "fixtures/architect-quality-runtime/valid/full-pipeline.json",
    )
    args = parser.parse_args()
    result = validate_run_file(args.run)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
