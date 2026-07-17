from __future__ import annotations

"""ARCH-02 bounded repair for the Architect Project Gate exporter.

This module preserves the ARCH-01 contract surface while moving every
semantic, contract, hash, provenance, and ancestry check that can invalidate
acceptance before the atomic no-clobber publication boundary. A successful
publication is the operational commit point. Later receipt, observation, or
cleanup degradation is reported as a warning and never retroactively turns a
valid committed artifact into a failed export.
"""

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable
import argparse
import json
import os
import sys

from . import runner as _legacy

# Preserve the complete ARCH-01 public/test surface, including underscore
# helpers used by the existing adversarial regression suite.
globals().update(
    {name: value for name, value in vars(_legacy).items() if not name.startswith("__")}
)


@dataclass(frozen=True)
class ExportOperationResult(ExportResult):
    """Explicit operator result for the ARCH-02 commit-boundary contract."""

    result_status: str = "SUCCESS"
    artifact_committed: bool = True
    receipt_emitted: bool = False
    cleanup_complete: bool = True


def _append_once(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)


def _diagnostic_name(exc: BaseException) -> str:
    if isinstance(exc, ExportError):
        return exc.code
    return type(exc).__name__


def _postcommit_warning(exc: BaseException) -> str:
    return f"ARCH_EXPORT_POST_COMMIT_OBSERVATION_WARNING:{_diagnostic_name(exc)}"


def _receipt_warning(exc: BaseException) -> str:
    return f"ARCH_EXPORT_RECEIPT_EMIT_FAILED:{type(exc).__name__}"


def _is_receipt_warning(warning: str) -> bool:
    return warning.startswith("ARCH_EXPORT_RECEIPT_EMIT_FAILED:")


def _is_cleanup_warning(warning: str) -> bool:
    return warning.startswith(
        (
            "ARCH_EXPORT_CANDIDATE_",
            "ARCH_EXPORT_OUTPUT_DESCRIPTOR_CLOSE_FAILED:",
            "ARCH_EXPORT_LOCK_",
            "ARCH_EXPORT_ANCESTRY_",
        )
    )


def _result_status(warnings: Iterable[str]) -> str:
    values = list(warnings)
    receipt = any(_is_receipt_warning(item) for item in values)
    other = any(not _is_receipt_warning(item) for item in values)
    if receipt and other:
        return "SUCCESS_WITH_WARNINGS"
    if receipt:
        return "SUCCESS_WITH_RECEIPT_WARNING"
    if other:
        return "SUCCESS_WITH_CLEANUP_WARNING"
    return "SUCCESS"


def _operation_result(
    export: dict[str, Any],
    hashes: dict[str, str],
    initial_git: GitProvenance,
    root: Path,
    output_path: Path,
    cleanup_warnings: Iterable[str],
    *,
    receipt_emitted: bool,
) -> ExportOperationResult:
    warnings = list(cleanup_warnings)
    return ExportOperationResult(
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
        cleanup_warnings=warnings,
        result_status=_result_status(warnings),
        artifact_committed=True,
        receipt_emitted=receipt_emitted,
        cleanup_complete=not any(_is_cleanup_warning(item) for item in warnings),
    )


def _normalize_precommit_error(exc: BaseException) -> ExportError:
    if isinstance(exc, ExportError):
        return exc
    return ExportError(
        "ARCH_EXPORT_FILESYSTEM_RACE",
        "output_transaction",
        f"Filesystem operation failed safely: {type(exc).__name__}.",
        "operator",
    )


def _publish_commit(transaction: OutputTransaction) -> list[str]:
    """Publish with an unambiguous atomic operational commit boundary.

    Before ``transaction.published`` becomes true, an exception is a normal
    pre-commit failure. Once the descriptor-derived no-clobber link succeeds,
    the artifact was already fully validated and is historically committed;
    any later observation failure is a warning, not rollback.
    """

    try:
        transaction.publish()
    except Exception as exc:
        if not transaction.published:
            raise
        transaction.committed = True
        _append_once(transaction.cleanup_warnings, _postcommit_warning(exc))
    else:
        transaction.committed = True
    return list(transaction.cleanup_warnings)


def atomic_write(
    path: Path,
    value: Any,
    overwrite: bool,
    root: Path | None = None,
) -> list[str]:
    transaction = OutputTransaction.stage(path, value, overwrite, root=root)
    precommit_error: ExportError | None = None
    try:
        _publish_commit(transaction)
    except Exception as exc:
        precommit_error = _normalize_precommit_error(exc)
        try:
            transaction.rollback()
        except Exception as rollback_exc:  # pragma: no cover - defensive only
            precommit_error = ExportError(
                "ARCH_EXPORT_ROLLBACK_FAILED",
                "precommit_cleanup",
                f"Nondestructive pre-commit cleanup failed: {type(rollback_exc).__name__}.",
                "operator",
                output_committed=False,
                destination_present=False,
            )
    finally:
        close_warnings = transaction.close()

    if precommit_error is not None:
        precommit_error.output_written = False
        precommit_error.output_committed = False
        precommit_error.destination_present = (
            transaction.destination_identity(precommit_error.stage) is not None
        )
        precommit_error.cleanup_warnings = list(close_warnings)
        raise precommit_error
    return list(close_warnings)


