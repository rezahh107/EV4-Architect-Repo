from __future__ import annotations

"""ARCH-02 bounded repair for the Architect Project Gate exporter.

Every semantic, contract, hash, Git-provenance, and ancestry check capable of
invalidating acceptance completes before canonical publication. Descriptor-
derived atomic no-clobber publication remains the historical commit point.
Post-link acceptance proof is separate: if canonical repository ancestry,
current Git provenance, or destination ownership cannot be proven, the artifact
remains committed but handoff is blocked without pathname-based rollback.
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Iterable

from . import runner as _legacy

# Preserve the complete ARCH-01 public/test surface, including underscore
# helpers used by the existing adversarial regression suite.
globals().update(
    {name: value for name, value in vars(_legacy).items() if not name.startswith("__")}
)


@dataclass(frozen=True)
class PublishOutcome:
    """Historical commit outcome before current-revision handoff acceptance."""

    warnings: tuple[str, ...] = ()
    acceptance_blockers: tuple[str, ...] = ()
    canonical_destination_present: bool = True
    committed_output_location: str = "canonical_repository_destination"


@dataclass(frozen=True)
class ExportOperationResult(ExportResult):
    """Explicit operator result for commit, location, and revision acceptance."""

    result_status: str = "SUCCESS"
    artifact_committed: bool = True
    receipt_emitted: bool = False
    cleanup_complete: bool = True
    current_revision_accepted: bool = True
    canonical_destination_present: bool = True
    committed_output_location: str = "canonical_repository_destination"
    acceptance_blockers: list[str] = field(default_factory=list)


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _diagnostic_name(exc: BaseException) -> str:
    return exc.code if isinstance(exc, ExportError) else type(exc).__name__


def _postcommit_warning(exc: BaseException) -> str:
    return f"ARCH_EXPORT_POST_COMMIT_OBSERVATION_WARNING:{_diagnostic_name(exc)}"


def _receipt_warning(exc: BaseException) -> str:
    return f"ARCH_EXPORT_RECEIPT_EMIT_FAILED:{type(exc).__name__}"


def _acceptance_blocker(prefix: str, exc: BaseException) -> str:
    return f"{prefix}:{_diagnostic_name(exc)}"


def _is_receipt_warning(warning: str) -> bool:
    return warning.startswith("ARCH_EXPORT_RECEIPT_EMIT_FAILED:")


def _is_cleanup_warning(warning: str) -> bool:
    return warning.startswith(
        (
            "ARCH_EXPORT_CANDIDATE_",
            "ARCH_EXPORT_OUTPUT_DESCRIPTOR_CLOSE_FAILED:",
            "ARCH_EXPORT_OUTPUT_LOCK_RELEASE_FAILED:",
            "ARCH_EXPORT_LOCK_",
            "ARCH_EXPORT_ANCESTRY_",
        )
    )


def _result_status(
    warnings: Iterable[str], acceptance_blockers: Iterable[str] = ()
) -> str:
    values = list(warnings)
    blockers = list(acceptance_blockers)
    if blockers:
        return (
            "COMMITTED_HANDOFF_BLOCKED_WITH_WARNINGS"
            if values
            else "COMMITTED_HANDOFF_BLOCKED"
        )
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
    acceptance_blockers: Iterable[str] = (),
    canonical_destination_present: bool = True,
    committed_output_location: str = "canonical_repository_destination",
    current_revision_accepted: bool = True,
) -> ExportOperationResult:
    collected = list(warnings)
    blockers = list(acceptance_blockers)
    accepted = current_revision_accepted and not blockers
    canonical_path = (
        str(output_path.relative_to(root)).replace(os.sep, "/")
        if canonical_destination_present
        else ""
    )
    return ExportOperationResult(
        status=export["handoff"]["status"],
        output_path=canonical_path,
        export_id=export["export_id"],
        payload_hash=hashes["payload_hash"],
        bundle_hash=hashes["bundle_hash"],
        export_hash=hashes["export_hash"],
        producer_commit=initial_git.commit_sha,
        handoff_target=TARGET,
        handoff_allowed=(
            export["handoff"]["allowed"]
            and accepted
            and canonical_destination_present
        ),
        output_written=False,
        output_committed=True,
        destination_present=canonical_destination_present,
        concurrent_destination_preserved=False,
        backup_retained=False,
        backup_path=None,
        receipt_scope="historical_commit",
        current_destination_claim=False,
        cleanup_warnings=collected,
        result_status=_result_status(collected, blockers),
        artifact_committed=True,
        receipt_emitted=receipt_emitted,
        cleanup_complete=not any(_is_cleanup_warning(item) for item in collected),
        current_revision_accepted=accepted,
        canonical_destination_present=canonical_destination_present,
        committed_output_location=committed_output_location,
        acceptance_blockers=blockers,
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


def _location_for_unproven_publication(exc: BaseException) -> str:
    diagnostic = _diagnostic_name(exc)
    if diagnostic.startswith("ARCH_EXPORT_OUTPUT_ANCESTRY_"):
        return "bound_parent_outside_canonical_ancestry"
    return "canonical_destination_unverified"


def _publication_still_canonical(transaction: OutputTransaction) -> bool:
    if transaction.published_descriptor is None:
        return False
    try:
        transaction.verify_owned("postcommit_exception_acceptance")
    except Exception:
        return False
    return True


def _publish_commit(transaction: OutputTransaction) -> PublishOutcome:
    """Publish once and separate historical commit from handoff acceptance."""

    warnings = list(transaction.cleanup_warnings)
    blockers: list[str] = []
    canonical_destination_present = True
    committed_output_location = "canonical_repository_destination"
    try:
        transaction.publish()
    except Exception as exc:
        if not transaction.published:
            raise
        transaction.committed = True
        _append_once(transaction.cleanup_warnings, _postcommit_warning(exc))
        warnings = list(transaction.cleanup_warnings)

        # A failure after the link may still be an auxiliary observation failure
        # if ancestry, destination identity, and bytes can be re-proved.
        if not _publication_still_canonical(transaction):
            _append_once(
                blockers,
                _acceptance_blocker(
                    "ARCH_EXPORT_POST_COMMIT_PUBLICATION_BLOCKED", exc
                ),
            )
            canonical_destination_present = False
            committed_output_location = _location_for_unproven_publication(exc)
    else:
        transaction.committed = True
        warnings = list(transaction.cleanup_warnings)

    return PublishOutcome(
        warnings=tuple(warnings),
        acceptance_blockers=tuple(blockers),
        canonical_destination_present=canonical_destination_present,
        committed_output_location=committed_output_location,
    )


def _post_link_acceptance(
    transaction: OutputTransaction,
    initial_git: GitProvenance,
    root: Path,
    payload_path: Path,
    output_path: Path,
    provenance_provider: Callable[
        [Path, Path, Path, Iterable[Path]], GitProvenance
    ],
    publication: PublishOutcome,
) -> tuple[list[str], bool, str, bool]:
    """Prove current-revision and canonical destination acceptance after link."""

    blockers = list(publication.acceptance_blockers)
    canonical_destination_present = publication.canonical_destination_present
    committed_output_location = publication.committed_output_location
    current_revision_accepted = not blockers

    try:
        post_link_git = provenance_provider(
            root, payload_path, output_path, transaction.allowed_paths()
        )
        _assert_same_provenance(
            initial_git, post_link_git, "postpublication_provenance"
        )
    except Exception as exc:
        _append_once(
            blockers,
            _acceptance_blocker(
                "ARCH_EXPORT_POST_COMMIT_PROVENANCE_BLOCKED", exc
            ),
        )
        current_revision_accepted = False

    try:
        transaction.verify_owned("postpublication_acceptance")
    except Exception as exc:
        _append_once(
            blockers,
            _acceptance_blocker(
                "ARCH_EXPORT_POST_COMMIT_DESTINATION_BLOCKED", exc
            ),
        )
        canonical_destination_present = False
        committed_output_location = _location_for_unproven_publication(exc)
        current_revision_accepted = False

    return (
        blockers,
        canonical_destination_present,
        committed_output_location,
        current_revision_accepted,
    )


def atomic_write(
    path: Path,
    value: Any,
    overwrite: bool,
    root: Path | None = None,
) -> list[str]:
    transaction = OutputTransaction.stage(path, value, overwrite, root=root)
    precommit_error: ExportError | None = None
    committed_blocker: PublishOutcome | None = None
    destination_present = False
    try:
        publication = _publish_commit(transaction)
        if publication.acceptance_blockers:
            committed_blocker = publication
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
    if committed_blocker is not None:
        raise ExportError(
            "ARCH_EXPORT_COMMITTED_DESTINATION_UNVERIFIED",
            "post_commit_acceptance",
            "The artifact was committed but its canonical repository destination could not be proven.",
            "operator",
            output_committed=True,
            destination_present=committed_blocker.canonical_destination_present,
            cleanup_warnings=list(close_warnings),
        )
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
    export, hashes = build_export(
        payload, initial_git, run_id, _input_ref(root, payload_path)
    )
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
        _assert_same_provenance(
            initial_git, prepublish_git, "prepublication_provenance"
        )
        transaction.ancestry.verify("prepublication_ancestry")

        commit_git = provenance_provider(
            root, payload_path, output_path, transaction.allowed_paths()
        )
        _assert_same_provenance(
            initial_git, commit_git, "operational_commit_provenance"
        )
        transaction.ancestry.verify("operational_commit_ancestry")

        # The link is the historical commit point. Handoff acceptance is then
        # re-proved against current Git provenance and canonical ancestry.
        publication = _publish_commit(transaction)
        (
            acceptance_blockers,
            canonical_destination_present,
            committed_output_location,
            current_revision_accepted,
        ) = _post_link_acceptance(
            transaction,
            initial_git,
            root,
            payload_path,
            output_path,
            provenance_provider,
            publication,
        )
        result = _operation_result(
            export,
            hashes,
            initial_git,
            root,
            output_path,
            transaction.cleanup_warnings,
            receipt_emitted=False,
            acceptance_blockers=acceptance_blockers,
            canonical_destination_present=canonical_destination_present,
            committed_output_location=committed_output_location,
            current_revision_accepted=current_revision_accepted,
        )

        # Receipt remains inside the cooperating lock. A receipt failure is
        # auxiliary and cannot weaken an existing acceptance blocker.
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
                    acceptance_blockers=result.acceptance_blockers,
                    canonical_destination_present=result.canonical_destination_present,
                    committed_output_location=result.committed_output_location,
                    current_revision_accepted=result.current_revision_accepted,
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
                acceptance_blockers=[
                    _acceptance_blocker(
                        "ARCH_EXPORT_POST_COMMIT_ACCEPTANCE_BLOCKED", exc
                    )
                ],
                canonical_destination_present=False,
                committed_output_location=_location_for_unproven_publication(exc),
                current_revision_accepted=False,
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

    # Close/release degradation is post-commit and reflected without losing
    # canonical-location or current-revision acceptance state.
    return _operation_result(
        export,
        hashes,
        initial_git,
        root,
        output_path,
        close_warnings,
        receipt_emitted=receipt_emitted,
        acceptance_blockers=result.acceptance_blockers,
        canonical_destination_present=result.canonical_destination_present,
        committed_output_location=result.committed_output_location,
        current_revision_accepted=result.current_revision_accepted,
    )


def render(data: dict[str, Any], mode: str) -> str:
    if mode == "json":
        return json.dumps(
            data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
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
    parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help=argparse.SUPPRESS
    )
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
        if result.cleanup_warnings or result.acceptance_blockers:
            update = {
                "receipt_update": "post_commit_state",
                "result_status": result.result_status,
                "artifact_committed": result.artifact_committed,
                "receipt_emitted": result.receipt_emitted,
                "cleanup_complete": result.cleanup_complete,
                "current_revision_accepted": result.current_revision_accepted,
                "canonical_destination_present": result.canonical_destination_present,
                "committed_output_location": result.committed_output_location,
                "cleanup_warnings": result.cleanup_warnings,
                "acceptance_blockers": result.acceptance_blockers,
            }
            try:
                print(render(update, args.format), file=sys.stderr, flush=True)
            except Exception:
                # The artifact is already committed. Reporting degradation must
                # not become destructive rollback or false current acceptance.
                pass
        return 0 if result.handoff_allowed else 2
    except ExportError as exc:
        print(render(exc.report(), args.format), file=sys.stderr, flush=True)
        return exc.exit_code
