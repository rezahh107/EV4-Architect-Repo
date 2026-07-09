# Wave 5 — UX-Safe Kernel Decision Receipts

Status: proposed
Scope: presentation_layer_only

Wave 5 adds a small human-readable receipt layer for Architect Kernel decision traces. The receipt is not a replacement for `kernel_decision_records[]`, does not validate downstream readiness, and does not upgrade any enforcement status.

## Source of Truth

The machine-readable decision trace remains the source of truth. A success receipt may be shown only when the trace includes all Kernel decision record fields required by `contracts/ARCHITECT_STAGE_EVIDENCE_PAYLOAD_V1.md`:

- `decision_family`
- `decision_card_ref`
- `selected_option`
- `rejected_options`
- `evidence_refs`
- `evidence_state`

If any required Kernel decision record field is missing or empty, the formatter must show the warning receipt instead of a green success receipt.

`consumer_stage` may appear as receipt-level metadata outside `machine_trace`, but it is not part of the current Kernel decision record shape and must not be required for a success receipt.

## Receipt Text

Success receipt pattern:

```text
✅ تصمیم به decision card کرنل وصل شده است؛ برای [decision_family] مقدار [selected_option] انتخاب شد چون evidence_refs معتبر وجود دارد.
```

Warning receipt pattern:

```text
⚠️ این تصمیم هنوز رسید معتبر کرنل ندارد؛ machine-readable trace یا evidence کافی نیست.
```

## Boundaries

- No new enforcement status is claimed.
- No CI, sequence, downstream, runtime, or production readiness status is upgraded.
- No authored `resolved` or `production_ready` fields are added.
- Receipt text must not be used to invent Kernel decision traces or decision card references.
- Receipt text must not be used as proof of decision validity without the machine-readable trace.
- Receipt metadata outside `machine_trace` must not be treated as Kernel decision evidence.

## Added Surfaces

- Reusable formatter: `scripts/kernel_decision_receipts.py`
- Positive fixture: `fixtures/kernel-decision-receipts/complete-trace-success-receipt.v1.json`
- Negative fixture: `fixtures/kernel-decision-receipts/missing-trace-warning-receipt.v1.json`
- Focused tests: `tests/test_kernel_decision_receipts.py`
