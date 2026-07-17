#!/usr/bin/env python3
"""Emit the official Architect-owned Project Gate artifact."""
from __future__ import annotations

import argparse
import errno
import hashlib
import importlib.util
import json
import math
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX fallback
    msvcrt = None

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPOSITORY = "rezahh107/EV4-Architect-Repo"
PAYLOAD_ID = "ev4-architect-stage-payload@1.0.0"
PAYLOAD_VERSION = "1.0.0"
BUNDLE_VERSION = "stage-evidence-bundle.v1"
EXPORT_VERSION = "producer-gate-export.v1"
PIPELINE_ID = "ev4-architect-pipeline"
TARGET = "ce-intake"
DEFAULT_OUTPUT = "architect-project-gate.json"
SHA40 = re.compile(r"^[a-f0-9]{40}$")
_DIR_FD_CAPABILITIES = {
    getattr(function, "__name__", "")
    for function in getattr(os, "supports_dir_fd", ())
}
_FOLLOW_SYMLINK_CAPABILITIES = {
    getattr(function, "__name__", "")
    for function in getattr(os, "supports_follow_symlinks", ())
}


@dataclass(frozen=True)
class GitProvenance:
    repository: str
    ref: str
    commit_sha: str


@dataclass(frozen=True)
class ExportResult:
    status: str
    output_path: str
    export_id: str
    payload_hash: str
    bundle_hash: str
    export_hash: str
    producer_commit: str
    handoff_target: str
    handoff_allowed: bool
    output_written: bool = False
    output_committed: bool = False
    destination_present: bool = False
    concurrent_destination_preserved: bool = False
    backup_retained: bool = False
    backup_path: str | None = None
    receipt_scope: str = "historical_commit"
    current_destination_claim: bool = False
    cleanup_warnings: list[str] = field(default_factory=list)


class ExportError(RuntimeError):
    def __init__(
        self,
        code: str,
        stage: str,
        reason: str,
        owner: str,
        exit_code: int = 1,
        output_written: bool = False,
        output_committed: bool = False,
        destination_present: bool = False,
        concurrent_destination_preserved: bool = False,
        backup_retained: bool = False,
        backup_path: str | None = None,
        cleanup_warnings: list[str] | None = None,
    ):
        super().__init__(reason)
        self.code, self.stage, self.reason = code, stage, reason
        self.owner, self.exit_code = owner, exit_code
        self.output_written = output_written
        self.output_committed = output_committed
        self.destination_present = destination_present
        self.concurrent_destination_preserved = concurrent_destination_preserved
        self.backup_retained = backup_retained
        self.backup_path = backup_path
        self.cleanup_warnings = list(cleanup_warnings or [])

    def report(self) -> dict[str, Any]:
        return {
            "diagnostic_code": self.code,
            "failed_stage": self.stage,
            "reason": self.reason,
            "repair_owner": self.owner,
            "output_written": self.output_written,
            "output_committed": self.output_committed,
            "destination_present": self.destination_present,
            "concurrent_destination_preserved": self.concurrent_destination_preserved,
            "backup_retained": self.backup_retained,
            "backup_path": self.backup_path,
            "cleanup_warnings": list(self.cleanup_warnings),
            "handoff_prohibited": True,
        }


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate object key: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite number: {value}")


def load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except UnicodeDecodeError as exc:
        raise ExportError(
            "ARCH_EXPORT_INPUT_NOT_UTF8", "json_parse", "Payload must be UTF-8 JSON.", "architect"
        ) from exc
    except OSError as exc:
        raise ExportError(
            "ARCH_EXPORT_INPUT_READ_FAILED",
            "json_parse",
            f"Payload could not be read: {type(exc).__name__}.",
            "operator",
        ) from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ExportError(
            "ARCH_EXPORT_MALFORMED_JSON",
            "json_parse",
            f"Payload is not strict JSON: {exc}.",
            "architect",
        ) from exc


