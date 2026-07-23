#!/usr/bin/env python3
"""Evaluate the canonical quality-first Architect runtime fixture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from architect_conversational_stage_output import load_output_files
from architect_quality_runtime import ROOT, RunContext, evaluate_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sequence",
        type=Path,
        default=ROOT / "fixtures/conversational-run/valid/minimal-complete-run",
    )
    parser.add_argument(
        "--terminal",
        type=Path,
        default=ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json",
    )
    args = parser.parse_args()
    outputs = load_output_files(args.sequence, root=ROOT)
    terminal = json.loads(args.terminal.read_text(encoding="utf-8"))
    result = evaluate_run(
        [*outputs, terminal],
        root=ROOT,
        run_context=RunContext(source_kind="fixture"),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
