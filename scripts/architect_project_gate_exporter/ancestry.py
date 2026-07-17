from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import (
    ExportError,
    _DIR_FD_CAPABILITIES,
    _FOLLOW_SYMLINK_CAPABILITIES,
    _pairs,
    _reject_constant,
    inside,
)


def _identity_from_stat(observed: os.stat_result) -> tuple[int, int]:
    return observed.st_dev, observed.st_ino


def _identity(path: Path) -> tuple[int, int] | None:
    try:
        return _identity_from_stat(os.lstat(path))
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ExportError(
            "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED",
            "output_preflight",
            f"Output path inspection failed: {type(exc).__name__}.",
            "operator",
        ) from exc


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


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


def _file_read_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


def _ancestry_primitives_available() -> bool:
    # Capture capability names at import time so deterministic tests may wrap
    # os.stat/os.link without making the platform appear unsupported.
    required_dir_fd = {"open", "stat", "link", "unlink", "mkdir"}
    required_follow = {"stat", "link"}
    return (
        os.name == "posix"
        and bool(getattr(os, "O_DIRECTORY", 0))
        and bool(getattr(os, "O_NOFOLLOW", 0))
        and required_dir_fd.issubset(_DIR_FD_CAPABILITIES)
        and required_follow.issubset(_FOLLOW_SYMLINK_CAPABILITIES)
    )


@dataclass
class DirectoryNode:
    name: str | None
    descriptor: int
    identity: tuple[int, int]


