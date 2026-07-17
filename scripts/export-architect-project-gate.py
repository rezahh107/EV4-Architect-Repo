#!/usr/bin/env python3
"""Emit the official Architect-owned Project Gate artifact."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
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
        raise ExportError("ARCH_EXPORT_INPUT_NOT_UTF8", "json_parse", "Payload must be UTF-8 JSON.", "architect") from exc
    except OSError as exc:
        raise ExportError("ARCH_EXPORT_INPUT_READ_FAILED", "json_parse", f"Payload could not be read: {type(exc).__name__}.", "operator") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ExportError("ARCH_EXPORT_MALFORMED_JSON", "json_parse", f"Payload is not strict JSON: {exc}.", "architect") from exc


def _finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ExportError("ARCH_EXPORT_NON_FINITE_NUMBER", "canonicalization", f"Non-finite number at {path}.", "architect")
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ExportError("ARCH_EXPORT_NON_STRING_KEY", "canonicalization", f"Non-string object key at {path}.", "architect")
        for key in sorted(value):
            _finite(value[key], f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite(item, f"{path}[{index}]")


def canonical_bytes(value: Any) -> bytes:
    _finite(value)
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ExportError("ARCH_EXPORT_CANONICALIZATION_FAILED", "canonicalization", str(exc), "architect") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", check=False)
    except OSError as exc:
        raise ExportError("ARCH_EXPORT_GIT_UNAVAILABLE", "git_provenance", "Git is unavailable.", "operator") from exc
    if result.returncode:
        raise ExportError("ARCH_EXPORT_GIT_COMMAND_FAILED", "git_provenance", result.stderr.strip() or result.stdout.strip() or "Git command failed.", "operator")
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
    absolute = path if path.is_absolute() else root / path
    if os.path.lexists(absolute) and absolute.is_symlink():
        raise ExportError("ARCH_EXPORT_UNSAFE_OUTPUT_PATH", "output_preflight", "Output must not be a symbolic link.", "operator")
    resolved = absolute.resolve()
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ExportError("ARCH_EXPORT_UNSAFE_OUTPUT_PATH", "output_preflight", "Output must remain inside the Architect repository.", "operator") from exc
    if relative.parts and relative.parts[0] == ".git":
        raise ExportError("ARCH_EXPORT_UNSAFE_OUTPUT_PATH", "output_preflight", "Output must not target Git metadata.", "operator")
    return resolved


def _is_tracked(root: Path, path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root.resolve())
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
        raise ExportError("ARCH_EXPORT_REPOSITORY_ROOT_MISMATCH", "git_provenance", "Run from the repository root.", "operator")
    remote = _git(root, "remote", "get-url", "origin")
    if (_remote_name(remote) or "").lower() != REPOSITORY.lower():
        raise ExportError("ARCH_EXPORT_WRONG_REPOSITORY", "git_provenance", f"origin must identify {REPOSITORY}; observed {remote!r}.", "repository_owner")
    try:
        ref = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    except ExportError as exc:
        raise ExportError("ARCH_EXPORT_DETACHED_HEAD", "git_provenance", "Detached HEAD cannot establish producer provenance.", "operator") from exc
    commit = _git(root, "rev-parse", "HEAD")
    if not SHA40.fullmatch(commit):
        raise ExportError("ARCH_EXPORT_INVALID_HEAD_SHA", "git_provenance", "HEAD is not a full commit SHA.", "operator")
    if _is_tracked(root, output):
        raise ExportError("ARCH_EXPORT_TRACKED_OUTPUT_FORBIDDEN", "output_preflight", "Output must not replace a tracked repository file.", "operator")
    allowed: set[Path] = set()
    for candidate in (payload, output, *tuple(allowed_paths)):
        try:
            allowed.add(candidate.resolve().relative_to(root.resolve()))
        except ValueError:
            pass
    dirty = []
    for line in _git(root, "-c", "core.quotepath=false", "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if line[:2] == "??" and _status_path(line) in allowed:
            continue
        dirty.append(line)
    if dirty:
        raise ExportError("ARCH_EXPORT_DIRTY_WORKTREE", "git_provenance", "Unrelated staged, unstaged, or untracked changes prevent reliable provenance.", "operator")
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


def validate_payload(root: Path, payload: Any) -> dict[str, Any]:
    path = root / "scripts/check-architect-stage-payload.py"
    spec = importlib.util.spec_from_file_location("architect_payload_validator", path)
    if spec is None or spec.loader is None:
        raise ExportError("ARCH_EXPORT_VALIDATOR_LOAD_FAILED", "semantic_validation", "Official Architect validator could not be loaded.", "repository_owner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        result = module.ArchitectPayloadValidator(root).validate_value(payload)
    except Exception as exc:
        raise ExportError("ARCH_EXPORT_VALIDATOR_LOAD_FAILED", "semantic_validation", f"Official validator failed: {type(exc).__name__}.", "repository_owner") from exc
    if result.get("status") == "invalid":
        codes = [item.get("code", "UNKNOWN") for item in result.get("diagnostics", []) if isinstance(item, dict)]
        raise ExportError("ARCH_EXPORT_ARCHITECT_PAYLOAD_INVALID", "semantic_validation", f"Official Architect validation failed: {', '.join(codes[:8])}.", "architect")
    if result.get("status") not in {"valid", "insufficient_evidence"}:
        raise ExportError("ARCH_EXPORT_VALIDATOR_RESULT_INVALID", "semantic_validation", "Official validator returned an unsupported status.", "repository_owner")
    return result


def _input_ref(root: Path, payload: Path) -> str:
    try:
        return str(payload.resolve().relative_to(root.resolve())).replace(os.sep, "/")
    except ValueError:
        return f"operator_input:{payload.name}"


def _source(source_type: str, reference: str) -> dict[str, str]:
    if source_type in {"repo_path", "schema", "contract"}:
        return {"type": "repo_path", "reference": reference}
    if source_type in {"fixture", "synthetic_fixture"}:
        return {"type": "synthetic_fixture", "reference": reference}
    prefix = "stage_payload:" if source_type == "stage_payload" else ""
    return {"type": "manual_observation", "reference": prefix + reference}


def _evidence(payload: dict[str, Any], payload_hash: str, input_ref: str) -> list[dict[str, Any]]:
    output = [{
        "id": "architect-stage-payload-canonical",
        "kind": "report",
        "state": "exported",
        "description": "Canonical identity of the Architect Stage Payload supplied to the exporter.",
        "artifact_hash": {"algorithm": "sha256", "value": payload_hash, "scope": "canonical_json"},
        "source": {"type": "manual_observation", "reference": input_ref},
        "derivation_rule": {"id": "ev4-canonical-json-sha256", "version": "1.0.0"},
    }]
    kinds = {"schema": "schema", "fixture": "fixture", "synthetic_fixture": "fixture", "contract": "document", "repo_path": "document", "stage_payload": "report"}
    for record in payload.get("evidence_register", []):
        source = record.get("source_ref", {})
        source_type = str(source.get("source_type", "manual_observation"))
        output.append({
            "id": str(record.get("evidence_id")),
            "kind": kinds.get(source_type, "other"),
            "state": str(record.get("state")),
            "description": str(record.get("claim")),
            "artifact_hash": {"algorithm": "sha256", "value": digest(record), "scope": "canonical_json"},
            "source": _source(source_type, str(source.get("reference", record.get("evidence_id", "unknown")))),
            "derivation_rule": {"id": "architect-evidence-record-canonicalization", "version": "1.0.0"},
        })
    return output


def _transition_blockers(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    boundaries = {"architect_stage_payload_acceptance", "ce_transition"}
    return [item for item in items if boundaries.intersection(item.get("blocks", [])) or item.get("required_before") in {"project_gate_acceptance", "ce_transition"}]


def build_export(payload: dict[str, Any], git: GitProvenance, run_id: str, input_ref: str) -> tuple[dict[str, Any], dict[str, str]]:
    run_id = run_id.strip()
    if not run_id:
        raise ExportError("ARCH_EXPORT_RUN_ID_REQUIRED", "run_identity", "--run-id is required to distinguish independent runs.", "operator")
    payload_hash = digest(payload)
    unresolved = [item for item in payload.get("unresolved_evidence", []) if isinstance(item, dict)]
    blockers = _transition_blockers(unresolved)
    insufficient = payload.get("payload_status") == "insufficient_evidence"
    synthetic = payload.get("synthetic") is True
    allowed = not insufficient and not synthetic and not blockers
    handoff_status = "insufficient_evidence" if insufficient else "blocked" if synthetic or blockers else "successful_with_flags" if unresolved else "successful"
    stage_status = "insufficient_evidence" if insufficient else "blocked" if synthetic or blockers else "complete"

    bundle_id = "architect-bundle-" + digest({"repository": git.repository, "commit": git.commit_sha, "run_id": run_id, "payload_hash": payload_hash})[:24]
    bundle: dict[str, Any] = {
        "schema_version": BUNDLE_VERSION,
        "bundle_id": bundle_id,
        "stage": "architect",
        "payload_schema": {"id": PAYLOAD_ID, "version": PAYLOAD_VERSION, "owner_repository": REPOSITORY},
        "produced_by": {"repository": git.repository, "ref": git.ref, "commit_sha": git.commit_sha},
        "evidence_status": str(payload.get("payload_status")),
        "payload": {"schema_id": PAYLOAD_ID, "data": payload},
        "evidence": _evidence(payload, payload_hash, input_ref),
        "provenance": {"source": f"architect_stage_payload:{input_ref}", "created_by": str(payload.get("payload_identity", {}).get("created_by", "ev4_architect"))},
        "synthetic": synthetic,
    }
    if insufficient:
        bundle["missing_evidence"] = [{"id": str(item.get("unresolved_id")), "owner": str(item.get("owner")), "reason": str(item.get("reason"))} for item in unresolved]
    bundle_hash = digest(bundle)
    export_id = "architect-export-" + digest({"repository": git.repository, "commit": git.commit_sha, "run_id": run_id, "bundle_hash": bundle_hash})[:24]

    diagnostics: list[dict[str, Any]] = []
    reasons: list[dict[str, Any]] = []
    if insufficient:
        diagnostics.append({"code": "ARCH_EXPORT_PAYLOAD_INSUFFICIENT_EVIDENCE", "severity": "error"})
        reasons.append({"id": "architect-payload-insufficient-evidence", "reason": "Architect payload is explicitly insufficient for handoff."})
    if synthetic:
        diagnostics.append({"code": "ARCH_EXPORT_SYNTHETIC_HANDOFF_FORBIDDEN", "severity": "error"})
        reasons.append({"id": "synthetic-run-not-authorized", "reason": "Synthetic payloads cannot authorize a real handoff."})
    diagnostics += [{"code": "ARCH_EXPORT_TRANSITION_EVIDENCE_BLOCKED", "severity": "error", "unresolved_id": item.get("unresolved_id")} for item in blockers]

    export = {
        "schema_version": EXPORT_VERSION,
        "export_id": export_id,
        "producer": {"stage": "architect", "repository": git.repository, "ref": git.ref, "commit_sha": git.commit_sha},
        "pipeline_id": PIPELINE_ID,
        "run_id": run_id,
        "stage_manifest": [{
            "stage_id": "/project-gate-export",
            "stage_version": "1.0.0",
            "ordinal": 12,
            "mandatory": True,
            "status": stage_status,
            "output": {"present": True, "artifact_ref": "final_stage_bundle", "artifact_hash": {"algorithm": "sha256", "value": bundle_hash, "scope": "canonical_json"}},
            "blockers": diagnostics,
            "unknowns": unresolved,
        }],
        "final_stage_bundle": bundle,
        "handoff": {"target": TARGET, "status": handoff_status, "allowed": allowed, "failure_reasons": reasons, "blocking_diagnostics": diagnostics, "unresolved_evidence": unresolved},
        "validation": {
            "schema_valid": True,
            "semantic_valid": True,
            "validator_id": "ev4-producer-gate-export-validator",
            "validator_version": "1.0.0",
            "diagnostics": [{"code": "ARCH_EXPORT_NONBLOCKING_UNRESOLVED_EVIDENCE", "severity": "warning", "count": len(unresolved)}] if unresolved and allowed else [],
        },
        "acquisition_mode": {"mode": "producer_emitted_gate_artifact", "silent_fallback_allowed": False},
    }
    hashes = {"payload_hash": payload_hash, "bundle_hash": bundle_hash, "export_hash": digest(export)}
    return export, hashes


def _errors(validator: Draft202012Validator, value: Any) -> list[str]:
    found = sorted(validator.iter_errors(value), key=lambda error: (list(error.absolute_path), error.message))
    return [f"{'/'.join(map(str, error.absolute_path)) or '$'}: {error.message}" for error in found]


def validate_contracts(root: Path, export: dict[str, Any]) -> None:
    bundle_schema = load_json(root / "contracts/project-gate/stage-bundle.v1.schema.json")
    export_schema = load_json(root / "contracts/project-gate/producer-gate-export.v1.schema.json")
    try:
        Draft202012Validator.check_schema(bundle_schema)
        Draft202012Validator.check_schema(export_schema)
        errors = _errors(Draft202012Validator(bundle_schema), export.get("final_stage_bundle"))
        if errors:
            raise ExportError("ARCH_EXPORT_STAGE_BUNDLE_SCHEMA_FAILED", "stage_bundle_validation", "; ".join(errors[:8]), "repository_owner")
        registry = Registry().with_resource(bundle_schema["$id"], Resource.from_contents(bundle_schema))
        errors = _errors(Draft202012Validator(export_schema, registry=registry), export)
        if errors:
            raise ExportError("ARCH_EXPORT_PRODUCER_EXPORT_SCHEMA_FAILED", "producer_export_validation", "; ".join(errors[:8]), "repository_owner")
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError("ARCH_EXPORT_CONTRACT_VALIDATION_FAILED", "contract_validation", f"Contract validation failed: {type(exc).__name__}: {exc}.", "repository_owner") from exc


def verify_hashes(export: dict[str, Any], expected: dict[str, str]) -> None:
    observed = {
        "payload_hash": digest(export.get("final_stage_bundle", {}).get("payload", {}).get("data")),
        "bundle_hash": digest(export.get("final_stage_bundle")),
        "export_hash": digest(export),
    }
    for key, value in expected.items():
        if observed.get(key) != value:
            raise ExportError("ARCH_EXPORT_HASH_SELF_VERIFICATION_FAILED", "hash_self_verification", f"{key} changed after construction or write.", "repository_owner")
    recorded = export.get("stage_manifest", [{}])[0].get("output", {}).get("artifact_hash", {}).get("value")
    if recorded != observed["bundle_hash"]:
        raise ExportError("ARCH_EXPORT_BUNDLE_HASH_MISMATCH", "hash_self_verification", "Recorded bundle hash does not match final_stage_bundle.", "repository_owner")


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        try:
            os.fsync(descriptor)
        except OSError:
            pass
    finally:
        os.close(descriptor)


def _identity(path: Path) -> tuple[int, int] | None:
    try:
        observed = os.lstat(path)
    except FileNotFoundError:
        return None
    return observed.st_dev, observed.st_ino


def _output_lock_path(path: Path) -> Path:
    normalized = os.path.normcase(os.path.abspath(os.fspath(path)))
    key = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / "ev4-architect-output-locks" / f"{key}.lock"


def _strict_json_bytes(data: bytes, stage: str) -> Any:
    try:
        text = data.decode("utf-8")
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except UnicodeDecodeError as exc:
        raise ExportError(
            "ARCH_EXPORT_OUTPUT_NOT_UTF8",
            stage,
            "Published output is not UTF-8 JSON.",
            "operator",
        ) from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ExportError(
            "ARCH_EXPORT_OUTPUT_MALFORMED_JSON",
            stage,
            f"Published output is not strict JSON: {exc}.",
            "operator",
        ) from exc


@dataclass
class OutputLock:
    path: Path
    descriptor: int | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            if fcntl is not None:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
            elif msvcrt is not None:
                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"0")
                    os.fsync(descriptor)
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
            else:
                raise ExportError(
                    "ARCH_EXPORT_OUTPUT_LOCK_UNAVAILABLE",
                    "output_lock",
                    "This platform does not provide the required exclusive output lock.",
                    "operator",
                )
        except ExportError:
            os.close(descriptor)
            raise
        except OSError as exc:
            os.close(descriptor)
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_LOCK_FAILED",
                "output_lock",
                f"The output transaction lock could not be acquired: {type(exc).__name__}.",
                "operator",
            ) from exc
        self.descriptor = descriptor

    def release(self) -> str | None:
        if self.descriptor is None:
            return None
        descriptor, self.descriptor = self.descriptor, None
        try:
            if fcntl is not None:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            elif msvcrt is not None:
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        except OSError as exc:
            return f"ARCH_EXPORT_OUTPUT_LOCK_RELEASE_FAILED:{type(exc).__name__}"
        finally:
            os.close(descriptor)
        return None


@dataclass
class OutputTransaction:
    path: Path
    candidate: Path
    expected_bytes: bytes
    lock: OutputLock
    published_identity: tuple[int, int] | None = None
    published_descriptor: int | None = None
    published: bool = False
    committed: bool = False
    backup: Path | None = None
    cleanup_warnings: list[str] = field(default_factory=list)

    @classmethod
    def stage(cls, path: Path, value: Any, overwrite: bool) -> "OutputTransaction":
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = OutputLock(_output_lock_path(path))
        lock.acquire()
        temp: Path | None = None
        try:
            if os.path.lexists(path):
                observed = os.lstat(path)
                if stat.S_ISLNK(observed.st_mode):
                    raise ExportError(
                        "ARCH_EXPORT_UNSAFE_OUTPUT_PATH",
                        "output_preflight",
                        "Output must not be a symbolic link.",
                        "operator",
                        destination_present=True,
                    )
                if not stat.S_ISREG(observed.st_mode):
                    raise ExportError(
                        "ARCH_EXPORT_OUTPUT_PATH_TYPE_INVALID",
                        "output_preflight",
                        "Existing output must be a regular file.",
                        "operator",
                        destination_present=True,
                    )
            if overwrite:
                raise ExportError(
                    "ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED",
                    "output_preflight",
                    "--overwrite is disabled because this platform-neutral exporter cannot atomically prove path ownership and destructively replace or restore a destination.",
                    "operator",
                    destination_present=os.path.lexists(path),
                )

            expected_bytes = canonical_bytes(value) + b"\n"
            with tempfile.NamedTemporaryFile(
                "wb",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp = Path(handle.name)
                handle.write(expected_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            return cls(
                path=path,
                candidate=temp,
                expected_bytes=expected_bytes,
                lock=lock,
            )
        except Exception:
            if temp is not None:
                temp.unlink(missing_ok=True)
            lock.release()
            raise

    def allowed_paths(self) -> tuple[Path, ...]:
        return (self.candidate,)

    def publish(self) -> None:
        candidate_identity = _identity(self.candidate)
        if candidate_identity is None:
            raise ExportError(
                "ARCH_EXPORT_STAGED_CANDIDATE_MISSING",
                "atomic_write",
                "The staged candidate disappeared before publication.",
                "operator",
            )
        try:
            os.link(self.candidate, self.path, follow_symlinks=False)
        except FileExistsError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_EXISTS",
                "atomic_write",
                "Output already exists at the atomic no-clobber publication boundary.",
                "operator",
                destination_present=True,
            ) from exc
        except (NotImplementedError, OSError) as exc:
            raise ExportError(
                "ARCH_EXPORT_ATOMIC_NO_CLOBBER_UNSUPPORTED",
                "atomic_write",
                f"Atomic no-clobber publication is unavailable: {type(exc).__name__}.",
                "operator",
                destination_present=os.path.lexists(self.path),
            ) from exc

        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.path, flags)
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_PUBLISHED_OUTPUT_OPEN_FAILED",
                "atomic_write",
                f"The published output could not be opened safely: {type(exc).__name__}.",
                "operator",
                destination_present=os.path.lexists(self.path),
            ) from exc

        observed = os.fstat(descriptor)
        published_identity = (observed.st_dev, observed.st_ino)
        if published_identity != candidate_identity:
            os.close(descriptor)
            raise ExportError(
                "ARCH_EXPORT_PUBLICATION_IDENTITY_MISMATCH",
                "atomic_write",
                "The destination no longer identifies the staged candidate.",
                "operator",
                destination_present=os.path.lexists(self.path),
                concurrent_destination_preserved=os.path.lexists(self.path),
            )

        self.published_descriptor = descriptor
        self.published_identity = published_identity
        self.published = True
        self.candidate.unlink(missing_ok=True)
        _fsync_directory(self.path.parent)

    def _owned_bytes(self) -> bytes:
        if self.published_descriptor is None:
            raise ExportError(
                "ARCH_EXPORT_PUBLICATION_NOT_OWNED",
                "post_write_validation",
                "No transaction-owned published descriptor is available.",
                "operator",
                destination_present=os.path.lexists(self.path),
            )
        os.lseek(self.published_descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(self.published_descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)

    def verify_owned(self, stage: str) -> bytes:
        if self.published_descriptor is None or self.published_identity is None:
            raise ExportError(
                "ARCH_EXPORT_PUBLICATION_NOT_OWNED",
                stage,
                "No transaction-owned publication identity is available.",
                "operator",
                destination_present=os.path.lexists(self.path),
            )
        descriptor_stat = os.fstat(self.published_descriptor)
        descriptor_identity = (descriptor_stat.st_dev, descriptor_stat.st_ino)
        current_identity = _identity(self.path)
        if descriptor_identity != self.published_identity or current_identity != self.published_identity:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_IDENTITY_DRIFT",
                stage,
                "The destination path no longer identifies the transaction-owned output.",
                "operator",
                destination_present=current_identity is not None,
                concurrent_destination_preserved=(
                    current_identity is not None and current_identity != self.published_identity
                ),
            )
        observed_bytes = self._owned_bytes()
        if observed_bytes != self.expected_bytes:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_BYTE_DRIFT",
                stage,
                "The transaction-owned output bytes changed after publication.",
                "operator",
                destination_present=True,
            )
        return observed_bytes

    def rollback(self) -> None:
        # PRF-004: rollback is deliberately namespace-nondestructive. A failed
        # post-publication artifact is retained for operator inspection and is
        # never removed or replaced based on a previously observed identity.
        self.candidate.unlink(missing_ok=True)
        if self.published:
            self.cleanup_warnings.append(
                f"ARCH_EXPORT_FAILED_OUTPUT_RETAINED:{self.path.name}"
            )

    def commit(self) -> list[str]:
        self.verify_owned("publication_commit")
        self.committed = True
        _fsync_directory(self.path.parent)
        return list(self.cleanup_warnings)

    def close(self) -> list[str]:
        self.candidate.unlink(missing_ok=True)
        if self.published_descriptor is not None:
            try:
                os.close(self.published_descriptor)
            except OSError as exc:
                self.cleanup_warnings.append(
                    f"ARCH_EXPORT_OUTPUT_DESCRIPTOR_CLOSE_FAILED:{type(exc).__name__}"
                )
            self.published_descriptor = None
        warning = self.lock.release()
        if warning is not None:
            self.cleanup_warnings.append(warning)
        return list(self.cleanup_warnings)


def _historical_result(
    export: dict[str, Any],
    hashes: dict[str, str],
    initial_git: GitProvenance,
    root: Path,
    output_path: Path,
    cleanup_warnings: list[str],
) -> ExportResult:
    return ExportResult(
        status=export["handoff"]["status"],
        output_path=str(output_path.relative_to(root)).replace(os.sep, "/"),
        export_id=export["export_id"],
        payload_hash=hashes["payload_hash"],
        bundle_hash=hashes["bundle_hash"],
        export_hash=hashes["export_hash"],
        producer_commit=initial_git.commit_sha,
        handoff_target=TARGET,
        handoff_allowed=export["handoff"]["allowed"],
        output_written=False,
        output_committed=True,
        destination_present=True,
        concurrent_destination_preserved=False,
        backup_retained=False,
        backup_path=None,
        receipt_scope="historical_commit",
        current_destination_claim=False,
        cleanup_warnings=cleanup_warnings,
    )


def atomic_write(path: Path, value: Any, overwrite: bool) -> list[str]:
    transaction = OutputTransaction.stage(path, value, overwrite)
    warnings: list[str] = []
    try:
        transaction.publish()
        transaction.verify_owned("atomic_write_final_verification")
        warnings = transaction.commit()
    except Exception as exc:
        try:
            transaction.rollback()
        except Exception as rollback_exc:  # pragma: no cover - defensive only
            raise ExportError(
                "ARCH_EXPORT_ROLLBACK_FAILED",
                "post_write_validation",
                f"Nondestructive rollback cleanup failed: {type(rollback_exc).__name__}.",
                "operator",
                destination_present=os.path.lexists(path),
            ) from exc
        raise
    finally:
        warnings = transaction.close()
    return warnings


def run_export(
    root: Path,
    payload_path: Path,
    output_path: Path,
    run_id: str,
    overwrite: bool = False,
    provenance_provider: Callable[[Path, Path, Path, Iterable[Path]], GitProvenance] = inspect_repository,
    receipt_emitter: Callable[[ExportResult], None] | None = None,
) -> ExportResult:
    root, payload_path = root.resolve(), payload_path.resolve()
    output_path = inside(root, output_path)
    if output_path == payload_path:
        raise ExportError(
            "ARCH_EXPORT_INPUT_OUTPUT_COLLISION",
            "output_preflight",
            "Output must not replace the source payload.",
            "operator",
        )
    payload = load_json(payload_path)
    if not isinstance(payload, dict):
        raise ExportError(
            "ARCH_EXPORT_PAYLOAD_NOT_OBJECT",
            "semantic_validation",
            "Architect payload must be an object.",
            "architect",
        )
    validate_payload(root, payload)
    initial_git = provenance_provider(root, payload_path, output_path, ())
    export, hashes = build_export(payload, initial_git, run_id, _input_ref(root, payload_path))
    validate_contracts(root, export)
    verify_hashes(export, hashes)

    transaction = OutputTransaction.stage(output_path, export, overwrite)
    result: ExportResult | None = None
    try:
        staged = load_json(transaction.candidate)
        validate_contracts(root, staged)
        verify_hashes(staged, hashes)

        prepublish_git = provenance_provider(
            root,
            payload_path,
            output_path,
            transaction.allowed_paths(),
        )
        _assert_same_provenance(
            initial_git,
            prepublish_git,
            "prepublication_provenance",
        )

        transaction.publish()
        owned_bytes = transaction.verify_owned("postpublication_identity_and_bytes")
        reread = _strict_json_bytes(owned_bytes, "postpublication_validation")
        validate_contracts(root, reread)
        verify_hashes(reread, hashes)

        final_git = provenance_provider(
            root,
            payload_path,
            output_path,
            transaction.allowed_paths(),
        )
        _assert_same_provenance(initial_git, final_git, "final_provenance")

        final_bytes = transaction.verify_owned("final_destination_verification")
        final_reread = _strict_json_bytes(final_bytes, "final_destination_validation")
        validate_contracts(root, final_reread)
        verify_hashes(final_reread, hashes)

        cleanup_warnings = transaction.commit()
        transaction.verify_owned("success_receipt_boundary")
        result = _historical_result(
            export,
            hashes,
            initial_git,
            root,
            output_path,
            cleanup_warnings,
        )
        if receipt_emitter is not None:
            try:
                receipt_emitter(result)
            except Exception as exc:
                raise ExportError(
                    "ARCH_EXPORT_RECEIPT_EMIT_FAILED",
                    "success_receipt",
                    f"The historical success receipt could not be emitted: {type(exc).__name__}.",
                    "operator",
                    output_committed=True,
                    destination_present=os.path.lexists(output_path),
                ) from exc
    except Exception as exc:
        try:
            transaction.rollback()
        except Exception as rollback_exc:
            raise ExportError(
                "ARCH_EXPORT_ROLLBACK_FAILED",
                "post_write_validation",
                f"Nondestructive rollback cleanup failed: {type(rollback_exc).__name__}.",
                "operator",
                output_committed=transaction.committed,
                destination_present=os.path.lexists(output_path),
            ) from exc
        if isinstance(exc, ExportError):
            current_identity = _identity(output_path)
            exc.output_written = False
            exc.output_committed = transaction.committed
            exc.destination_present = current_identity is not None
            exc.concurrent_destination_preserved = (
                transaction.published_identity is not None
                and current_identity is not None
                and current_identity != transaction.published_identity
            )
            exc.cleanup_warnings = list(transaction.cleanup_warnings)
        raise
    finally:
        close_warnings = transaction.close()

    if result is None:  # pragma: no cover - defensive only
        raise ExportError(
            "ARCH_EXPORT_RESULT_MISSING",
            "success_receipt",
            "Exporter completed without producing a receipt.",
            "repository_owner",
            output_committed=transaction.committed,
            destination_present=os.path.lexists(output_path),
        )
    if close_warnings != result.cleanup_warnings:
        result = ExportResult(
            status=result.status,
            output_path=result.output_path,
            export_id=result.export_id,
            payload_hash=result.payload_hash,
            bundle_hash=result.bundle_hash,
            export_hash=result.export_hash,
            producer_commit=result.producer_commit,
            handoff_target=result.handoff_target,
            handoff_allowed=result.handoff_allowed,
            output_written=False,
            output_committed=True,
            destination_present=result.destination_present,
            concurrent_destination_preserved=False,
            backup_retained=False,
            backup_path=None,
            receipt_scope="historical_commit",
            current_destination_claim=False,
            cleanup_warnings=close_warnings,
        )
    return result


def render(data: dict[str, Any], mode: str) -> str:
    if mode == "json":
        return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "\n".join(
        f"{key}: {str(value).lower() if isinstance(value, bool) else value}"
        for key, value in data.items()
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit the official Architect Project Gate artifact."
    )
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_OUTPUT))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    payload = args.payload if args.payload.is_absolute() else root / args.payload
    output = args.output if args.output.is_absolute() else root / args.output

    emitted = False

    def emit_receipt(result: ExportResult) -> None:
        nonlocal emitted
        print(render(asdict(result), args.format), flush=True)
        emitted = True

    try:
        result = run_export(
            root,
            payload,
            output,
            args.run_id,
            args.overwrite,
            receipt_emitter=emit_receipt,
        )
        if not emitted:  # pragma: no cover - defensive only
            emit_receipt(result)
        if result.cleanup_warnings:
            cleanup_update = {
                "receipt_update": "post_release_cleanup",
                "cleanup_warnings": result.cleanup_warnings,
            }
            print(render(cleanup_update, args.format), file=sys.stderr, flush=True)
        return 0 if result.handoff_allowed else 2
    except ExportError as exc:
        print(render(exc.report(), args.format), file=sys.stderr, flush=True)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
