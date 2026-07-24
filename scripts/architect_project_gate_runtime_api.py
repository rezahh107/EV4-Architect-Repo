"""Official Runtime-owned Project Gate finalization API bridge."""
from __future__ import annotations

import copy
import functools
from pathlib import Path
from typing import Any, Iterable

import architect_quality_runtime as _runtime
from architect_project_gate_finalization import (
    ProjectGateFinalizationResult,
    _ProjectGateExecution,
    evaluate_project_gate_execution,
    failed_result,
    publish_project_gate_execution,
)

_CALLER_AUTHORITY_FIELDS = frozenset(
    {
        "artifact",
        "capability",
        "ce_transition_authorized",
        "digests",
        "eligibility",
        "functional_eligibility",
        "handoff_allowed",
        "payload",
        "payload_path",
        "producer_provenance",
        "project_gate_accepted",
        "project_gate_payload",
        "provenance",
        "receipt",
        "run_state",
        "runtime_capability",
        "stage_results",
        "validation_result",
        "validator_result",
    }
)


def _install_terminal_execution_bridge() -> None:
    """Install the explicit terminal execution return path on the loaded Runtime core."""

    _runtime.INTERNAL_EVALUATOR._evaluate_project_gate = functools.partial(
        evaluate_project_gate_execution,
        producer_provenance=_runtime.INTERNAL_EVALUATOR._producer_provenance,
        expected_issues=_runtime.INTERNAL_EVALUATOR._expected_issues,
        issue_factory=_runtime.INTERNAL_EVALUATOR._issue,
    )


_install_terminal_execution_bridge()


def _caller_authority_diagnostics(outputs: list[Any]) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for index, item in enumerate(outputs):
        if not isinstance(item, dict):
            continue
        for field in sorted(set(item) & _CALLER_AUTHORITY_FIELDS):
            diagnostics.append(
                {
                    "code": "RUNTIME_CALLER_FINALIZATION_AUTHORITY_FIELD_FORBIDDEN",
                    "message": (
                        f"Stage Output cannot supply Runtime finalization authority field {field!r}."
                    ),
                    "path": f"history[{index}].{field}",
                    "stage_id": item.get("stage_id"),
                }
            )
    return diagnostics


def finalize_project_gate(
    stage_outputs: Iterable[dict[str, Any]],
    *,
    run_context: Any,
    repository_root: Path,
    output_directory: Path,
    git_provider: Any | None = None,
) -> ProjectGateFinalizationResult:
    """Replay exactly twelve Stage Outputs once and publish the terminal execution.

    The API accepts Stage Outputs only. Payloads, Stage Results, Run State,
    provenance, eligibility, digests, and Handoff booleans are never inputs.
    """

    root = Path(repository_root).expanduser().resolve()
    outputs = [copy.deepcopy(item) for item in stage_outputs]
    run_id = (
        outputs[0].get("run_id")
        if outputs and isinstance(outputs[0], dict)
        else None
    )
    caller_diagnostics = _caller_authority_diagnostics(outputs)
    if caller_diagnostics:
        return failed_result(
            run_id=run_id,
            source_kind=run_context.source_kind,
            diagnostics=caller_diagnostics,
        )
    try:
        replay = _runtime._replay_outcome(
            outputs,
            run_context=run_context,
            repository_root=root,
            require_terminal=True,
            git_provider=git_provider,
        )
    except _runtime.ArchitectRuntimeExpectedError as exc:
        return failed_result(
            run_id=run_id,
            source_kind=run_context.source_kind,
            diagnostics=[_runtime._diagnostic_dict(item) for item in exc.diagnostics],
        )

    if replay.status != "valid" or replay.run_state is None:
        return failed_result(
            run_id=run_id,
            source_kind=run_context.source_kind,
            diagnostics=[
                _runtime._diagnostic_dict(item) for item in replay.diagnostics
            ],
            stage_results=tuple(
                copy.deepcopy(item) for item in replay.results
            ),
            run_state=replay.run_state,
        )
    if len(replay.results) != 12:
        return failed_result(
            run_id=run_id,
            source_kind=run_context.source_kind,
            diagnostics=[
                {
                    "code": "RUNTIME_PROJECT_GATE_HISTORY_INCOMPLETE",
                    "message": "Project Gate finalization requires all twelve Stage Results.",
                    "path": "history",
                    "stage_id": "/project-gate-export",
                }
            ],
            stage_results=tuple(copy.deepcopy(item) for item in replay.results),
            run_state=replay.run_state,
        )

    execution = replay.results[-1].get("project_gate_export")
    if not isinstance(execution, _ProjectGateExecution):
        return failed_result(
            run_id=run_id,
            source_kind=run_context.source_kind,
            diagnostics=[
                {
                    "code": "RUNTIME_PROJECT_GATE_EXECUTION_MISSING",
                    "message": "Terminal Runtime execution was not produced.",
                    "path": "results[-1].project_gate_export",
                    "stage_id": "/project-gate-export",
                }
            ],
            stage_results=tuple(copy.deepcopy(item) for item in replay.results),
            run_state=replay.run_state,
        )

    return publish_project_gate_execution(
        execution,
        stage_outputs=outputs,
        stage_results=tuple(copy.deepcopy(item) for item in replay.results),
        run_state=copy.deepcopy(replay.run_state),
        run_context=run_context,
        repository_root=root,
        output_directory=Path(output_directory),
        runtime_interface_id=_runtime.RUNTIME_INTERFACE_ID,
    )


__all__ = ["ProjectGateFinalizationResult", "finalize_project_gate"]
