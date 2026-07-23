"""Typed expected-failure boundary for the single Architect Runtime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RuntimeDiagnostic:
    code: str
    message: str
    path: str | None = None
    stage_id: str | None = None

    def render(self) -> str:
        location = self.path or self.stage_id
        return f"{self.code}: {location}: {self.message}" if location else f"{self.code}: {self.message}"


class ArchitectRuntimeExpectedError(Exception):
    """Expected invalid input, domain failure, or supported Runtime environment failure."""

    def __init__(self, diagnostics: RuntimeDiagnostic | Iterable[RuntimeDiagnostic]):
        if isinstance(diagnostics, RuntimeDiagnostic):
            values = (diagnostics,)
        else:
            values = tuple(diagnostics)
        if not values:
            raise ValueError("ArchitectRuntimeExpectedError requires at least one diagnostic")
        self.diagnostics = values
        super().__init__("; ".join(item.render() for item in values))


class StageOutputValidationError(ArchitectRuntimeExpectedError):
    pass


class RunSequenceValidationError(ArchitectRuntimeExpectedError):
    pass


class PayloadDerivationError(ArchitectRuntimeExpectedError):
    pass


class ProjectGateValidationError(ArchitectRuntimeExpectedError):
    pass


class RuntimeEnvironmentError(ArchitectRuntimeExpectedError):
    pass
