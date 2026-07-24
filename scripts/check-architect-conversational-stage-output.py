#!/usr/bin/env python3
"""Validate conversational Stage Output examples, release sources, and full terminal Runtime semantics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from architect_conversational_stage_output import ROOT, validate_repository_vectors


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root used for deterministic source validation.",
    )
    parser.add_argument(
        "--terminal",
        type=Path,
        default=None,
        help="Optional terminal Stage Output path used for adversarial validation.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = validate_repository_vectors(root=args.root, terminal_path=args.terminal)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
