from __future__ import annotations

"""ARCH-02 bounded repair for the Architect Project Gate exporter.

Every semantic, contract, hash, Git-provenance, and ancestry check capable of
invalidating acceptance completes before canonical publication. Successful
descriptor-derived atomic no-clobber publication is the operational commit
point. Receipt, observation, and cleanup degradation after that point is
warning-bearing success and never destructive rollback or false artifact
failure.
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable

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
    return exc.code if isinstance(exc, ExportError) else type(exc).__name__


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
    warnings: Iterable[str],
    *,
    receipt_emitted: bool,
) -> ExportOperationResult:
    collected = list(warnings)
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
        cleanup_warnings=collected,
        result_status=_result_status(collected),
        artifact_committed=True,
        receipt_emitted=receipt_emitted,
        cleanup_complete=not any(_is_cleanup_warning(item) for item in collected),
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


def _destination_present(transaction: OutputTransaction, stage: str) -> bool:
    try:
        return transaction.destination_identity(stage) is not None
    except ExportError:
        return False


def _publish_commit(transaction: OutputTransaction) -> list[str]:
    """Publish once; the successful no-clobber link is operational commit."""

    try:
        transaction.publish()
    except Exception as exc:
        if not transaction.published:
            raise
        # The link already made a fully prevalidated artifact operational.
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
    destination_present = False
    try:
        _publish_commit(transaction)
    except Exception as exc:
        precommit_error = _normalize_precommit_error(exc)
        destination_present = _destination_present(transaction, precommit_error.stage)
        try:
            transaction.rollback()
        except Exception as rollback_exc:  # pragma: no cover - defensive only
            precommit_error = ExportError(
                "ARCH_EXPORT_ROLLBACK_FAILED",
                "precommit_cleanup",
                f"Nondestructive pre-commit cleanup failed: {type(rollback_exc).__name__}.",
                "operator",
                output_committed=False,
                destination_present=destination_present,
            )
    finally:
        close_warnings = transaction.close()

    if precommit_error is not None:
        precommit_error.output_written = False
        precommit_error.output_committed = False
        precommit_error.destination_present = destination_present
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
    precommit_destination_present = False
    receipt_emitted = False

    try:
        # Candidate acceptance is complete before canonical publication.
        staged_bytes = transaction.read_candidate("staged_candidate_ancestry")
        staged = _strict_json_bytes(staged_bytes, "staged_candidate_validation")
        validate_contracts(root, staged)
        verify_hashes(staged, hashes)

        prepublish_git = provenance_provider(
            root, payload_path, output_path, transaction.allowed_paths()
        )
        _assert_same_provenance(initial_git, prepublish_git, "prepublication_provenance")
        transaction.ancestry.verify("prepublication_ancestry")

        # Repeat the mutable repository/worktree proof immediately before the
        # atomic boundary. This is still pre-commit, not post-publication proof.
        commit_git = provenance_provider(
            root, payload_path, output_path, transaction.allowed_paths()
        )
        _assert_same_provenance(initial_git, commit_git, "operational_commit_provenance")
        transaction.ancestry.verify("operational_commit_ancestry")

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

        # Receipt is auxiliary post-commit reporting. It remains inside the
        # cooperating lock so another exporter cannot interleave with the
        # historical acknowledgment, but failure is warning-bearing success.
        if receipt_emitter is not None:
            emitted_result = replace(result, receipt_emitted=True)
            try:
                receipt_emitter(emitted_result)
            except Exception as exc:
                _append_once(transaction.cleanup_warnings, _receipt_warning(exc))
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
                receipt_emitted = True
                result = emitted_result
    except Exception as exc:
        if transaction.published:
            transaction.committed = True
            _append_once(transaction.cleanup_warnings, _postcommit_warning(exc))
            result = _operation_result(
                export,
                hashes,
                initial_git,
                root,
                output_path,
                transaction.cleanup_warnings,
                receipt_emitted=receipt_emitted,
            )
        else:
            precommit_error = _normalize_precommit_error(exc)
            precommit_destination_present = _destination_present(
                transaction, precommit_error.stage
            )
            try:
                transaction.rollback()
            except Exception as rollback_exc:
                precommit_error = ExportError(
                    "ARCH_EXPORT_ROLLBACK_FAILED",
                    "precommit_cleanup",
                    f"Nondestructive pre-commit cleanup failed: {type(rollback_exc).__name__}.",
                    "operator",
                    output_committed=False,
                    destination_present=precommit_destination_present,
                )
    finally:
        close_warnings = transaction.close()

    if precommit_error is not None:
        precommit_error.output_written = False
        precommit_error.output_committed = False
        precommit_error.destination_present = precommit_destination_present
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
    return _operation_result(
        export,
        hashes,
        initial_git,
        root,
        output_path,
        close_warnings,
        receipt_emitted=receipt_emitted,
    )


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
