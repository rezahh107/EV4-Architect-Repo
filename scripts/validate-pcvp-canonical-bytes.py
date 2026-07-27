"""Validate dormant Architect PCVP resources against one immutable snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

LOCK_PATH = "contracts/pcvp/architect-producer.lock.json"
LOCK_SCHEMA_VERSION = "ev4-pcvp-architect-producer-lock.v1"
CANONICAL_REPOSITORY = "rezahh107/EV4-Decision-Kernel"
CANONICAL_BUNDLE_ROOT = "kernel/pcvp/v1.0.0/bundle"
EXPECTED_RESOURCE_PAIRS = (
    (
        "contracts/pcvp/EV4_PCVP_MODEL_POLICY_v1.0.0.md",
        "02-MODEL_POLICY/EV4_PCVP_MODEL_POLICY_v1.0.0.md",
    ),
    (
        "contracts/pcvp/architect.profile.yaml",
        "03-PROFILES/architect.profile.yaml",
    ),
    (
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/authorization.schema.json",
        "04-SCHEMAS/authorization.schema.json",
    ),
    (
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/claim.schema.json",
        "04-SCHEMAS/claim.schema.json",
    ),
    (
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/effect.schema.json",
        "04-SCHEMAS/effect.schema.json",
    ),
    (
        "contracts/pcvp/vendor/decision-kernel/v1.0.0/handoff.schema.json",
        "04-SCHEMAS/handoff.schema.json",
    ),
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA1 = re.compile(r"^[0-9a-f]{40}$")


class CanonicalParityError(RuntimeError):
    """Raised when PCVP inventory identity or canonical byte parity fails."""


def _safe_relative_path(value: Any, *, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CanonicalParityError(f"Unsafe {field}: {value!r}")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CanonicalParityError(f"Unsafe {field}: {value!r}")
    return path


def _resolve_file(root: Path, relative: PurePosixPath, *, field: str) -> Path:
    try:
        resolved_root = root.resolve(strict=True)
        candidate = (resolved_root / Path(*relative.parts)).resolve(strict=True)
        candidate.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CanonicalParityError(
            f"{field} is unavailable or escaped its root: {relative.as_posix()}"
        ) from exc
    if not candidate.is_file():
        raise CanonicalParityError(
            f"{field} is not a regular file: {relative.as_posix()}"
        )
    return candidate


def _load_lock(repository_root: Path) -> dict[str, Any]:
    path = _resolve_file(
        repository_root,
        _safe_relative_path(LOCK_PATH, field="lock path"),
        field="PCVP lock",
    )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CanonicalParityError(
            f"PCVP lock could not be loaded: {type(exc).__name__}"
        ) from exc
    if not isinstance(value, dict):
        raise CanonicalParityError("PCVP lock must be a JSON object.")
    return value


def _checkout_head(checkout: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise CanonicalParityError(
            f"Decision Kernel checkout identity could not be read: {type(exc).__name__}"
        ) from exc
    if completed.returncode != 0:
        raise CanonicalParityError(
            "EV4_DECISION_KERNEL_CHECKOUT is not a readable Git checkout."
        )
    return completed.stdout.strip()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_canonical_bytes(
    repository_root: str | Path,
    decision_kernel_checkout: str | Path,
) -> dict[str, Any]:
    """Require exact local, lock, and immutable canonical resource identity."""

    root = Path(repository_root)
    checkout = Path(decision_kernel_checkout)
    lock = _load_lock(root)

    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        raise CanonicalParityError("PCVP lock schema identity drifted.")

    canonical = lock.get("canonical")
    if not isinstance(canonical, dict):
        raise CanonicalParityError("PCVP canonical lock section is malformed.")
    commit_sha = canonical.get("commit_sha")
    if (
        canonical.get("repository") != CANONICAL_REPOSITORY
        or canonical.get("bundle_root") != CANONICAL_BUNDLE_ROOT
        or not isinstance(commit_sha, str)
        or not GIT_SHA1.fullmatch(commit_sha)
    ):
        raise CanonicalParityError("PCVP canonical snapshot identity drifted.")

    verification = lock.get("verification")
    if verification != {
        "byte_equality_required": True,
        "compare_against_moving_default_branch": False,
    }:
        raise CanonicalParityError("PCVP canonical verification policy drifted.")

    observed_head = _checkout_head(checkout)
    if observed_head != commit_sha:
        raise CanonicalParityError(
            "Decision Kernel checkout Head mismatch: "
            f"expected {commit_sha}, observed {observed_head or '<empty>'}."
        )

    entries = lock.get("resources")
    if not isinstance(entries, list) or len(entries) != len(
        EXPECTED_RESOURCE_PAIRS
    ):
        raise CanonicalParityError("PCVP lock must declare exactly six resources.")

    normalized: list[tuple[PurePosixPath, PurePosixPath, str]] = []
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "canonical_path", "sha256"}
            or not isinstance(entry.get("sha256"), str)
            or not SHA256.fullmatch(entry["sha256"])
        ):
            raise CanonicalParityError("PCVP resource lock entry is malformed.")
        local_path = _safe_relative_path(entry.get("path"), field="local path")
        canonical_path = _safe_relative_path(
            entry.get("canonical_path"), field="canonical path"
        )
        normalized.append((local_path, canonical_path, entry["sha256"]))

    local_paths = [item[0].as_posix() for item in normalized]
    canonical_paths = [item[1].as_posix() for item in normalized]
    if len(set(local_paths)) != len(local_paths):
        raise CanonicalParityError("PCVP lock contains duplicate local paths.")
    if len(set(canonical_paths)) != len(canonical_paths):
        raise CanonicalParityError("PCVP lock contains duplicate canonical paths.")

    observed_pairs = set(zip(local_paths, canonical_paths, strict=True))
    if observed_pairs != set(EXPECTED_RESOURCE_PAIRS):
        raise CanonicalParityError(
            "PCVP resource inventory contains a missing, undeclared, or "
            "incorrect canonical path mapping."
        )

    bundle_root = _safe_relative_path(
        CANONICAL_BUNDLE_ROOT, field="canonical bundle root"
    )
    matches: list[dict[str, str]] = []
    for local_relative, canonical_relative, expected_digest in sorted(
        normalized, key=lambda item: item[0].as_posix()
    ):
        local_file = _resolve_file(
            root, local_relative, field="Local PCVP resource"
        )
        canonical_file = _resolve_file(
            checkout,
            PurePosixPath(*bundle_root.parts, *canonical_relative.parts),
            field="Canonical PCVP resource",
        )
        local_bytes = local_file.read_bytes()
        local_digest = _sha256(local_bytes)
        if local_digest != expected_digest:
            raise CanonicalParityError(
                "Local PCVP resource digest mismatch: "
                f"{local_relative.as_posix()}."
            )
        if local_bytes != canonical_file.read_bytes():
            raise CanonicalParityError(
                "Canonical PCVP byte mismatch: "
                f"{local_relative.as_posix()} != "
                f"{canonical_relative.as_posix()}."
            )
        matches.append(
            {
                "path": local_relative.as_posix(),
                "canonical_path": canonical_relative.as_posix(),
                "sha256": local_digest,
            }
        )

    return {
        "canonical_commit": commit_sha,
        "resource_count": len(matches),
        "matches": matches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Architect PCVP resources against Decision Kernel."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args(argv)
    checkout = os.environ.get("EV4_DECISION_KERNEL_CHECKOUT")
    if not checkout:
        print(
            "PCVP_CANONICAL_PARITY_FAILED: "
            "EV4_DECISION_KERNEL_CHECKOUT is required.",
            file=sys.stderr,
        )
        return 1

    try:
        result = validate_canonical_bytes(args.repository_root, checkout)
    except CanonicalParityError as exc:
        print(f"PCVP_CANONICAL_PARITY_FAILED: {exc}", file=sys.stderr)
        return 1

    for item in result["matches"]:
        print(
            f"MATCH {item['path']} {item['canonical_path']} {item['sha256']}"
        )
    print(
        "PCVP_CANONICAL_PARITY_OK "
        f"resources={result['resource_count']} "
        f"commit={result['canonical_commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
