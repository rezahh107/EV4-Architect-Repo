#!/usr/bin/env python3
"""Canonical Architect Stage Payload checker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from architect_payload_semantic_validator import (
    ArchitectPayloadValidator,
    validate_fixture_suite,
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--file", type=Path)
    parser.add_argument(
        "--expect", choices=["valid", "invalid", "insufficient_evidence"]
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    validator = ArchitectPayloadValidator(root)
    if args.file:
        path = args.file if args.file.is_absolute() else root / args.file
        result = validator.validate_file(path)
        if args.format == "json":
            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        else:
            print(f"status: {result['status']}")
        if args.expect:
            return 0 if result["status"] == args.expect else 1
        return 0 if result["status"] == "valid" else 2 if result["status"] == "insufficient_evidence" else 1
    failures, reports = validate_fixture_suite(root)
    if args.format == "json":
        print(
            json.dumps(
                {"failures": failures, "reports": reports},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    else:
        for report in reports:
            print(
                f"{'ok' if report['ok'] else 'FAIL'}: {report['fixture']} "
                f"expected={report['expected']} actual={report['actual']} "
                f"codes={','.join(report['diagnostic_codes'])}"
            )
        print(f"fixture_failures: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