def _finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ExportError(
            "ARCH_EXPORT_NON_FINITE_NUMBER",
            "canonicalization",
            f"Non-finite number at {path}.",
            "architect",
        )
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ExportError(
                    "ARCH_EXPORT_NON_STRING_KEY",
                    "canonicalization",
                    f"Non-string object key at {path}.",
                    "architect",
                )
        for key in sorted(value):
            _finite(value[key], f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite(item, f"{path}[{index}]")


def canonical_bytes(value: Any) -> bytes:
    _finite(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ExportError(
            "ARCH_EXPORT_CANONICALIZATION_FAILED", "canonicalization", str(exc), "architect"
        ) from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as exc:
        raise ExportError(
            "ARCH_EXPORT_GIT_UNAVAILABLE", "git_provenance", "Git is unavailable.", "operator"
        ) from exc
    if result.returncode:
        raise ExportError(
            "ARCH_EXPORT_GIT_COMMAND_FAILED",
            "git_provenance",
            result.stderr.strip() or result.stdout.strip() or "Git command failed.",
            "operator",
        )
    return result.stdout.strip()


def _remote_name(remote: str) -> str | None:
    for pattern in (
        r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?",
        r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?",
        r"ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?",
    ):
        match = re.fullmatch(pattern, remote.strip())
        if match:
            return match.group(1).removesuffix(".git")
    return None


def _status_path(line: str) -> Path:
    value = line[3:] if len(line) > 3 else ""
    value = value.split(" -> ", 1)[-1]
    if value.startswith('"') and value.endswith('"'):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
    return Path(value)


def inside(root: Path, path: Path) -> Path:
    """Return a lexical absolute output path without following output components."""
    root = root.resolve()
    supplied = path if path.is_absolute() else root / path
    absolute = Path(os.path.abspath(os.fspath(supplied)))
    try:
        relative = absolute.relative_to(root)
    except ValueError as exc:
        raise ExportError(
            "ARCH_EXPORT_UNSAFE_OUTPUT_PATH",
            "output_preflight",
            "Output must remain inside the Architect repository.",
            "operator",
        ) from exc
    if relative.parts and relative.parts[0] == ".git":
        raise ExportError(
            "ARCH_EXPORT_UNSAFE_OUTPUT_PATH",
            "output_preflight",
            "Output must not target Git metadata.",
            "operator",
        )
    return absolute


def _is_tracked(root: Path, path: Path) -> bool:
    try:
        relative = Path(os.path.abspath(os.fspath(path))).relative_to(root.resolve())
    except ValueError:
        return False
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", str(relative)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return result.returncode == 0


def inspect_repository(
    root: Path,
    payload: Path,
    output: Path,
    allowed_paths: Iterable[Path] = (),
) -> GitProvenance:
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise ExportError(
            "ARCH_EXPORT_REPOSITORY_ROOT_MISMATCH",
            "git_provenance",
            "Run from the repository root.",
            "operator",
        )
    remote = _git(root, "remote", "get-url", "origin")
    if (_remote_name(remote) or "").lower() != REPOSITORY.lower():
        raise ExportError(
            "ARCH_EXPORT_WRONG_REPOSITORY",
            "git_provenance",
            f"origin must identify {REPOSITORY}; observed {remote!r}.",
            "repository_owner",
        )
    try:
        ref = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    except ExportError as exc:
        raise ExportError(
            "ARCH_EXPORT_DETACHED_HEAD",
            "git_provenance",
            "Detached HEAD cannot establish producer provenance.",
            "operator",
        ) from exc
    commit = _git(root, "rev-parse", "HEAD")
    if not SHA40.fullmatch(commit):
        raise ExportError(
            "ARCH_EXPORT_INVALID_HEAD_SHA",
            "git_provenance",
            "HEAD is not a full commit SHA.",
            "operator",
        )
    if _is_tracked(root, output):
        raise ExportError(
            "ARCH_EXPORT_TRACKED_OUTPUT_FORBIDDEN",
            "output_preflight",
            "Output must not replace a tracked repository file.",
            "operator",
        )
    allowed: set[Path] = set()
    for candidate in (payload, output, *tuple(allowed_paths)):
        try:
            allowed.add(Path(os.path.abspath(os.fspath(candidate))).relative_to(root.resolve()))
        except ValueError:
            pass
    dirty = []
    for line in _git(
        root,
        "-c",
        "core.quotepath=false",
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).splitlines():
        if line[:2] == "??" and _status_path(line) in allowed:
            continue
        dirty.append(line)
    if dirty:
        raise ExportError(
            "ARCH_EXPORT_DIRTY_WORKTREE",
            "git_provenance",
            "Unrelated staged, unstaged, or untracked changes prevent reliable provenance.",
            "operator",
        )
    return GitProvenance(REPOSITORY, ref, commit)


def _assert_same_provenance(expected: GitProvenance, observed: GitProvenance, stage: str) -> None:
    if observed == expected:
        return
    changes = []
    if observed.repository != expected.repository:
        changes.append("repository")
    if observed.ref != expected.ref:
        changes.append("ref")
    if observed.commit_sha != expected.commit_sha:
        changes.append("HEAD")
    raise ExportError(
        "ARCH_EXPORT_PROVENANCE_DRIFT",
        stage,
        f"Git provenance changed during export: {', '.join(changes) or 'unknown field'}.",
        "operator",
    )
