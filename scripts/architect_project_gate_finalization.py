"""Runtime-owned Project Gate execution capture and atomic publication."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from jsonschema import Draft202012Validator

ARTIFACT_FILENAME = "architect-project-gate.json"
RECEIPT_FILENAME = "architect-project-gate-receipt.json"
RECEIPT_SCHEMA_ID = "ev4-architect-project-gate-finalization-receipt@1.0.0"
RECEIPT_SCHEMA_PATH = "schemas/ev4-architect-project-gate-finalization-receipt.v1.schema.json"


class _ProjectGateExecution(dict[str, Any]):
    """Public summary mapping carrying one private terminal execution value."""

    def __init__(
        self,
        public_summary: dict[str, Any],
        *,
        runtime_issued_payload: dict[str, Any],
        project_gate_artifact: dict[str, Any],
        hashes: dict[str, str],
        validation_result: dict[str, Any],
        functional_eligibility: dict[str, Any],
        producer_provenance: Any,
    ) -> None:
        super().__init__(public_summary)
        self.runtime_issued_payload = runtime_issued_payload
        self.project_gate_artifact = project_gate_artifact
        self.hashes = hashes
        self.validation_result = validation_result
        self.functional_eligibility = functional_eligibility
        self.producer_provenance = producer_provenance

    def __deepcopy__(self, memo: dict[int, Any]) -> dict[str, Any]:
        # Public Runtime projections receive only the approved summary mapping.
        return copy.deepcopy(dict(self), memo)


@dataclass(frozen=True)
class ProjectGateFinalizationResult:
    finalization_succeeded: bool
    handoff_allowed: bool
    publication_status: Literal[
        "published_allowed", "published_blocked", "not_published"
    ]
    artifact_path: Path | None
    receipt_path: Path | None
    artifact_sha256: str | None
    receipt_sha256: str | None
    run_id: str | None
    source_kind: str
    synthetic: bool
    diagnostics: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    stage_results: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    run_state: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "finalization_succeeded": self.finalization_succeeded,
            "handoff_allowed": self.handoff_allowed,
            "publication_status": self.publication_status,
            "artifact_path": str(self.artifact_path) if self.artifact_path else None,
            "receipt_path": str(self.receipt_path) if self.receipt_path else None,
            "artifact_sha256": self.artifact_sha256,
            "receipt_sha256": self.receipt_sha256,
            "run_id": self.run_id,
            "source_kind": self.source_kind,
            "synthetic": self.synthetic,
            "diagnostics": [copy.deepcopy(item) for item in self.diagnostics],
            "stage_results": [copy.deepcopy(item) for item in self.stage_results],
            "run_state": copy.deepcopy(self.run_state),
        }


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _bytes_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _diagnostic(
    code: str,
    message: str,
    *,
    path: str | None = None,
    stage_id: str | None = "/project-gate-export",
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "path": path,
        "stage_id": stage_id,
    }


def failed_result(
    *,
    run_id: str | None,
    source_kind: str,
    diagnostics: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    stage_results: tuple[dict[str, Any], ...] = (),
    run_state: dict[str, Any] | None = None,
    artifact_path: Path | None = None,
) -> ProjectGateFinalizationResult:
    return ProjectGateFinalizationResult(
        finalization_succeeded=False,
        handoff_allowed=False,
        publication_status="not_published",
        artifact_path=artifact_path,
        receipt_path=None,
        artifact_sha256=None,
        receipt_sha256=None,
        run_id=run_id,
        source_kind=source_kind,
        synthetic=source_kind != "live_conversation",
        diagnostics=tuple(copy.deepcopy(list(diagnostics))),
        stage_results=tuple(copy.deepcopy(list(stage_results))),
        run_state=copy.deepcopy(run_state),
    )


def evaluate_project_gate_execution(
    output: dict[str, Any],
    state: dict[str, Any],
    root: Path,
    run_context: Any,
    git_provider: Any | None,
    issues: list[dict[str, Any]],
    *,
    producer_provenance: Callable[[Path, Any | None], Any],
    expected_issues: Callable[[Any, str], list[dict[str, Any]]],
    issue_factory: Callable[..., dict[str, Any]],
) -> _ProjectGateExecution | None:
    """Execute the terminal Project Gate transaction and return an explicit value."""

    import importlib

    scripts = root / "scripts"
    import sys

    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    contracts = importlib.import_module("architect_project_gate_exporter.contracts")
    runtime_gate = importlib.import_module("architect_runtime_project_gate")
    eligibility_module = importlib.import_module(
        "architect_project_gate_exporter.eligibility"
    )
    assembler = importlib.import_module("architect_runtime_payload_assembler")
    errors = importlib.import_module("architect_runtime_errors")

    try:
        payload = assembler.assemble_architect_stage_payload(
            run_state=state,
            source_kind=run_context.source_kind,
        )
        validation = runtime_gate.validate_payload(root, payload)
        eligibility = eligibility_module.derive_handoff_eligibility(payload)
        provenance = producer_provenance(root, git_provider)
        export, hashes = contracts.build_export(
            payload,
            provenance,
            state["run_id"],
            "quality_runtime:runtime_issued_payload",
        )
        runtime_gate.validate_contracts(root, export)
        contracts.verify_hashes(export, hashes)
        allowed = export.get("handoff", {}).get("allowed") is True
        if export.get("run_id") != state["run_id"]:
            raise errors.ProjectGateValidationError(
                errors.RuntimeDiagnostic(
                    "RUNTIME_PROJECT_GATE_RUN_MISMATCH",
                    "Generated export belongs to another Run",
                    stage_id="/project-gate-export",
                )
            )
        if run_context.synthetic and allowed:
            raise errors.ProjectGateValidationError(
                errors.RuntimeDiagnostic(
                    "RUNTIME_SYNTHETIC_HANDOFF_ALLOWED",
                    "Synthetic Runtime context produced an allowed real handoff",
                    stage_id="/project-gate-export",
                )
            )
        if (
            not run_context.synthetic
            and eligibility["would_allow"]
            and not allowed
        ):
            raise errors.ProjectGateValidationError(
                errors.RuntimeDiagnostic(
                    "RUNTIME_ELIGIBLE_LIVE_HANDOFF_BLOCKED",
                    "Eligible live Runtime context did not produce an allowed handoff",
                    stage_id="/project-gate-export",
                )
            )
    except errors.ArchitectRuntimeExpectedError as exc:
        issues.extend(expected_issues(exc, "/project-gate-export"))
        return None
    except contracts.ExportError as exc:
        issues.append(
            issue_factory(exc.code, exc.reason, "/project-gate-export")
        )
        return None

    summary = {
        "canonical_payload_valid": True,
        "legacy_export_substituted": False,
        "source_payload_digest": "sha256:" + hashes["payload_hash"],
        "export_digest": "sha256:" + hashes["export_hash"],
        "validator_identity": "ev4-producer-gate-export-validator@1.0.0",
        "validation_result": validation["status"],
        "export_id": export["export_id"],
        "functional_eligibility": eligibility,
        "execution_context": {
            "source_kind": run_context.source_kind,
            "synthetic": run_context.synthetic,
        },
        "handoff_allowed": allowed,
    }
    return _ProjectGateExecution(
        summary,
        runtime_issued_payload=payload,
        project_gate_artifact=export,
        hashes=hashes,
        validation_result=validation,
        functional_eligibility=eligibility,
        producer_provenance=provenance,
    )


def _stage_temp_file(directory: Path, filename: str, data: bytes) -> Path:
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{filename}.",
        suffix=".tmp",
        dir=directory,
    )
    path = Path(raw_path)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def _publish_no_replace(staged: Path, destination: Path) -> None:
    os.link(staged, destination)
    staged.unlink()


def _verify_committed_bytes(path: Path, expected: bytes) -> str:
    observed = path.read_bytes()
    if observed != expected:
        raise OSError(f"Committed bytes differ for {path.name}")
    return _bytes_digest(observed)


def _remove_owned_artifact(path: Path, expected: bytes) -> bool:
    try:
        if path.is_file() and path.read_bytes() == expected:
            path.unlink()
            return True
    except OSError:
        return False
    return not path.exists()


def _validate_receipt(root: Path, receipt: dict[str, Any]) -> None:
    schema_path = root / RECEIPT_SCHEMA_PATH
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        first = errors[0]
        location = "/".join(map(str, first.absolute_path)) or "$"
        raise ValueError(f"{location}: {first.message}")


def publish_project_gate_execution(
    execution: _ProjectGateExecution,
    *,
    stage_outputs: list[dict[str, Any]],
    stage_results: tuple[dict[str, Any], ...],
    run_state: dict[str, Any],
    run_context: Any,
    repository_root: Path,
    output_directory: Path,
    runtime_interface_id: str,
) -> ProjectGateFinalizationResult:
    """Validate and atomically publish the artifact and deterministic receipt."""

    root = Path(repository_root).resolve()
    destination_root = Path(output_directory).expanduser().resolve()
    run_id = str(run_state.get("run_id") or "")
    source_kind = str(run_context.source_kind)
    artifact_path = destination_root / ARTIFACT_FILENAME
    receipt_path = destination_root / RECEIPT_FILENAME
    artifact_bytes: bytes | None = None
    staged_artifact: Path | None = None
    staged_receipt: Path | None = None

    try:
        if not run_id:
            raise ValueError("Runtime-derived run_id is missing.")
        if len(stage_outputs) != 12:
            raise ValueError("Project Gate finalization requires exactly twelve Stage Outputs.")
        if stage_outputs[-1].get("stage_id") != "/project-gate-export":
            raise ValueError("Terminal Stage Output identity is invalid.")
        try:
            destination_root.relative_to(root)
        except ValueError:
            pass
        else:
            raise ValueError(
                "Project Gate publication directory must be outside the Architect repository."
            )
        destination_root.mkdir(parents=True, exist_ok=True)
        if artifact_path.exists() or receipt_path.exists():
            raise FileExistsError(
                "Project Gate finalization destinations must not already exist."
            )

        import importlib

        contracts = importlib.import_module("architect_project_gate_exporter.contracts")
        runtime_gate = importlib.import_module("architect_runtime_project_gate")
        artifact = execution.project_gate_artifact
        contracts.validate_contracts(root, artifact)
        contracts.verify_hashes(artifact, execution.hashes)
        runtime_gate.validate_contracts(root, artifact)

        artifact_bytes = _canonical_bytes(artifact)
        artifact_sha = _bytes_digest(artifact_bytes)
        producer = execution.producer_provenance
        handoff = artifact.get("handoff", {})
        publication_status = (
            "published_allowed"
            if handoff.get("allowed") is True
            else "published_blocked"
        )
        receipt = {
            "schema_id": RECEIPT_SCHEMA_ID,
            "schema_version": "1.0.0",
            "runtime_interface_id": runtime_interface_id,
            "run_id": run_id,
            "source_kind": source_kind,
            "synthetic": bool(run_context.synthetic),
            "producer": {
                "repository": producer.repository,
                "ref": producer.ref,
                "commit_sha": producer.commit_sha,
            },
            "stage_history": {
                "stage_count": len(stage_outputs),
                "terminal_stage": "/project-gate-export",
                "canonical_sha256": _canonical_digest(stage_outputs),
            },
            "payload": {
                "schema_id": "ev4-architect-stage-payload@1.0.0",
                "canonical_sha256": execution.hashes["payload_hash"],
                "runtime_issued": True,
            },
            "artifact": {
                "filename": ARTIFACT_FILENAME,
                "relative_path": ARTIFACT_FILENAME,
                "canonical_sha256": artifact_sha,
                "schema_valid": True,
                "semantic_valid": execution.validation_result.get("status")
                in {"valid", "insufficient_evidence"},
                "hashes_verified": True,
                "committed": True,
            },
            "handoff": {
                "allowed": handoff.get("allowed") is True,
                "status": str(handoff.get("status")),
                "functional_eligibility_would_allow": bool(
                    execution.functional_eligibility.get("would_allow")
                ),
                "blocking_diagnostics": copy.deepcopy(
                    handoff.get("blocking_diagnostics", [])
                ),
            },
            "finalization": {
                "status": publication_status,
                "completed": True,
                "receipt_filename": RECEIPT_FILENAME,
                "receipt_relative_path": RECEIPT_FILENAME,
            },
        }
        _validate_receipt(root, receipt)
        receipt_bytes = _canonical_bytes(receipt)

        staged_artifact = _stage_temp_file(
            destination_root, ARTIFACT_FILENAME, artifact_bytes
        )
        staged_receipt = _stage_temp_file(
            destination_root, RECEIPT_FILENAME, receipt_bytes
        )
        _publish_no_replace(staged_artifact, artifact_path)
        staged_artifact = None
        observed_artifact_sha = _verify_committed_bytes(
            artifact_path, artifact_bytes
        )
        if observed_artifact_sha != artifact_sha:
            raise OSError("Artifact digest changed after publication.")
        try:
            _publish_no_replace(staged_receipt, receipt_path)
            staged_receipt = None
            receipt_sha = _verify_committed_bytes(receipt_path, receipt_bytes)
        except Exception:
            _remove_owned_artifact(artifact_path, artifact_bytes)
            raise

        return ProjectGateFinalizationResult(
            finalization_succeeded=True,
            handoff_allowed=handoff.get("allowed") is True,
            publication_status=publication_status,
            artifact_path=artifact_path,
            receipt_path=receipt_path,
            artifact_sha256=artifact_sha,
            receipt_sha256=receipt_sha,
            run_id=run_id,
            source_kind=source_kind,
            synthetic=bool(run_context.synthetic),
            diagnostics=(),
            stage_results=tuple(copy.deepcopy(list(stage_results))),
            run_state=copy.deepcopy(run_state),
        )
    except Exception as exc:
        if staged_artifact is not None:
            staged_artifact.unlink(missing_ok=True)
        if staged_receipt is not None:
            staged_receipt.unlink(missing_ok=True)
        if receipt_path.exists():
            try:
                receipt_path.unlink()
            except OSError:
                pass
        if artifact_bytes is not None and artifact_path.exists():
            _remove_owned_artifact(artifact_path, artifact_bytes)
        return failed_result(
            run_id=run_id or None,
            source_kind=source_kind,
            diagnostics=[
                _diagnostic(
                    "RUNTIME_PROJECT_GATE_FINALIZATION_FAILED",
                    f"{type(exc).__name__}: {exc}",
                    path="output_directory",
                )
            ],
            stage_results=stage_results,
            run_state=run_state,
            artifact_path=artifact_path if artifact_path.exists() else None,
        )


__all__ = [
    "ProjectGateFinalizationResult",
    "failed_result",
    "publish_project_gate_execution",
]
