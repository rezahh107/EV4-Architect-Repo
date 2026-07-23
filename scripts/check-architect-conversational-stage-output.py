#!/usr/bin/env python3
"""Validate conversational Stage Output examples and fixtures."""
from __future__ import annotations

import json

from architect_conversational_stage_output import validate_repository_vectors


def main() -> int:
    result = validate_repository_vectors()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