def run_export(
    root: Path,
    payload_path: Path,
    output_path: Path,
    run_id: str,
    overwrite: bool = False,
    provenance_provider: Callable[
        [Path, Path, Path, Iterable[Path]], GitProvenance
    ] = inspect_repository,
    receipt_emitter: Callable[[ExportOperationResult], None] | None = None,
) -> ExportOperationResult:
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

    try:
        transaction = OutputTransaction.stage(output_path, export, overwrite, root=root)
    except ExportError:
        raise
    except OSError as exc:  # pragma: no cover - final containment guard
        raise ExportError(
            "ARCH_EXPORT_OUTPUT_PREFLIGHT_FAILED",
            "output_preflight",
            f"Output preflight failed: {type(exc).__name__}.",
            "operator",
        ) from exc

    result: ExportOperationResult | None = None
    precommit_error: ExportError | None = None
    try:
        # Every acceptance-invalidating check completes before publication.
        staged_bytes = transaction.read_candidate("staged_candidate_ancestry")
        staged = _strict_json_bytes(staged_bytes, "staged_candidate_validation")
        validate_contracts(root, staged)
        verify_hashes(staged, hashes)

        prepublish_git = provenance_provider(
            root, payload_path, output_path, transaction.allowed_paths()
        )
        _assert_same_provenance(initial_git, prepublish_git, "prepublication_provenance")
        transaction.ancestry.verify("prepublication_ancestry")

        # Successful no-clobber publication is the operational commit point.
        _publish_commit(transaction)
        result = _operation_result(
            export,
            hashes,
            initial_git,
            root,
            output_path,
            transaction.cleanup_warnings,
            receipt_emitted=False,
        )
    except Exception as exc:
        if transaction.published:
            # The artifact was already valid and atomically committed. Do not
            # misreport it as a failed/rolled-back export.
            transaction.committed = True
            _append_once(transaction.cleanup_warnings, _postcommit_warning(exc))
            result = _operation_result(
                export,
                hashes,
                initial_git,
                root,
                output_path,
                transaction.cleanup_warnings,
                receipt_emitted=False,
            )
        else:
            precommit_error = _normalize_precommit_error(exc)
            try:
                transaction.rollback()
            except Exception as rollback_exc:
                precommit_error = ExportError(
                    "ARCH_EXPORT_ROLLBACK_FAILED",
                    "precommit_cleanup",
                    f"Nondestructive pre-commit cleanup failed: {type(rollback_exc).__name__}.",
                    "operator",
                    output_committed=False,
                    destination_present=False,
                )
    finally:
        close_warnings = transaction.close()

    if precommit_error is not None:
        try:
            current_identity = transaction.destination_identity(precommit_error.stage)
        except ExportError:
            current_identity = None
        precommit_error.output_written = False
        precommit_error.output_committed = False
        precommit_error.destination_present = current_identity is not None
        precommit_error.cleanup_warnings = list(close_warnings)
        raise precommit_error

    if result is None:  # pragma: no cover - defensive only
        raise ExportError(
            "ARCH_EXPORT_RESULT_MISSING",
            "operational_commit",
            "Exporter completed without an operational result.",
            "repository_owner",
            output_committed=transaction.committed,
            destination_present=transaction.published,
        )

    # Close/release degradation is post-commit and reflected in the final result.
    result = _operation_result(
        export,
        hashes,
        initial_git,
        root,
        output_path,
        close_warnings,
        receipt_emitted=False,
    )

    # Receipt emission is auxiliary reporting after operational commit and cleanup.
    if receipt_emitter is not None:
        emitted_result = replace(result, receipt_emitted=True)
        try:
            receipt_emitter(emitted_result)
        except Exception as exc:
            warnings = list(result.cleanup_warnings)
            _append_once(warnings, _receipt_warning(exc))
            result = _operation_result(
                export,
                hashes,
                initial_git,
                root,
                output_path,
                warnings,
                receipt_emitted=False,
            )
        else:
            result = emitted_result
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

    def emit_receipt(result: ExportOperationResult) -> None:
        print(render(asdict(result), args.format), flush=True)

    try:
        result = run_export(
            root,
            payload,
            output,
            args.run_id,
            args.overwrite,
            receipt_emitter=emit_receipt,
        )
        if result.cleanup_warnings:
            update = {
                "receipt_update": "post_commit_warning",
                "result_status": result.result_status,
                "artifact_committed": result.artifact_committed,
                "receipt_emitted": result.receipt_emitted,
                "cleanup_complete": result.cleanup_complete,
                "cleanup_warnings": result.cleanup_warnings,
            }
            try:
                print(render(update, args.format), file=sys.stderr, flush=True)
            except Exception:
                # The artifact is already committed. Reporting degradation must
                # not become a false exporter failure.
                pass
        return 0 if result.handoff_allowed else 2
    except ExportError as exc:
        print(render(exc.report(), args.format), file=sys.stderr, flush=True)
        return exc.exit_code
