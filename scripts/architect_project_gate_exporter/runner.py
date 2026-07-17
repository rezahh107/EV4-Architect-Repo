from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Iterable

from . import ancestry as _ancestry_module
from . import base as _base_module
from . import contracts as _contracts_module
from . import locking as _locking_module
from . import transaction as _transaction_module

for _module in (
    _base_module,
    _contracts_module,
    _ancestry_module,
    _locking_module,
    _transaction_module,
):
    globals().update(
        {name: value for name, value in vars(_module).items() if not name.startswith("__")}
    )


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


def atomic_write(
    path: Path,
    value: Any,
    overwrite: bool,
    root: Path | None = None,
) -> list[str]:
    transaction = OutputTransaction.stage(path, value, overwrite, root=root)
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
                destination_present=(
                    transaction.destination_identity("post_write_validation") is not None
                ),
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
    provenance_provider: Callable[
        [Path, Path, Path, Iterable[Path]], GitProvenance
    ] = inspect_repository,
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

    result: ExportResult | None = None
    try:
        staged_bytes = transaction.read_candidate("staged_candidate_ancestry")
        staged = _strict_json_bytes(staged_bytes, "staged_candidate_validation")
        validate_contracts(root, staged)
        verify_hashes(staged, hashes)

        prepublish_git = provenance_provider(
            root, payload_path, output_path, transaction.allowed_paths()
        )
        _assert_same_provenance(initial_git, prepublish_git, "prepublication_provenance")
        transaction.ancestry.verify("prepublication_ancestry")

        transaction.publish()
        owned_bytes = transaction.verify_owned("postpublication_identity_bytes_ancestry")
        reread = _strict_json_bytes(owned_bytes, "postpublication_validation")
        validate_contracts(root, reread)
        verify_hashes(reread, hashes)

        final_git = provenance_provider(
            root, payload_path, output_path, transaction.allowed_paths()
        )
        _assert_same_provenance(initial_git, final_git, "final_provenance")

        final_bytes = transaction.verify_owned("final_destination_verification")
        final_reread = _strict_json_bytes(final_bytes, "final_destination_validation")
        validate_contracts(root, final_reread)
        verify_hashes(final_reread, hashes)

        cleanup_warnings = transaction.commit()
        transaction.verify_owned("success_receipt_boundary")
        result = _historical_result(
            export, hashes, initial_git, root, output_path, cleanup_warnings
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
                    destination_present=(
                        transaction.destination_identity("success_receipt") is not None
                    ),
                ) from exc
    except Exception as exc:
        if not isinstance(exc, ExportError):
            exc = ExportError(
                "ARCH_EXPORT_FILESYSTEM_RACE",
                "output_transaction",
                f"Filesystem operation failed safely: {type(exc).__name__}.",
                "operator",
            )
        try:
            transaction.rollback()
        except Exception as rollback_exc:
            raise ExportError(
                "ARCH_EXPORT_ROLLBACK_FAILED",
                "post_write_validation",
                f"Nondestructive rollback cleanup failed: {type(rollback_exc).__name__}.",
                "operator",
                output_committed=transaction.committed,
                destination_present=(
                    transaction.destination_identity("post_write_validation") is not None
                ),
            ) from exc
        if isinstance(exc, ExportError):
            try:
                current_identity = transaction.destination_identity(exc.stage)
            except ExportError:
                current_identity = None
            exc.output_written = False
            exc.output_committed = transaction.committed
            exc.destination_present = current_identity is not None
            exc.concurrent_destination_preserved = (
                exc.concurrent_destination_preserved
                or (
                    transaction.published_identity is not None
                    and current_identity is not None
                    and current_identity != transaction.published_identity
                )
            )
            exc.cleanup_warnings = list(transaction.cleanup_warnings)
        raise exc
    finally:
        close_warnings = transaction.close()

    if result is None:  # pragma: no cover - defensive only
        raise ExportError(
            "ARCH_EXPORT_RESULT_MISSING",
            "success_receipt",
            "Exporter completed without producing a receipt.",
            "repository_owner",
            output_committed=transaction.committed,
            destination_present=False,
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
