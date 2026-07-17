from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX fallback
    msvcrt = None

from .base import ExportError
from .ancestry import _output_lock_path


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


def _write_all(descriptor: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(descriptor, data[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _read_all(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