@dataclass
class AncestryBinding:
    root_path: Path
    root: DirectoryNode
    components: list[DirectoryNode]
    closed: bool = False

    @classmethod
    def bind(cls, root_path: Path, parent_path: Path) -> "AncestryBinding":
        if not _ancestry_primitives_available():
            raise ExportError(
                "ARCH_EXPORT_ANCESTRY_BINDING_UNSUPPORTED",
                "output_ancestry",
                "This platform lacks the descriptor-relative primitives required to bind output ancestry.",
                "operator",
            )
        root_path = root_path.resolve()
        parent_path = Path(os.path.abspath(os.fspath(parent_path)))
        try:
            relative = parent_path.relative_to(root_path)
        except ValueError as exc:
            raise ExportError(
                "ARCH_EXPORT_UNSAFE_OUTPUT_PATH",
                "output_preflight",
                "Output parent must remain inside the Architect repository.",
                "operator",
            ) from exc

        descriptors: list[int] = []
        try:
            root_descriptor = os.open(root_path, _directory_flags())
            descriptors.append(root_descriptor)
            root_stat = os.fstat(root_descriptor)
            if not stat.S_ISDIR(root_stat.st_mode):
                raise ExportError(
                    "ARCH_EXPORT_REPOSITORY_ROOT_INVALID",
                    "output_ancestry",
                    "Repository root is not a directory.",
                    "operator",
                )
            root_node = DirectoryNode(None, root_descriptor, _identity_from_stat(root_stat))
            components: list[DirectoryNode] = []
            current_descriptor = root_descriptor
            for part in relative.parts:
                if part in {"", ".", ".."}:
                    raise ExportError(
                        "ARCH_EXPORT_UNSAFE_OUTPUT_PATH",
                        "output_preflight",
                        "Output parent contains an unsafe path component.",
                        "operator",
                    )
                try:
                    entry_stat = os.stat(
                        part, dir_fd=current_descriptor, follow_symlinks=False
                    )
                except FileNotFoundError:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=current_descriptor)
                    except FileExistsError:
                        pass
                    except OSError as exc:
                        raise ExportError(
                            "ARCH_EXPORT_OUTPUT_ANCESTRY_CREATE_FAILED",
                            "output_ancestry",
                            f"Output directory creation failed: {type(exc).__name__}.",
                            "operator",
                        ) from exc
                    try:
                        entry_stat = os.stat(
                            part, dir_fd=current_descriptor, follow_symlinks=False
                        )
                    except OSError as exc:
                        raise ExportError(
                            "ARCH_EXPORT_OUTPUT_ANCESTRY_UNSAFE",
                            "output_ancestry",
                            f"Created output directory could not be inspected safely: {type(exc).__name__}.",
                            "operator",
                        ) from exc
                except OSError as exc:
                    raise ExportError(
                        "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED",
                        "output_ancestry",
                        f"Output directory component inspection failed: {type(exc).__name__}.",
                        "operator",
                    ) from exc
                if not stat.S_ISDIR(entry_stat.st_mode):
                    raise ExportError(
                        "ARCH_EXPORT_OUTPUT_ANCESTRY_UNSAFE",
                        "output_ancestry",
                        "Output path component is not a real directory.",
                        "operator",
                    )
                try:
                    child_descriptor = os.open(
                        part, _directory_flags(), dir_fd=current_descriptor
                    )
                except OSError as exc:
                    code = (
                        "ARCH_EXPORT_OUTPUT_ANCESTRY_UNSAFE"
                        if exc.errno in {errno.ELOOP, errno.ENOTDIR}
                        else "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED"
                    )
                    raise ExportError(
                        code,
                        "output_ancestry",
                        f"Output directory component could not be opened safely: {type(exc).__name__}.",
                        "operator",
                    ) from exc
                descriptors.append(child_descriptor)
                child_stat = os.fstat(child_descriptor)
                if (
                    not stat.S_ISDIR(child_stat.st_mode)
                    or _identity_from_stat(child_stat) != _identity_from_stat(entry_stat)
                ):
                    raise ExportError(
                        "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT",
                        "output_ancestry",
                        "Output directory component changed while being bound.",
                        "operator",
                    )
                node = DirectoryNode(part, child_descriptor, _identity_from_stat(child_stat))
                components.append(node)
                current_descriptor = child_descriptor
            binding = cls(root_path=root_path, root=root_node, components=components)
            binding.verify("output_ancestry_bind")
            return binding
        except Exception:
            for descriptor in reversed(descriptors):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            raise

    @property
    def parent(self) -> DirectoryNode:
        return self.components[-1] if self.components else self.root

    def _raise_drift(self, stage: str, reason: str) -> None:
        raise ExportError(
            "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT", stage, reason, "operator"
        )

    def verify(self, stage: str) -> None:
        if self.closed:
            self._raise_drift(stage, "Output ancestry descriptors are already closed.")
        try:
            root_at_path = os.lstat(self.root_path)
        except FileNotFoundError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT",
                stage,
                "Repository root path disappeared during export.",
                "operator",
            ) from exc
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED",
                stage,
                f"Repository root inspection failed: {type(exc).__name__}.",
                "operator",
            ) from exc
        if (
            not stat.S_ISDIR(root_at_path.st_mode)
            or _identity_from_stat(root_at_path) != self.root.identity
        ):
            self._raise_drift(stage, "Repository root identity changed during export.")

        parent = self.root
        for node in self.components:
            assert node.name is not None
            try:
                observed = os.stat(
                    node.name,
                    dir_fd=parent.descriptor,
                    follow_symlinks=False,
                )
            except (FileNotFoundError, NotADirectoryError) as exc:
                raise ExportError(
                    "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT",
                    stage,
                    "Output directory component disappeared or was redirected.",
                    "operator",
                ) from exc
            except OSError as exc:
                raise ExportError(
                    "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED",
                    stage,
                    f"Output ancestry inspection failed: {type(exc).__name__}.",
                    "operator",
                ) from exc
            if (
                not stat.S_ISDIR(observed.st_mode)
                or _identity_from_stat(observed) != node.identity
            ):
                self._raise_drift(stage, "Output directory component identity changed.")
            try:
                parent_descriptor = os.open("..", _directory_flags(), dir_fd=node.descriptor)
            except OSError as exc:
                raise ExportError(
                    "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED",
                    stage,
                    f"Output parent relationship could not be inspected: {type(exc).__name__}.",
                    "operator",
                ) from exc
            try:
                if _identity_from_stat(os.fstat(parent_descriptor)) != parent.identity:
                    self._raise_drift(stage, "Output directory parent relationship changed.")
            finally:
                os.close(parent_descriptor)
            parent = node

        current_descriptor = os.open(".", _directory_flags(), dir_fd=self.parent.descriptor)
        try:
            for _ in range(1024):
                current_identity = _identity_from_stat(os.fstat(current_descriptor))
                if current_identity == self.root.identity:
                    return
                upper_descriptor = os.open("..", _directory_flags(), dir_fd=current_descriptor)
                upper_identity = _identity_from_stat(os.fstat(upper_descriptor))
                if upper_identity == current_identity:
                    os.close(upper_descriptor)
                    self._raise_drift(
                        stage, "Output parent is no longer a descendant of repository root."
                    )
                os.close(current_descriptor)
                current_descriptor = upper_descriptor
            self._raise_drift(stage, "Output ancestry depth exceeded the safety bound.")
        except ExportError:
            raise
        except OSError as exc:
            raise ExportError(
                "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED",
                stage,
                f"Output ancestry walk failed: {type(exc).__name__}.",
                "operator",
            ) from exc
        finally:
            try:
                os.close(current_descriptor)
            except OSError:
                pass

    def close(self) -> list[str]:
        if self.closed:
            return []
        self.closed = True
        warnings: list[str] = []
        for node in reversed(self.components):
            try:
                os.close(node.descriptor)
            except OSError as exc:
                warnings.append(
                    f"ARCH_EXPORT_ANCESTRY_DESCRIPTOR_CLOSE_FAILED:{type(exc).__name__}"
                )
        try:
            os.close(self.root.descriptor)
        except OSError as exc:
            warnings.append(
                f"ARCH_EXPORT_ANCESTRY_DESCRIPTOR_CLOSE_FAILED:{type(exc).__name__}"
            )
        return warnings
