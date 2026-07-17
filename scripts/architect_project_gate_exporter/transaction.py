from __future__ import annotations

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
    _strict_json_bytes,
)
from .locking import OutputLock, _read_all, _write_all


@dataclass
class OutputTransaction:
    root: Path
    path: Path
    destination_name: str
    candidate: Path
    candidate_name: str
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
        candidate_name: str | None = None
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

            expected_bytes = canonical_bytes(value) + b"\n"
            for _ in range(128):
                candidate_name = f".{path.name}.{secrets.token_hex(16)}.tmp"
                flags = (
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                )
                try:
                    descriptor = os.open(
                        candidate_name,
                        flags,
                        0o600,
                        dir_fd=ancestry.parent.descriptor,
                    )
                    break
                except FileExistsError:
                    continue
                except OSError as exc:
                    raise ExportError(
                        "ARCH_EXPORT_STAGED_CANDIDATE_CREATE_FAILED",
                        "atomic_write",
                        f"Staged candidate creation failed: {type(exc).__name__}.",
                        "operator",
                    ) from exc
            else:
                raise ExportError(
                    "ARCH_EXPORT_STAGED_CANDIDATE_CREATE_FAILED",
                    "atomic_write",
                    "Could not allocate an unpredictable staged candidate name.",
                    "operator",
                )
            try:
                _write_all(descriptor, expected_bytes)
                os.fsync(descriptor)
            except OSError as exc:
                raise ExportError(
                    "ARCH_EXPORT_STAGED_CANDIDATE_WRITE_FAILED",
                    "atomic_write",
                    f"Staged candidate write failed: {type(exc).__name__}.",
                    "operator",
                ) from exc
            finally:
                os.close(descriptor)
            return cls(
                root=root,
                path=path,
                destination_name=path.name,
                candidate=path.parent / candidate_name,
                candidate_name=candidate_name,
                expected_bytes=expected_bytes,
                ancestry=ancestry,
                lock=lock,
            )
        except ExportError:
            if candidate_name is not None and ancestry is not None:
                try:
                    os.unlink(candidate_name, dir_fd=ancestry.parent.descriptor)
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
            if lock is not None:
                lock.release()
            if ancestry is not None:
                ancestry.close()
            raise
        except OSError as exc:
            if candidate_name is not None and ancestry is not None:
                try:
                    os.unlink(candidate_name, dir_fd=ancestry.parent.descriptor)
                except OSError:
                    pass
            if lock is not None:
                lock.release()
            if ancestry is not None:
                ancestry.close()
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_PREFLIGHT_FAILED",
                "output_preflight",
                f"Output preflight failed: {type(exc).__name__}.",
                "operator",
            ) from exc

    def allowed_paths(self) -> tuple[Path, ...]:
        return (self.candidate,)

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

    def _unlink_candidate(self) -> None:
        try:
            os.unlink(self.candidate_name, dir_fd=self.ancestry.parent.descriptor)
        except FileNotFoundError:
            pass
        except OSError as exc:
            self.cleanup_warnings.append(
                f"ARCH_EXPORT_CANDIDATE_CLEANUP_FAILED:{type(exc).__name__}"
            )

    def read_candidate(self, stage: str = "staged_candidate_validation") -> bytes:
        self.ancestry.verify(stage)
        try:
            descriptor = os.open(
                self.candidate_name,
                _file_read_flags(),
                dir_fd=self.ancestry.parent.descriptor,
            )
        except FileNotFoundError as exc:
            raise ExportError(
                "ARCH_EXPORT_STAGED_CANDIDATE_MISSING",
                stage,
                "The staged candidate disappeared before validation.",
                "operator",
            ) from exc
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_STAGED_CANDIDATE_READ_FAILED",
                stage,
                f"Staged candidate could not be opened safely: {type(exc).__name__}.",
                "operator",
            ) from exc
        try:
            return _read_all(descriptor)
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_STAGED_CANDIDATE_READ_FAILED",
                stage,
                f"Staged candidate read failed: {type(exc).__name__}.",
                "operator",
            ) from exc
        finally:
            os.close(descriptor)

    def publish(self) -> None:
        self.ancestry.verify("prepublication_ancestry")
        try:
            candidate_stat = os.stat(
                self.candidate_name,
                dir_fd=self.ancestry.parent.descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError as exc:
            raise ExportError(
                "ARCH_EXPORT_STAGED_CANDIDATE_MISSING",
                "atomic_write",
                "The staged candidate disappeared before publication.",
                "operator",
            ) from exc
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_STAGED_CANDIDATE_INSPECTION_FAILED",
                "atomic_write",
                f"Staged candidate inspection failed: {type(exc).__name__}.",
                "operator",
            ) from exc
        candidate_identity = _identity_from_stat(candidate_stat)
        try:
            os.link(
                self.candidate_name,
                self.destination_name,
                src_dir_fd=self.ancestry.parent.descriptor,
                dst_dir_fd=self.ancestry.parent.descriptor,
                follow_symlinks=False,
            )
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
                f"Atomic descriptor-relative no-clobber publication is unavailable: {type(exc).__name__}.",
                "operator",
                destination_present=self._destination_stat("atomic_write") is not None,
            ) from exc

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
            ) from exc
        try:
            observed = os.fstat(descriptor)
        except OSError as exc:
            os.close(descriptor)
            raise ExportError(
                "ARCH_EXPORT_PUBLISHED_OUTPUT_INSPECTION_FAILED",
                "atomic_write",
                f"Published output descriptor inspection failed: {type(exc).__name__}.",
                "operator",
            ) from exc
        published_identity = _identity_from_stat(observed)
        current_identity = self.destination_identity("atomic_write")
        if published_identity != candidate_identity or current_identity != candidate_identity:
            os.close(descriptor)
            raise ExportError(
                "ARCH_EXPORT_PUBLICATION_IDENTITY_MISMATCH",
                "atomic_write",
                "The descriptor-relative destination no longer identifies the staged candidate.",
                "operator",
                destination_present=current_identity is not None,
                concurrent_destination_preserved=(
                    current_identity is not None and current_identity != candidate_identity
                ),
            )
        self.published_descriptor = descriptor
        self.published_identity = published_identity
        self.published = True
        self._unlink_candidate()
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
            )
        try:
            descriptor_identity = _identity_from_stat(os.fstat(self.published_descriptor))
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED",
                stage,
                f"Published output descriptor inspection failed: {type(exc).__name__}.",
                "operator",
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
        self._unlink_candidate()
        if self.published:
            warning = f"ARCH_EXPORT_FAILED_OUTPUT_RETAINED:{self.path.name}"
            if warning not in self.cleanup_warnings:
                self.cleanup_warnings.append(warning)

    def commit(self) -> list[str]:
        self.verify_owned("publication_commit")
        self.committed = True
        try:
            os.fsync(self.ancestry.parent.descriptor)
        except OSError:
            pass
        return list(self.cleanup_warnings)

    def close(self) -> list[str]:
        self._unlink_candidate()
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
        self.cleanup_warnings.extend(self.ancestry.close())
        return list(self.cleanup_warnings)
