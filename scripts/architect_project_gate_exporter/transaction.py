from __future__ import annotations

import errno
import hashlib
import os
import secrets
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import ExportError, canonical_bytes, inside
from .ancestry import (
    AncestryBinding,
    _file_read_flags,
    _identity_from_stat,
    _output_lock_path,
)
from .locking import OutputLock, _read_all, _write_all

_CANDIDATE_ALLOCATION_ATTEMPTS = 128
_UNNAMED_UNSUPPORTED_ERRNOS = {
    errno.EINVAL,
    errno.EISDIR,
    errno.ENOSYS,
    errno.EOPNOTSUPP,
    getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
    errno.EPERM,
}


def _append_warning(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)


def _candidate_residue_directory_path(root: Path) -> Path:
    key = hashlib.sha256(os.fsencode(str(root.resolve()))).hexdigest()[:16]
    uid = str(os.getuid()) if hasattr(os, "getuid") else "process"
    return root.resolve().parent / f".ev4-architect-candidates-{uid}-{key}"


def _candidate_name(destination_name: str, token: str) -> str:
    return f".{destination_name}.{token}.tmp"


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


def _open_unnamed_candidate(parent_descriptor: int) -> int | None:
    o_tmpfile = getattr(os, "O_TMPFILE", 0)
    if os.name != "posix" or not o_tmpfile:
        return None
    try:
        return os.open(
            ".",
            os.O_RDWR | o_tmpfile | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=parent_descriptor,
        )
    except OSError as exc:
        if exc.errno in _UNNAMED_UNSUPPORTED_ERRNOS:
            return None
        raise ExportError(
            "ARCH_EXPORT_STAGED_CANDIDATE_CREATE_FAILED",
            "atomic_write",
            f"Unnamed staged candidate creation failed: {type(exc).__name__}.",
            "operator",
        ) from exc


def _open_residue_directory(root: Path, parent_descriptor: int) -> tuple[Path, int]:
    path = _candidate_residue_directory_path(root)
    try:
        os.mkdir(path, mode=0o700)
    except FileExistsError:
        pass
    except OSError as exc:
        raise ExportError(
            "ARCH_EXPORT_CANDIDATE_PRIMITIVE_UNSUPPORTED",
            "atomic_write",
            f"Candidate residue directory could not be created safely: {type(exc).__name__}.",
            "operator",
        ) from exc

    try:
        path_stat = os.lstat(path)
    except OSError as exc:
        raise ExportError(
            "ARCH_EXPORT_CANDIDATE_PRIMITIVE_UNSUPPORTED",
            "atomic_write",
            f"Candidate residue directory could not be inspected safely: {type(exc).__name__}.",
            "operator",
        ) from exc
    if not stat.S_ISDIR(path_stat.st_mode) or stat.S_ISLNK(path_stat.st_mode):
        raise ExportError(
            "ARCH_EXPORT_CANDIDATE_PRIMITIVE_UNSUPPORTED",
            "atomic_write",
            "Candidate residue path is not a real directory.",
            "operator",
        )
    if hasattr(os, "getuid") and path_stat.st_uid != os.getuid():
        raise ExportError(
            "ARCH_EXPORT_CANDIDATE_PRIMITIVE_UNSUPPORTED",
            "atomic_write",
            "Candidate residue directory is not owned by the current user.",
            "operator",
        )
    if stat.S_IMODE(path_stat.st_mode) & 0o077:
        raise ExportError(
            "ARCH_EXPORT_CANDIDATE_PRIMITIVE_UNSUPPORTED",
            "atomic_write",
            "Candidate residue directory permissions are not private.",
            "operator",
        )

    try:
        descriptor = os.open(path, _directory_flags())
    except OSError as exc:
        raise ExportError(
            "ARCH_EXPORT_CANDIDATE_PRIMITIVE_UNSUPPORTED",
            "atomic_write",
            f"Candidate residue directory could not be opened safely: {type(exc).__name__}.",
            "operator",
        ) from exc
    try:
        opened = os.fstat(descriptor)
        parent = os.fstat(parent_descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or _identity_from_stat(opened) != _identity_from_stat(path_stat)
            or opened.st_dev != parent.st_dev
        ):
            raise ExportError(
                "ARCH_EXPORT_CANDIDATE_PRIMITIVE_UNSUPPORTED",
                "atomic_write",
                "Candidate residue directory is not safely bound to the output filesystem.",
                "operator",
            )
        return path, descriptor
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


@dataclass
class CandidateOwnership:
    descriptor: int | None
    identity: tuple[int, int]
    residue_path: Path | None
    state: str = "owned"
    residue_reported: bool = False


