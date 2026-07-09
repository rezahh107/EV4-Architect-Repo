from __future__ import annotations

from typing import Any

SUCCESS_RECEIPT_TEMPLATE = (
    "✅ تصمیم به decision card کرنل وصل شده است؛ برای {decision_family} "
    "مقدار {selected_option} انتخاب شد چون evidence_refs معتبر وجود دارد."
)
WARNING_RECEIPT = "⚠️ این تصمیم هنوز رسید معتبر کرنل ندارد؛ machine-readable trace یا evidence کافی نیست."

REQUIRED_TRACE_FIELDS = (
    "decision_family",
    "decision_card_ref",
    "selected_option",
    "rejected_options",
    "evidence_refs",
    "evidence_state",
    "consumer_stage",
)


def missing_receipt_trace_fields(trace: Any) -> list[str]:
    """Return required receipt trace fields that are absent or empty.

    Receipt validation is presentation-only. It does not infer missing Kernel
    lineage, validate decision semantics, or replace the machine-readable trace.
    """
    if not isinstance(trace, dict):
        return list(REQUIRED_TRACE_FIELDS)

    missing: list[str] = []
    for field in REQUIRED_TRACE_FIELDS:
        value = trace.get(field)
        if value is None or value == "" or value == []:
            missing.append(field)
    return missing


def format_kernel_decision_receipt(trace: Any) -> str:
    """Format a UX-safe human receipt from a complete machine-readable trace.

    A success receipt is emitted only when every required trace field is present.
    Incomplete traces always downgrade to the insufficient-evidence warning.
    """
    missing = missing_receipt_trace_fields(trace)
    if missing:
        return WARNING_RECEIPT

    assert isinstance(trace, dict)
    return SUCCESS_RECEIPT_TEMPLATE.format(
        decision_family=trace["decision_family"],
        selected_option=trace["selected_option"],
    )


def build_receipt_entry(trace: Any) -> dict[str, Any]:
    """Build a receipt entry while preserving the original machine trace."""
    missing = missing_receipt_trace_fields(trace)
    return {
        "receipt_status": "success" if not missing else "insufficient_evidence",
        "receipt_text": format_kernel_decision_receipt(trace),
        "missing_trace_fields": missing,
        "machine_trace": trace,
    }
