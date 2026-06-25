# Stage 2/4/7/10 Responsive Start Packet Review Fixes

Status: confirmed_review_fix_patch_v1.0.1
Version: 1.0.1
Applies to:
- `contracts/EV4_RESPONSIVE_START_PACKET_CONTRACT.md`
- `stages/STAGE_2_4_7_10_RESPONSIVE_START_PACKET_PATCH.md`

This overlay records the accepted Gemini review fixes for PR #4. It is the active correction layer until the base files are inlined in a later cleanup.

## RF-001 — Required Stage 8 input

`contracts/EV4_RESPONSIVE_START_PACKET_CONTRACT.md` Section 3 must include this required upstream input between `build_tree_payload` and `final_audit_payload`:

```yaml
  implementation_payload:
    source_stage: /implementation
    used_for:
      - asset accessibility map
      - meaningful content visibility policy
      - responsive implementation plan
```

A full `EV4_RESPONSIVE_START_PACKET` cannot be emitted unless `implementation_payload` is present or explicitly marked unavailable with `packet_status: blocked_or_partial`.

## RF-002 — Route seed advisory field name

Every route seed block in `stages/STAGE_2_4_7_10_RESPONSIVE_START_PACKET_PATCH.md` must use this field:

```yaml
route_is_advisory_only: true
```

The older alias `advisory_only` is invalid after this overlay.

Affected examples:

```yaml
downstream_route_seed:
  route: same_tree_responsive_overrides | viewport_specific_variant_tree | hybrid_split | unresolved_requires_designer_input
  confidence: high | medium | low | unknown
  route_is_advisory_only: true

responsive_route_seed:
  route: same_tree_responsive_overrides | viewport_specific_variant_tree | hybrid_split | unresolved_requires_designer_input
  confidence: high | medium | low | unknown
  reason:
  route_is_advisory_only: true
```

## RF-003 — `/score-audit` repair owner

The `responsive_start_packet_audit.repair_owner` enum in `stages/STAGE_2_4_7_10_RESPONSIVE_START_PACKET_PATCH.md` must be read as:

```yaml
repair_owner: /score-evidence | /score-audit | /build-tree | /implementation | /final-audit | /handoff-export
```

## Source-of-truth order

For responsive start packet work after this review fix, use this order:

```text
1. This review-fix overlay v1.0.1
2. contracts/EV4_RESPONSIVE_START_PACKET_CONTRACT.md
3. stages/STAGE_2_4_7_10_RESPONSIVE_START_PACKET_PATCH.md
4. Older examples only when not contradicted by 1-3
```

## Machine-readable payload

```json
{
  "schema": "ev4-responsive-start-packet-review-fix@1.0.1",
  "status": "confirmed_review_fix_patch_v1.0.1",
  "fixes": [
    "RF-001-add-implementation-payload-required-input",
    "RF-002-align-route-is-advisory-only-field-name",
    "RF-003-add-score-audit-repair-owner"
  ],
  "non_regression_rule": "viewport-specific variant routing must not improve desktop same-tree Responsiveness scoring",
  "next_cleanup": "Inline this overlay into the base contract and base stage patch when direct file replacement is available."
}
```