def _raw_identity(observed: os.stat_result) -> tuple[int, int]:
    """Return identity without relying on the validated conversion helper."""
    return observed.st_dev, observed.st_ino


def _descriptor_identity_for_reporting(descriptor: int) -> tuple[int, int] | None:
    """Best-effort identity used only to classify retained non-destructive residue."""
    try:
        return _raw_identity(os.fstat(descriptor))
    except OSError:
        pass
    try:
        return _raw_identity(os.stat(f"/proc/self/fd/{descriptor}", follow_symlinks=True))
    except (OSError, NotImplementedError, TypeError):
        return None


def _record_residue_path_state(
    residue_path: Path | None,
    expected_identity: tuple[int, int] | None,
    warnings: list[str],
) -> None:
    if residue_path is None:
        return
    try:
        observed = os.lstat(residue_path)
    except FileNotFoundError:
        _append_warning(warnings, "ARCH_EXPORT_CANDIDATE_RESIDUE_STATUS_UNKNOWN:MISSING")
        return
    except OSError as exc:
        _append_warning(
            warnings,
            f"ARCH_EXPORT_CANDIDATE_RESIDUE_STATUS_UNKNOWN:{type(exc).__name__}",
        )
        return
    if expected_identity is None:
        _append_warning(
            warnings,
            "ARCH_EXPORT_CANDIDATE_RESIDUE_STATUS_UNKNOWN:IDENTITY_UNAVAILABLE",
        )
    elif _raw_identity(observed) == expected_identity:
        _append_warning(warnings, "ARCH_EXPORT_CANDIDATE_RESIDUE_RETAINED")
    else:
        _append_warning(warnings, "ARCH_EXPORT_CANDIDATE_CLEANUP_CONFLICT")


def _record_residue_state(candidate: CandidateOwnership, warnings: list[str]) -> None:
    if candidate.residue_path is None or candidate.residue_reported:
        return
    candidate.residue_reported = True
    _record_residue_path_state(candidate.residue_path, candidate.identity, warnings)


def _close_provisional_descriptor(descriptor: int, warnings: list[str]) -> None:
    try:
        os.close(descriptor)
    except OSError as exc:
        _append_warning(
            warnings,
            f"ARCH_EXPORT_CANDIDATE_RELEASE_FAILED:{type(exc).__name__}",
        )


def _candidate_identity_capture_error(
    descriptor: int,
    residue_path: Path | None,
    captured_identity: tuple[int, int] | None,
    cause: Exception,
) -> ExportError:
    warnings: list[str] = []
    reporting_identity = captured_identity
    if reporting_identity is None:
        reporting_identity = _descriptor_identity_for_reporting(descriptor)
    _close_provisional_descriptor(descriptor, warnings)
    _record_residue_path_state(residue_path, reporting_identity, warnings)
    return ExportError(
        "ARCH_EXPORT_CANDIDATE_IDENTITY_CAPTURE_FAILED",
        "atomic_write",
        f"Staged candidate identity capture failed: {type(cause).__name__}.",
        "operator",
        cleanup_warnings=warnings,
    )


def _complete_candidate_ownership(
    descriptor: int,
    residue_path: Path | None,
) -> CandidateOwnership:
    """Promote a just-created descriptor/path pair from provisional to owned."""
    captured_identity: tuple[int, int] | None = None
    try:
        observed = os.fstat(descriptor)
        captured_identity = _raw_identity(observed)
        identity = _identity_from_stat(observed)
        return CandidateOwnership(
            descriptor=descriptor,
            identity=identity,
            residue_path=residue_path,
        )
    except Exception as exc:
        raise _candidate_identity_capture_error(
            descriptor,
            residue_path,
            captured_identity,
            exc,
        ) from exc


def _release_candidate(candidate: CandidateOwnership, warnings: list[str]) -> None:
    if candidate.state != "owned":
        return
    descriptor, candidate.descriptor = candidate.descriptor, None
    candidate.state = "released"
    if descriptor is not None:
        try:
            os.close(descriptor)
        except OSError as exc:
            _append_warning(
                warnings,
                f"ARCH_EXPORT_CANDIDATE_RELEASE_FAILED:{type(exc).__name__}",
            )
    _record_residue_state(candidate, warnings)


