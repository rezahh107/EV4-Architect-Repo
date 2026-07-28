"""Test-only access to the explicit internal terminal execution value."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable


def evaluate_run_with_private_payload(
    runtime: Any,
    stage_outputs: Iterable[dict[str, Any]],
    *,
    root: Path,
    run_context: Any,
    git_provider: Any | None = None,
    require_terminal: bool = True,
) -> dict[str, Any]:
    replay = runtime._replay_outcome(
        stage_outputs,
        run_context=run_context,
        repository_root=root,
        require_terminal=require_terminal,
        git_provider=git_provider,
    )
    outcome = replay.to_public()
    if replay.status != "valid" or not replay.results:
        return outcome
    execution = replay.results[-1].get("project_gate_export")
    payload = getattr(execution, "runtime_issued_payload", None)
    if payload is not None:
        outcome["results"][-1]["project_gate_export"][
            "runtime_issued_payload"
        ] = copy.deepcopy(payload)
    return outcome
