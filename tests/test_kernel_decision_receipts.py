import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "kernel_decision_receipts.py"

spec = importlib.util.spec_from_file_location("kernel_decision_receipts", SCRIPT)
receipt_module = importlib.util.module_from_spec(spec)
sys.modules["kernel_decision_receipts"] = receipt_module
assert spec.loader is not None
spec.loader.exec_module(receipt_module)

WARNING_RECEIPT = receipt_module.WARNING_RECEIPT
build_receipt_entry = receipt_module.build_receipt_entry
format_kernel_decision_receipt = receipt_module.format_kernel_decision_receipt


def complete_trace():
    return {
        "decision_family": "layout_structure",
        "decision_card_ref": "kernel/decision-governance/p0-decision-matrices.v0.json#decision_family_id=layout_structure",
        "selected_option": "Relative Stage + SVG Connector Layer",
        "rejected_options": ["absolute-only overlay"],
        "evidence_refs": ["ev-rec", "ev-stage7"],
        "evidence_state": "observed",
        "consumer_stage": "architect",
    }


def test_complete_machine_trace_allows_success_receipt():
    receipt = format_kernel_decision_receipt(complete_trace())

    assert receipt == (
        "✅ تصمیم به decision card کرنل وصل شده است؛ برای layout_structure "
        "مقدار Relative Stage + SVG Connector Layer انتخاب شد چون evidence_refs معتبر وجود دارد."
    )


def test_missing_decision_card_ref_blocks_success_receipt():
    trace = complete_trace()
    del trace["decision_card_ref"]

    entry = build_receipt_entry(trace)

    assert entry["receipt_status"] == "insufficient_evidence"
    assert entry["receipt_text"] == WARNING_RECEIPT
    assert "decision_card_ref" in entry["missing_trace_fields"]


def test_missing_evidence_refs_blocks_success_receipt():
    trace = complete_trace()
    trace["evidence_refs"] = []

    entry = build_receipt_entry(trace)

    assert entry["receipt_status"] == "insufficient_evidence"
    assert entry["receipt_text"] == WARNING_RECEIPT
    assert "evidence_refs" in entry["missing_trace_fields"]


def test_warning_receipt_is_used_when_trace_is_incomplete():
    assert format_kernel_decision_receipt({"decision_family": "layout_structure"}) == WARNING_RECEIPT


def test_receipt_does_not_replace_machine_trace():
    trace = complete_trace()

    entry = build_receipt_entry(trace)

    assert entry["receipt_status"] == "success"
    assert entry["machine_trace"] is trace
    assert entry["machine_trace"]["decision_card_ref"] == trace["decision_card_ref"]
    assert "receipt_text" in entry
