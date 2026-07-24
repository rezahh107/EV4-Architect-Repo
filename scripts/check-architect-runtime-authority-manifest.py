#!/usr/bin/env python3
"""Validate the bounded Architect Runtime authority declaration."""
from __future__ import annotations

import json
from pathlib import Path

from architect_runtime_authority_manifest import (
    MANIFEST_PATH,
    RuntimeAuthorityManifestError,
    load_runtime_authority_manifest,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        manifest = load_runtime_authority_manifest(root)
    except RuntimeAuthorityManifestError as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "status": "valid",
                "manifest_path": str(MANIFEST_PATH),
                "runtime_interface_id": manifest["runtime_interface_id"],
                "python_authority_path_count": len(manifest["python_authority_paths"]),
                "data_authority_path_count": len(manifest["data_authority_paths"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
