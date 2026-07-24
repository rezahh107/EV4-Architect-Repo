"""History-replay facade for the existing Architect Payload assembler."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any, Iterable

from architect_css_target_validation import validate_css_target_references
from architect_runtime_errors import PayloadDerivationError

_CORE_NAME = "_ev4_architect_payload_assembler_internal"
_CORE_PATH = Path(__file__).resolve().parents[1] / "architect_runtime_payload_assembler_core.py"
_spec = importlib.util.spec_from_file_location(_CORE_NAME, _CORE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load Architect Payload assembler core: {_CORE_PATH}")
_core = importlib.util.module_from_spec(_spec)
sys.modules[_CORE_NAME] = _core
_spec.loader.exec_module(_core)
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

INTERNAL_ASSEMBLER = _core


def _validate_css(payload: dict[str, Any]) -> dict[str, Any]:
    diagnostics = validate_css_target_references(payload)
    if diagnostics:
        raise PayloadDerivationError(diagnostics)
    return payload


def assemble_architect_stage_payload(
    *,
    stage_outputs: Iterable[dict[str, Any]] | None = None,
    run_state: dict[str, Any] | None = None,
    source_kind: str,
    run_context: Any | None = None,
    repository_root: Path | None = None,
    git_provider: Any | None = None,
) -> dict[str, Any]:
    """Assemble only from replayed model-authored Stage Output history.

    During canonical replay the internal evaluator passes the state it has just
    derived. That internal call consumes the state directly to avoid recursive
    replay. External callers never have the active Runtime context and therefore
    always reconstruct from Stage Output history before assembly.
    """

    import architect_quality_runtime as runtime

    active_context = runtime.current_run_context()
    if active_context is not None:
        if not isinstance(run_state, dict):
            raise PayloadDerivationError(
                runtime.RuntimeDiagnostic(
                    "PAYLOAD_REPLAY_STATE_REQUIRED",
                    "Internal terminal assembly requires Runtime-derived replay state",
                    path="run_state",
                )
            )
        return _validate_css(
            _core.assemble_architect_stage_payload(
                run_state=run_state,
                source_kind=active_context.source_kind,
            )
        )

    if stage_outputs is None:
        values = run_state.get("evaluated_stage_outputs", []) if isinstance(run_state, dict) else []
        stage_outputs = [item for item in values if isinstance(item, dict)]
    history = [copy.deepcopy(item) for item in stage_outputs]
    root = Path(repository_root or runtime.ROOT).resolve()
    context = run_context or runtime.RunContext(source_kind=source_kind)
    session = runtime.resume_run(
        history,
        run_context=context,
        repository_root=root,
        git_provider=git_provider,
    )
    canonical_state = session.run_state
    if canonical_state is None:
        raise PayloadDerivationError(
            runtime.RuntimeDiagnostic(
                "PAYLOAD_STAGE_HISTORY_REQUIRED",
                "Payload assembly requires a replayable Stage Output history",
                path="history",
            )
        )
    return _validate_css(
        _core.assemble_architect_stage_payload(
            run_state=canonical_state,
            source_kind=context.source_kind,
        )
    )


__all__ = [
    "assemble_architect_stage_payload",
    "validate_derivation_authority",
    "validate_derivation_schema",
    "REQUIRED_PAYLOAD_DERIVATION_RULES",
    "PAYLOAD_DERIVATION_RULES",
    "DERIVATION_KINDS",
]
