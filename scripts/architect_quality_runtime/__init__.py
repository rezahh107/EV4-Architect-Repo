"""Canonical history-replay interface for the single Architect Runtime.

The existing evaluator core remains the only Stage evaluation implementation.
Ordered model-authored Stage Outputs are persistent truth; all Run State and
Stage Results are reconstructed by the Runtime.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_CORE_NAME = "_ev4_architect_quality_runtime_internal"
_CORE_PATH = Path(__file__).resolve().parents[1] / "architect_quality_runtime_core.py"
_spec = importlib.util.spec_from_file_location(_CORE_NAME, _CORE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load Architect Runtime evaluator core: {_CORE_PATH}")
_core = importlib.util.module_from_spec(_spec)
sys.modules[_CORE_NAME] = _core
_spec.loader.exec_module(_core)
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

INTERNAL_EVALUATOR = _core
ROOT = _core.ROOT
RUNTIME_INTERFACE_ID = _core.RUNTIME_INTERFACE_ID
_ACTIVE_RUN_CONTEXT: ContextVar[Any | None] = ContextVar(
    "architect_active_run_context", default=None
)
_ACTIVE_GIT_PROVIDER: ContextVar[Any | None] = ContextVar(
    "architect_active_git_provider", default=None
)


def current_run_context() -> Any | None:
    return _ACTIVE_RUN_CONTEXT.get()


def current_git_provider() -> Any | None:
    return _ACTIVE_GIT_PROVIDER.get()


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _render_diagnostics(exc: Any) -> list[str]:
    return [item.render() for item in getattr(exc, "diagnostics", [])]


def _diagnostics_from_strings(values: Iterable[str], *, stage_id: str | None = None) -> list[Any]:
    diagnostics: list[Any] = []
    for value in values:
        text = str(value)
        code, _, message = text.partition(":")
        diagnostics.append(
            _core.RuntimeDiagnostic(
                code.strip() or "RUNTIME_STAGE_EVALUATION_FAILED",
                message.strip() or text,
                stage_id=stage_id,
            )
        )
    return diagnostics or [
        _core.RuntimeDiagnostic(
            "RUNTIME_STAGE_EVALUATION_FAILED",
            "Stage evaluation failed",
            stage_id=stage_id,
        )
    ]


def _provider_for_context(run_context: Any, git_provider: Any | None) -> Any | None:
    if run_context.source_kind == "live_conversation" and git_provider is not None:
        raise _core.RuntimeEnvironmentError(
            _core.RuntimeDiagnostic(
                "RUNTIME_LIVE_GIT_PROVIDER_INJECTION_FORBIDDEN",
                "live_conversation provenance is resolved only from the actual checkout",
                path="git_provider",
            )
        )
    return git_provider


def _sequence_diagnostics(
    outputs: list[Any], order: list[str], *, require_terminal: bool
) -> list[Any]:
    diagnostics: list[Any] = []
    stage_ids: list[str | None] = []
    run_ids: list[str | None] = []
    for index, item in enumerate(outputs):
        if not isinstance(item, dict):
            diagnostics.append(
                _core.RuntimeDiagnostic(
                    "RUNTIME_STAGE_OUTPUT_INVALID",
                    "Stage Output history entries must be JSON objects",
                    path=f"history[{index}]",
                )
            )
            stage_ids.append(None)
            run_ids.append(None)
            continue
        stage_ids.append(item.get("stage_id"))
        run_ids.append(item.get("run_id"))

    for stage in sorted(
        {value for value in stage_ids if isinstance(value, str) and value not in order}
    ):
        diagnostics.append(
            _core.RuntimeDiagnostic(
                "RUNTIME_STAGE_ID_UNKNOWN",
                f"Unknown Stage Output in history: {stage}",
                path="history",
                stage_id=stage,
            )
        )

    seen: set[str] = set()
    duplicates: set[str] = set()
    for stage in stage_ids:
        if not isinstance(stage, str):
            continue
        if stage in seen:
            duplicates.add(stage)
        seen.add(stage)
    for stage in sorted(duplicates):
        diagnostics.append(
            _core.RuntimeDiagnostic(
                "RUNTIME_STAGE_DUPLICATE",
                f"Stage Output history contains a duplicate Stage: {stage}",
                path="history",
                stage_id=stage,
            )
        )

    nonempty_run_ids = {value for value in run_ids if isinstance(value, str) and value}
    if len(nonempty_run_ids) > 1:
        diagnostics.append(
            _core.RuntimeDiagnostic(
                "RUNTIME_RUN_HISTORY_MIXED",
                "Stage Output history contains incompatible run_id values",
                path="history",
            )
        )

    expected = order if require_terminal else order[: len(stage_ids)]
    if stage_ids != expected:
        diagnostics.append(
            _core.RuntimeDiagnostic(
                "RUNTIME_STAGE_ORDER_MISMATCH",
                "Stage Output history must be one exact contiguous Manifest prefix",
                path="history",
            )
        )
    return diagnostics


def _call_internal_stage(
    stage_output: dict[str, Any],
    state: dict[str, Any],
    *,
    root: Path,
    run_context: Any,
    git_provider: Any | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    context_token = _ACTIVE_RUN_CONTEXT.set(run_context)
    provider_token = _ACTIVE_GIT_PROVIDER.set(git_provider)
    try:
        return _core.evaluate_stage(
            stage_output["stage_id"],
            stage_output,
            state,
            root=root,
            run_context=run_context,
            git_provider=git_provider,
        )
    finally:
        _ACTIVE_GIT_PROVIDER.reset(provider_token)
        _ACTIVE_RUN_CONTEXT.reset(context_token)


def _invalid_run(
    errors: Iterable[str],
    results: list[dict[str, Any]],
    state: dict[str, Any] | None,
    order: list[str],
) -> dict[str, Any]:
    return {
        "status": "invalid",
        "errors": sorted(set(errors)),
        "results": _copy(results),
        "stages_visited": [item["stage_id"] for item in results],
        "all_required_stages_visited": [item["stage_id"] for item in results] == order,
        "terminal_stage": order[-1],
        "run_state": _copy(state),
    }


def _replay_history(
    prior_stage_outputs: Iterable[dict[str, Any]],
    *,
    run_context: Any,
    repository_root: Path = ROOT,
    require_terminal: bool = False,
    git_provider: Any | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    provider = _provider_for_context(run_context, git_provider)
    manifest, _ = _core.load_authority(root)
    order, _ = _core._stage_map(manifest)
    outputs = [_copy(item) for item in prior_stage_outputs]
    if not outputs:
        if require_terminal:
            return _invalid_run(
                ["RUNTIME_RUN_EMPTY: Stage Output history is empty"], [], None, order
            )
        return {
            "status": "valid",
            "errors": [],
            "results": [],
            "stages_visited": [],
            "all_required_stages_visited": False,
            "terminal_stage": order[-1],
            "run_state": None,
        }

    sequence = _sequence_diagnostics(outputs, order, require_terminal=require_terminal)
    if sequence:
        return _invalid_run([item.render() for item in sequence], [], None, order)

    state = _core.initial_run_state(outputs[0].get("run_id"), root=root)
    results: list[dict[str, Any]] = []
    try:
        for output in outputs:
            result, next_state = _call_internal_stage(
                output,
                state,
                root=root,
                run_context=run_context,
                git_provider=provider,
            )
            results.append(result)
            if result["stage_status"] != "pass":
                errors = [
                    f"{result['stage_id']}: {item['issue_id']}"
                    for item in result["blocking_issues"]
                ]
                if require_terminal and len(results) != len(order):
                    errors.append("run: complete replay must pass every mandatory Stage")
                return _invalid_run(errors, results, state, order)
            state = next_state
    except _core.ArchitectRuntimeExpectedError as exc:
        errors = _render_diagnostics(exc)
        if require_terminal and len(results) != len(order):
            errors.append("run: complete replay must pass every mandatory Stage")
        return _invalid_run(errors, results, state, order)

    if require_terminal and len(results) != len(order):
        return _invalid_run(
            ["run: complete replay must pass every mandatory Stage"], results, state, order
        )
    return {
        "status": "valid",
        "errors": [],
        "results": _copy(results),
        "stages_visited": [item["stage_id"] for item in results],
        "all_required_stages_visited": [item["stage_id"] for item in results] == order,
        "terminal_stage": order[-1],
        "run_state": _copy(state),
    }


@dataclass(frozen=True)
class SessionProjection:
    accepted_stage_outputs: tuple[dict[str, Any], ...]
    derived_stage_results: tuple[dict[str, Any], ...]
    run_state: dict[str, Any] | None
    expected_stage: str | None


class RuntimeSession:
    __slots__ = (
        "_root",
        "_run_context",
        "_git_provider",
        "_outputs",
        "_results",
        "_state",
        "_order",
    )

    def __init__(
        self,
        *,
        root: Path,
        run_context: Any,
        git_provider: Any | None,
        outputs: list[dict[str, Any]],
        results: list[dict[str, Any]],
        state: dict[str, Any] | None,
    ) -> None:
        self._root = Path(root).resolve()
        self._run_context = run_context
        self._git_provider = git_provider
        self._outputs = _copy(outputs)
        self._results = _copy(results)
        self._state = _copy(state)
        manifest, _ = _core.load_authority(self._root)
        self._order = _core._stage_map(manifest)[0]

    @property
    def projection(self) -> SessionProjection:
        return SessionProjection(
            accepted_stage_outputs=tuple(_copy(self._outputs)),
            derived_stage_results=tuple(_copy(self._results)),
            run_state=_copy(self._state),
            expected_stage=self.expected_stage,
        )

    @property
    def accepted_stage_outputs(self) -> list[dict[str, Any]]:
        return _copy(self._outputs)

    @property
    def derived_stage_results(self) -> list[dict[str, Any]]:
        return _copy(self._results)

    @property
    def run_state(self) -> dict[str, Any] | None:
        return _copy(self._state)

    @property
    def expected_stage(self) -> str | None:
        return self._order[len(self._outputs)] if len(self._outputs) < len(self._order) else None

    def _advance_strict(self, stage_output: dict[str, Any]) -> dict[str, Any]:
        candidate = _copy(stage_output)
        expected = self.expected_stage
        observed = candidate.get("stage_id") if isinstance(candidate, dict) else None
        if observed != expected:
            raise _core.RunSequenceValidationError(
                _core.RuntimeDiagnostic(
                    "RUNTIME_STAGE_SEQUENCE_MISMATCH",
                    f"RuntimeSession expected {expected!r}, observed {observed!r}",
                    path="stage_output.stage_id",
                    stage_id=observed if isinstance(observed, str) else None,
                )
            )
        if self._state is None:
            self._state = _core.initial_run_state(candidate.get("run_id"), root=self._root)

        if observed == self._order[-1]:
            replay = _replay_history(
                [*self._outputs, candidate],
                run_context=self._run_context,
                repository_root=self._root,
                require_terminal=True,
                git_provider=self._git_provider,
            )
            if replay["status"] != "valid":
                result = replay["results"][-1] if replay["results"] else None
                return {
                    "accepted": False,
                    "stage_result": _copy(result),
                    "diagnostics": list(replay["errors"]),
                    "run_state": _copy(self._state),
                }
            self._outputs.append(candidate)
            self._results = replay["results"]
            self._state = replay["run_state"]
            return {
                "accepted": True,
                "stage_result": _copy(self._results[-1]),
                "diagnostics": [],
                "run_state": _copy(self._state),
            }

        result, next_state = _call_internal_stage(
            candidate,
            self._state,
            root=self._root,
            run_context=self._run_context,
            git_provider=self._git_provider,
        )
        if result["stage_status"] != "pass":
            return {
                "accepted": False,
                "stage_result": _copy(result),
                "diagnostics": [
                    f"{result['stage_id']}: {item['issue_id']}"
                    for item in result["blocking_issues"]
                ],
                "run_state": _copy(self._state),
            }
        self._outputs.append(candidate)
        self._results.append(_copy(result))
        self._state = _copy(next_state)
        return {
            "accepted": True,
            "stage_result": _copy(result),
            "diagnostics": [],
            "run_state": _copy(self._state),
        }

    def advance(self, stage_output: dict[str, Any]) -> dict[str, Any]:
        before = self.projection
        try:
            return self._advance_strict(stage_output)
        except _core.ArchitectRuntimeExpectedError as exc:
            self._outputs = [*before.accepted_stage_outputs]
            self._results = [*before.derived_stage_results]
            self._state = _copy(before.run_state)
            return {
                "accepted": False,
                "stage_result": None,
                "diagnostics": _render_diagnostics(exc),
                "run_state": _copy(self._state),
            }

    def finalize(self) -> dict[str, Any]:
        return _replay_history(
            self._outputs,
            run_context=self._run_context,
            repository_root=self._root,
            require_terminal=True,
            git_provider=self._git_provider,
        )

    def rerun_from(self, earliest_stage: str) -> "RuntimeSession":
        if earliest_stage not in self._order:
            raise _core.RunSequenceValidationError(
                _core.RuntimeDiagnostic(
                    "RUNTIME_RERUN_STAGE_UNKNOWN",
                    f"Unknown rerun Stage: {earliest_stage}",
                    stage_id=earliest_stage,
                )
            )
        return resume_run(
            self._outputs[: self._order.index(earliest_stage)],
            run_context=self._run_context,
            repository_root=self._root,
            git_provider=self._git_provider,
        )


def resume_run(
    prior_stage_outputs: Iterable[dict[str, Any]],
    *,
    run_context: Any,
    repository_root: Path = ROOT,
    git_provider: Any | None = None,
) -> RuntimeSession:
    outputs = [_copy(item) for item in prior_stage_outputs]
    replay = _replay_history(
        outputs,
        run_context=run_context,
        repository_root=repository_root,
        require_terminal=False,
        git_provider=git_provider,
    )
    if replay["status"] != "valid":
        raise _core.RunSequenceValidationError(
            [
                _core.RuntimeDiagnostic(
                    "RUNTIME_RESUME_HISTORY_INVALID",
                    error,
                    path="history",
                )
                for error in replay["errors"]
            ]
        )
    return RuntimeSession(
        root=Path(repository_root),
        run_context=run_context,
        git_provider=_provider_for_context(run_context, git_provider),
        outputs=outputs,
        results=replay["results"],
        state=replay["run_state"],
    )


def evaluate_run(
    outputs: list[dict[str, Any]],
    *,
    run_context: Any,
    root: Path = ROOT,
    require_terminal: bool = True,
    git_provider: Any | None = None,
) -> dict[str, Any]:
    try:
        return _replay_history(
            outputs,
            run_context=run_context,
            repository_root=root,
            require_terminal=require_terminal,
            git_provider=git_provider,
        )
    except _core.ArchitectRuntimeExpectedError as exc:
        manifest, _ = _core.load_authority(root)
        order, _ = _core._stage_map(manifest)
        return _invalid_run(_render_diagnostics(exc), [], None, order)


def evaluate_stage(
    stage_id: str,
    stage_output: dict[str, Any],
    run_state: dict[str, Any] | None = None,
    *,
    root: Path = ROOT,
    run_context: Any | None = None,
    git_provider: Any | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    context = run_context or _core.RunContext(source_kind="live_conversation")
    history: list[dict[str, Any]] = []
    if isinstance(run_state, dict):
        values = run_state.get("evaluated_stage_outputs", [])
        if isinstance(values, list):
            history = [item for item in values if isinstance(item, dict)]
    session = resume_run(
        history,
        run_context=context,
        repository_root=root,
        git_provider=git_provider,
    )
    if stage_output.get("stage_id") != stage_id:
        raise _core.RunSequenceValidationError(
            _core.RuntimeDiagnostic(
                "RUNTIME_STAGE_OUTPUT_IDENTITY_MISMATCH",
                "stage_id argument and Stage Output identity differ",
                stage_id=stage_id,
            )
        )
    outcome = session._advance_strict(stage_output)
    result = outcome.get("stage_result")
    if not isinstance(result, dict) or result.get("stage_id") != stage_id:
        raise _core.StageOutputValidationError(
            _diagnostics_from_strings(outcome.get("diagnostics", []), stage_id=stage_id)
        )
    return result, session.run_state or _core.initial_run_state(
        stage_output.get("run_id"), root=root
    )


def apply_partial_rerun(
    run_state_or_outputs: dict[str, Any] | list[dict[str, Any]],
    earliest_stage: str,
    *,
    root: Path = ROOT,
    run_context: Any | None = None,
    git_provider: Any | None = None,
) -> dict[str, Any]:
    context = run_context or _core.RunContext(source_kind="fixture")
    if isinstance(run_state_or_outputs, list):
        history = [item for item in run_state_or_outputs if isinstance(item, dict)]
        old_state: dict[str, Any] = {}
    else:
        old_state = run_state_or_outputs if isinstance(run_state_or_outputs, dict) else {}
        history = [
            item
            for item in old_state.get("evaluated_stage_outputs", [])
            if isinstance(item, dict)
        ]
    manifest, _ = _core.load_authority(root)
    order, _ = _core._stage_map(manifest)
    if earliest_stage not in order:
        raise _core.RunSequenceValidationError(
            _core.RuntimeDiagnostic(
                "RUNTIME_RERUN_STAGE_UNKNOWN",
                f"Unknown rerun Stage: {earliest_stage}",
                stage_id=earliest_stage,
            )
        )
    index = order.index(earliest_stage)
    retained = history[:index]
    removed = history[index:]
    session = resume_run(
        retained,
        run_context=context,
        repository_root=root,
        git_provider=git_provider,
    )
    new_state = session.run_state
    if new_state is None:
        run_id = history[0].get("run_id") if history else old_state.get("run_id")
        new_state = _core.initial_run_state(run_id, root=root)
    old_unknowns = {
        item.get("unknown_id")
        for item in old_state.get("unknown_ledger", [])
        if isinstance(item, dict)
    }
    new_unknowns = {
        item.get("unknown_id")
        for item in new_state.get("unknown_ledger", [])
        if isinstance(item, dict)
    }
    return {
        "earliest_rerun_stage": earliest_stage,
        "invalidated_stages": [item.get("stage_id") for item in removed],
        "retained_outputs": _copy(retained),
        "preserved_state": _copy(new_state),
        "reactivated_unknowns": sorted(old_unknowns & new_unknowns),
        "discarded_unknowns": sorted(old_unknowns - new_unknowns),
        "candidate_lock_invalidated": bool(
            old_state.get("selected_candidate_locked")
            and not new_state.get("selected_candidate_locked")
        ),
    }


__all__ = [
    "RunContext",
    "RuntimeSession",
    "SessionProjection",
    "SubprocessGitProvider",
    "RUNTIME_INTERFACE_ID",
    "resume_run",
    "evaluate_run",
    "evaluate_stage",
    "apply_partial_rerun",
    "validate_stage_result",
    "load_authority",
    "initial_run_state",
]
