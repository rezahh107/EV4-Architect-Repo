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
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

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
    output_written: bool = True


class ExportError(RuntimeError):
    def __init__(self, code: str, stage: str, reason: str, owner: str, exit_code: int = 1, output_written: bool = False):
        super().__init__(reason)
        self.code, self.stage, self.reason = code, stage, reason
        self.owner, self.exit_code, self.output_written = owner, exit_code, output_written

    def report(self) -> dict[str, Any]:
        return {
            "diagnostic_code": self.code,
            "failed_stage": self.stage,
            "reason": self.reason,
            "repair_owner": self.owner,
            "output_written": self.output_written,
            "handoff_prohibited": True,
        }


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate object key: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite number: {value}")),
        )
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
        for key in sorted(value):
            if not isinstance(key, str):
                raise ExportError("ARCH_EXPORT_NON_STRING_KEY", "canonicalization", f"Non-string object key at {path}.", "architect")
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
    resolved = path.resolve()
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


def inspect_repository(root: Path, payload: Path, output: Path) -> GitProvenance:
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
    for candidate in (payload, output):
        try:
            allowed.add(candidate.resolve().relative_to(root.resolve()))
        except ValueError:
            pass
    dirty = []
    for line in _git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if line[:2] == "??" and _status_path(line) in allowed:
            continue
        dirty.append(line)
    if dirty:
        raise ExportError("ARCH_EXPORT_DIRTY_WORKTREE", "git_provenance", "Unrelated staged, unstaged, or untracked changes prevent reliable provenance.", "operator")
    return GitProvenance(REPOSITORY, ref, commit)


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


def atomic_write(path: Path, value: Any, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise ExportError("ARCH_EXPORT_OUTPUT_EXISTS", "atomic_write", "Output exists; pass --overwrite only intentionally.", "operator")
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temp = Path(handle.name)
            handle.write(canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists() and not overwrite:
            raise ExportError("ARCH_EXPORT_OUTPUT_EXISTS", "atomic_write", "Output appeared during write; nothing was replaced.", "operator")
        os.replace(temp, path)
        temp = None
    finally:
        if temp:
            temp.unlink(missing_ok=True)


def run_export(
    root: Path,
    payload_path: Path,
    output_path: Path,
    run_id: str,
    overwrite: bool = False,
    provenance_provider: Callable[[Path, Path, Path], GitProvenance] = inspect_repository,
) -> ExportResult:
    root, payload_path = root.resolve(), payload_path.resolve()
    output_path = inside(root, output_path)
    if output_path == payload_path:
        raise ExportError("ARCH_EXPORT_INPUT_OUTPUT_COLLISION", "output_preflight", "Output must not replace the source payload.", "operator")
    if output_path.exists() and not overwrite:
        raise ExportError("ARCH_EXPORT_OUTPUT_EXISTS", "output_preflight", "Output exists; pass --overwrite only intentionally.", "operator")
    payload = load_json(payload_path)
    validate_payload(root, payload)
    if not isinstance(payload, dict):
        raise ExportError("ARCH_EXPORT_PAYLOAD_NOT_OBJECT", "semantic_validation", "Architect payload must be an object.", "architect")
    git = provenance_provider(root, payload_path, output_path)
    export, hashes = build_export(payload, git, run_id, _input_ref(root, payload_path))
    validate_contracts(root, export)
    verify_hashes(export, hashes)
    try:
        atomic_write(output_path, export, overwrite)
        reread = load_json(output_path)
        validate_contracts(root, reread)
        verify_hashes(reread, hashes)
    except Exception as exc:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            if isinstance(exc, ExportError):
                exc.output_written = output_path.exists()
            else:
                raise ExportError(
                    "ARCH_EXPORT_POSTWRITE_CLEANUP_FAILED",
                    "post_write_validation",
                    "Post-write validation failed and the invalid artifact could not be removed.",
                    "operator",
                    output_written=output_path.exists(),
                ) from exc
        raise
    return ExportResult(
        status=export["handoff"]["status"],
        output_path=str(output_path.relative_to(root)).replace(os.sep, "/"),
        export_id=export["export_id"],
        payload_hash=hashes["payload_hash"],
        bundle_hash=hashes["bundle_hash"],
        export_hash=hashes["export_hash"],
        producer_commit=git.commit_sha,
        handoff_target=TARGET,
        handoff_allowed=export["handoff"]["allowed"],
    )


def render(data: dict[str, Any], mode: str) -> str:
    if mode == "json":
        return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "\n".join(f"{key}: {str(value).lower() if isinstance(value, bool) else value}" for key, value in data.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit the official Architect Project Gate artifact.")
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
    try:
        result = run_export(root, payload, output, args.run_id, args.overwrite)
        print(render(asdict(result), args.format))
        return 0 if result.handoff_allowed else 2
    except ExportError as exc:
        print(render(exc.report(), args.format), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
