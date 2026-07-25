"""Process-local capability boundary for Runtime-issued Architect Payloads."""
from __future__ import annotations

import hashlib
import json
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any


class RuntimePayloadAuthorityError(RuntimeError):
    """Raised when a caller attempts to bypass the terminal Runtime transaction."""


@dataclass(frozen=True)
class _RuntimePayloadIssuance:
    payload_object_id: int
    payload_digest: str
    run_id: str
    source_kind: str
    synthetic: bool
    context_object_id: int


_ACTIVE_ISSUANCE: ContextVar[_RuntimePayloadIssuance | None] = ContextVar(
    "architect_runtime_payload_issuance", default=None
)


def _digest(value: Any) -> str:
    try:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RuntimePayloadAuthorityError(
            f"Runtime-issued Payload is not canonical JSON: {exc}"
        ) from exc
    return hashlib.sha256(raw).hexdigest()


def _issue_runtime_terminal_payload(
    payload: dict[str, Any],
    *,
    run_state: dict[str, Any],
    source_kind: str,
) -> dict[str, Any]:
    """Bind one exact Payload object to the active terminal evaluator transaction."""

    import architect_quality_runtime as runtime

    context = runtime.current_run_context()
    if context is None:
        raise RuntimePayloadAuthorityError(
            "Payload issuance requires an active Runtime evaluator transaction."
        )
    if source_kind != context.source_kind:
        raise RuntimePayloadAuthorityError(
            "Payload issuance source_kind does not match the active RunContext."
        )
    if run_state.get("current_stage") != "/project-gate-export":
        raise RuntimePayloadAuthorityError(
            "Payload issuance is restricted to the terminal /project-gate-export transaction."
        )
    completed = run_state.get("completed_stages")
    if not isinstance(completed, list) or len(completed) != 11:
        raise RuntimePayloadAuthorityError(
            "Payload issuance requires the complete contiguous preterminal Stage history."
        )
    if completed[-1:] != ["/handoff-export"]:
        raise RuntimePayloadAuthorityError(
            "Payload issuance requires /handoff-export as the accepted preterminal Stage."
        )
    run_id = run_state.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise RuntimePayloadAuthorityError("Runtime-derived run_id is required.")
    if payload.get("synthetic") is not context.synthetic:
        raise RuntimePayloadAuthorityError(
            "Payload synthetic identity does not match the active RunContext."
        )
    identity = payload.get("payload_identity")
    if not isinstance(identity, dict) or identity.get("created_by") != "architect_quality_runtime":
        raise RuntimePayloadAuthorityError(
            "Payload identity is not Runtime-issued."
        )

    issuance = _RuntimePayloadIssuance(
        payload_object_id=id(payload),
        payload_digest=_digest(payload),
        run_id=run_id,
        source_kind=context.source_kind,
        synthetic=context.synthetic,
        context_object_id=id(context),
    )
    _ACTIVE_ISSUANCE.set(issuance)
    return payload


def _consume_runtime_terminal_payload(
    payload: dict[str, Any],
    *,
    run_id: str,
) -> _RuntimePayloadIssuance:
    """Consume the one-shot capability for the exact Runtime-issued Payload object."""

    import architect_quality_runtime as runtime

    issuance = _ACTIVE_ISSUANCE.get()
    _ACTIVE_ISSUANCE.set(None)
    context = runtime.current_run_context()
    if issuance is None or context is None:
        raise RuntimePayloadAuthorityError(
            "Direct Project Gate export from a caller-supplied Payload is unsupported."
        )
    if issuance.context_object_id != id(context):
        raise RuntimePayloadAuthorityError(
            "Payload issuance belongs to another Runtime transaction."
        )
    if issuance.payload_object_id != id(payload):
        raise RuntimePayloadAuthorityError(
            "Only the exact Runtime-issued Payload object may enter the exporter."
        )
    if issuance.payload_digest != _digest(payload):
        raise RuntimePayloadAuthorityError(
            "Runtime-issued Payload changed after canonical assembly."
        )
    if issuance.run_id != run_id:
        raise RuntimePayloadAuthorityError(
            "Exporter run_id does not match Runtime-derived Run State."
        )
    if issuance.source_kind != context.source_kind or issuance.synthetic is not context.synthetic:
        raise RuntimePayloadAuthorityError(
            "Payload issuance context changed before export."
        )
    return issuance


__all__ = ["RuntimePayloadAuthorityError"]