def _allocate_candidate(
    root: Path,
    destination_name: str,
    parent_descriptor: int,
) -> CandidateOwnership:
    descriptor = _open_unnamed_candidate(parent_descriptor)
    if descriptor is not None:
        # The returned descriptor is provisional immediately after kernel creation.
        return _complete_candidate_ownership(descriptor, None)

    residue_root, residue_descriptor = _open_residue_directory(root, parent_descriptor)
    try:
        flags = (
            os.O_RDWR
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        for _ in range(_CANDIDATE_ALLOCATION_ATTEMPTS):
            name = _candidate_name(destination_name, secrets.token_hex(16))
            try:
                descriptor = os.open(name, flags, 0o600, dir_fd=residue_descriptor)
            except FileExistsError:
                continue
            except OSError as exc:
                raise ExportError(
                    "ARCH_EXPORT_STAGED_CANDIDATE_CREATE_FAILED",
                    "atomic_write",
                    f"Staged candidate creation failed: {type(exc).__name__}.",
                    "operator",
                ) from exc

            # Record provisional state immediately after successful O_EXCL creation,
            # before fstat, identity conversion, or CandidateOwnership construction.
            residue_path = residue_root / name
            return _complete_candidate_ownership(descriptor, residue_path)
        raise ExportError(
            "ARCH_EXPORT_STAGED_CANDIDATE_CREATE_FAILED",
            "atomic_write",
            "Could not allocate an unpredictable staged candidate name without disturbing existing entries.",
            "operator",
        )
    finally:
        try:
            os.close(residue_descriptor)
        except OSError:
            pass


@dataclass
class OutputTransaction:
    root: Path
    path: Path
    destination_name: str
    candidate: CandidateOwnership
    expected_bytes: bytes
    ancestry: AncestryBinding
    lock: OutputLock
    published_identity: tuple[int, int] | None = None
    published_descriptor: int | None = None
    published: bool = False
    committed: bool = False
    backup: Path | None = None
    cleanup_warnings: list[str] = field(default_factory=list)

    @classmethod
    def stage(
        cls,
        path: Path,
        value: Any,
        overwrite: bool,
        root: Path | None = None,
    ) -> "OutputTransaction":
        path = Path(os.path.abspath(os.fspath(path)))
        root = (root or path.parent).resolve()
        path = inside(root, path)
        ancestry: AncestryBinding | None = None
        lock: OutputLock | None = None
        candidate: CandidateOwnership | None = None
        try:
            ancestry = AncestryBinding.bind(root, path.parent)
            lock = OutputLock(_output_lock_path(path))
            lock.acquire()
            ancestry.verify("output_preflight_ancestry")

            try:
                observed = os.stat(
                    path.name,
                    dir_fd=ancestry.parent.descriptor,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                observed = None
            except OSError as exc:
                raise ExportError(
                    "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED",
                    "output_preflight",
                    f"Output path inspection failed: {type(exc).__name__}.",
                    "operator",
                ) from exc

            destination_present = observed is not None
            if observed is not None and stat.S_ISLNK(observed.st_mode):
                raise ExportError(
                    "ARCH_EXPORT_UNSAFE_OUTPUT_PATH",
                    "output_preflight",
                    "Output must not be a symbolic link.",
                    "operator",
                    destination_present=True,
                )
            if observed is not None and not stat.S_ISREG(observed.st_mode):
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
                    "--overwrite is disabled because safe conditional destructive replacement is unavailable.",
                    "operator",
                    destination_present=destination_present,
                )
            if destination_present:
                raise ExportError(
                    "ARCH_EXPORT_OUTPUT_EXISTS",
                    "output_preflight",
                    "Output already exists.",
                    "operator",
                    destination_present=True,
                )

            expected_bytes = canonical_bytes(value) + b"\n"
            candidate = _allocate_candidate(root, path.name, ancestry.parent.descriptor)
            try:
                assert candidate.descriptor is not None
                _write_all(candidate.descriptor, expected_bytes)
                os.fsync(candidate.descriptor)
            except OSError as exc:
                warnings: list[str] = []
                _release_candidate(candidate, warnings)
                raise ExportError(
                    "ARCH_EXPORT_STAGED_CANDIDATE_WRITE_FAILED",
                    "atomic_write",
                    f"Staged candidate write failed: {type(exc).__name__}.",
                    "operator",
                    cleanup_warnings=warnings,
                ) from exc
            return cls(
                root=root,
                path=path,
                destination_name=path.name,
                candidate=candidate,
                expected_bytes=expected_bytes,
                ancestry=ancestry,
                lock=lock,
            )
        except ExportError as exc:
            if candidate is not None:
                _release_candidate(candidate, exc.cleanup_warnings)
            if lock is not None:
                warning = lock.release()
                if warning is not None:
                    _append_warning(exc.cleanup_warnings, warning)
            if ancestry is not None:
                for warning in ancestry.close():
                    _append_warning(exc.cleanup_warnings, warning)
            raise
        except OSError as exc:
            warnings: list[str] = []
            if candidate is not None:
                _release_candidate(candidate, warnings)
            if lock is not None:
                warning = lock.release()
                if warning is not None:
                    _append_warning(warnings, warning)
            if ancestry is not None:
                for warning in ancestry.close():
                    _append_warning(warnings, warning)
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_PREFLIGHT_FAILED",
                "output_preflight",
                f"Output preflight failed: {type(exc).__name__}.",
                "operator",
                cleanup_warnings=warnings,
            ) from exc

    @property
    def candidate_name(self) -> str | None:
        return self.candidate.residue_path.name if self.candidate.residue_path is not None else None

    def allowed_paths(self) -> tuple[Path, ...]:
        if self.candidate.residue_path is None:
            return ()
        try:
            self.candidate.residue_path.relative_to(self.root)
        except ValueError:
            return ()
        return (self.candidate.residue_path,)

    def _destination_stat(self, stage: str) -> os.stat_result | None:
        try:
            return os.stat(
                self.destination_name,
                dir_fd=self.ancestry.parent.descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED",
                stage,
                f"Output path inspection failed: {type(exc).__name__}.",
                "operator",
            ) from exc

    def destination_identity(self, stage: str = "output_state") -> tuple[int, int] | None:
        observed = self._destination_stat(stage)
        return _identity_from_stat(observed) if observed is not None else None

    def _owned_candidate_descriptor(self, stage: str) -> int:
        if self.candidate.state != "owned" or self.candidate.descriptor is None:
            raise ExportError(
                "ARCH_EXPORT_CANDIDATE_OWNERSHIP_LOST",
                stage,
                "The transaction no longer owns a staged candidate descriptor.",
                "operator",
                cleanup_warnings=list(self.cleanup_warnings),
            )
        try:
            observed = _identity_from_stat(os.fstat(self.candidate.descriptor))
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_CANDIDATE_OWNERSHIP_LOST",
                stage,
                f"The staged candidate descriptor is unavailable: {type(exc).__name__}.",
                "operator",
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc
        if observed != self.candidate.identity:
            raise ExportError(
                "ARCH_EXPORT_CANDIDATE_OWNERSHIP_LOST",
                stage,
                "The staged candidate descriptor identity changed.",
                "operator",
                cleanup_warnings=list(self.cleanup_warnings),
            )
        return self.candidate.descriptor

    def read_candidate(self, stage: str = "staged_candidate_validation") -> bytes:
        self.ancestry.verify(stage)
        descriptor = self._owned_candidate_descriptor(stage)
        try:
            os.lseek(descriptor, 0, os.SEEK_SET)
            return _read_all(descriptor)
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_STAGED_CANDIDATE_READ_FAILED",
                stage,
                f"Staged candidate read failed: {type(exc).__name__}.",
                "operator",
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc

    def publish(self) -> None:
        self.ancestry.verify("prepublication_ancestry")
        candidate_descriptor = self._owned_candidate_descriptor("atomic_write")
        candidate_identity = self.candidate.identity
        source = f"/proc/self/fd/{candidate_descriptor}"
        try:
            os.link(
                source,
                self.destination_name,
                dst_dir_fd=self.ancestry.parent.descriptor,
                follow_symlinks=True,
            )
        except FileExistsError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_EXISTS",
                "atomic_write",
                "Output already exists at the atomic no-clobber publication boundary.",
                "operator",
                destination_present=True,
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc
        except (NotImplementedError, OSError) as exc:
            raise ExportError(
                "ARCH_EXPORT_ATOMIC_NO_CLOBBER_UNSUPPORTED",
                "atomic_write",
                f"Descriptor-derived atomic no-clobber publication is unavailable: {type(exc).__name__}.",
                "operator",
                destination_present=self._destination_stat("atomic_write") is not None,
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc

        self.published = True
        self.published_identity = candidate_identity
        try:
            descriptor = os.open(
                self.destination_name,
                _file_read_flags(),
                dir_fd=self.ancestry.parent.descriptor,
            )
        except OSError as exc:
            current_identity = self.destination_identity("atomic_write")
            raise ExportError(
                "ARCH_EXPORT_PUBLISHED_OUTPUT_OPEN_FAILED",
                "atomic_write",
                f"The published output could not be opened safely: {type(exc).__name__}.",
                "operator",
                destination_present=current_identity is not None,
                concurrent_destination_preserved=(
                    current_identity is not None and current_identity != candidate_identity
                ),
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc
        try:
            observed = os.fstat(descriptor)
        except OSError as exc:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise ExportError(
                "ARCH_EXPORT_PUBLISHED_OUTPUT_INSPECTION_FAILED",
                "atomic_write",
                f"Published output descriptor inspection failed: {type(exc).__name__}.",
                "operator",
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc
        published_identity = _identity_from_stat(observed)
        current_identity = self.destination_identity("atomic_write")
        if published_identity != candidate_identity or current_identity != candidate_identity:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise ExportError(
                "ARCH_EXPORT_PUBLICATION_IDENTITY_MISMATCH",
                "atomic_write",
                "The descriptor-relative destination no longer identifies the staged candidate.",
                "operator",
                destination_present=current_identity is not None,
                concurrent_destination_preserved=(
                    current_identity is not None and current_identity != candidate_identity
                ),
                cleanup_warnings=list(self.cleanup_warnings),
            )
        self.published_descriptor = descriptor
        _release_candidate(self.candidate, self.cleanup_warnings)
        try:
            os.fsync(self.ancestry.parent.descriptor)
        except OSError:
            pass
        self.ancestry.verify("postpublication_ancestry")

    def _owned_bytes(self) -> bytes:
        if self.published_descriptor is None:
            raise ExportError(
                "ARCH_EXPORT_PUBLICATION_NOT_OWNED",
                "post_write_validation",
                "No transaction-owned published descriptor is available.",
                "operator",
                destination_present=self._destination_stat("post_write_validation") is not None,
                cleanup_warnings=list(self.cleanup_warnings),
            )
        try:
            os.lseek(self.published_descriptor, 0, os.SEEK_SET)
            return _read_all(self.published_descriptor)
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_READ_FAILED",
                "post_write_validation",
                f"Published output read failed: {type(exc).__name__}.",
                "operator",
                destination_present=(
                    self._destination_stat("post_write_validation") is not None
                ),
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc

    def verify_owned(self, stage: str) -> bytes:
        self.ancestry.verify(stage)
        if self.published_descriptor is None or self.published_identity is None:
            raise ExportError(
                "ARCH_EXPORT_PUBLICATION_NOT_OWNED",
                stage,
                "No transaction-owned publication identity is available.",
                "operator",
                destination_present=self._destination_stat(stage) is not None,
                cleanup_warnings=list(self.cleanup_warnings),
            )
        try:
            descriptor_identity = _identity_from_stat(os.fstat(self.published_descriptor))
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED",
                stage,
                f"Published output descriptor inspection failed: {type(exc).__name__}.",
                "operator",
                cleanup_warnings=list(self.cleanup_warnings),
            ) from exc
        current_identity = self.destination_identity(stage)
        if descriptor_identity != self.published_identity or current_identity != self.published_identity:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_IDENTITY_DRIFT",
                stage,
                "The descriptor-relative destination no longer identifies the transaction-owned output.",
                "operator",
                destination_present=current_identity is not None,
                concurrent_destination_preserved=(
                    current_identity is not None and current_identity != self.published_identity
                ),
                cleanup_warnings=list(self.cleanup_warnings),
            )
        observed_bytes = self._owned_bytes()
        if observed_bytes != self.expected_bytes:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_BYTE_DRIFT",
                stage,
                "The transaction-owned output bytes changed after publication.",
                "operator",
                destination_present=True,
                cleanup_warnings=list(self.cleanup_warnings),
            )
        return observed_bytes

    def rollback(self) -> None:
        _release_candidate(self.candidate, self.cleanup_warnings)
        if self.published:
            _append_warning(
                self.cleanup_warnings,
                f"ARCH_EXPORT_FAILED_OUTPUT_RETAINED:{self.path.name}",
            )

    def commit(self) -> list[str]:
        self.verify_owned("publication_commit")
        self.committed = True
        try:
            os.fsync(self.ancestry.parent.descriptor)
        except OSError:
            pass
        return list(self.cleanup_warnings)

    def close(self) -> list[str]:
        _release_candidate(self.candidate, self.cleanup_warnings)
        if self.published_descriptor is not None:
            descriptor, self.published_descriptor = self.published_descriptor, None
            try:
                os.close(descriptor)
            except OSError as exc:
                _append_warning(
                    self.cleanup_warnings,
                    f"ARCH_EXPORT_OUTPUT_DESCRIPTOR_CLOSE_FAILED:{type(exc).__name__}",
                )
        warning = self.lock.release()
        if warning is not None:
            _append_warning(self.cleanup_warnings, warning)
        for warning in self.ancestry.close():
            _append_warning(self.cleanup_warnings, warning)
        return list(self.cleanup_warnings)
