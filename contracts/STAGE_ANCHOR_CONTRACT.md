# Stage Anchor Contract

Status: active
Current Schema: `ev4-stage-anchor@1.3.0`
Schema path: `schemas/ev4-stage-anchor.v1.schema.json`

## Authority boundary

An Anchor is a user-facing handoff carrier. It never independently authorizes continuation. Machine authorization derives only from an independently regenerated valid Validation Bundle.

The only active binding shape is:

```yaml
boundary_ref:
failure_event_ref:
handoff_state:
```

The obsolete v1.2 fields `source_artifact` and `source_validation` are not permitted by the active Schema.

## Success Anchor

```yaml
anchor_schema: ev4-stage-anchor@1.3.0
anchor_type: NEXT_STAGE_ANCHOR
source_stage: <validated Stage>
target_stage: <next Stage>
repair_target_stage: null
boundary_ref: <ev4-stage-boundary-record@1.1.0 reference>
failure_event_ref: null
```

## Repair Anchor

```yaml
anchor_schema: ev4-stage-anchor@1.3.0
anchor_type: REPAIR_ANCHOR
source_stage: <actual failed Stage>
target_stage: null
repair_target_stage: <earliest repair owner>
boundary_ref: <Repair Boundary reference>
failure_event_ref: <Failure Event reference>
```

## Semantic handoff state

`handoff_state` is generated from validated Artifact evidence and contains:

```yaml
critical_unknowns:
blocking_items:
confidence_delta:
  - subject_id:
    subject_type: unknown | candidate | gate | evidence
    previous_confidence: confirmed | likely | unknown | blocked | not_applicable
    current_confidence: confirmed | likely | unknown | blocked | not_applicable
    direction: increased | decreased | unchanged | resolved | new_unknown
    reason:
    evidence_refs:
    downstream_impact:
gate_results:
  receipt_status: valid | invalid
  boundary_transition: next_stage | repair
  next_stage_authorized: true | false
audit_flags:
required_user_confirmations:
partial_rerun_state:
stage_boundary:
```

Receipt status belongs only under `gate_results`; it is not a confidence delta. Active states `carried`, `score_capped`, `blocking`, and `downstream_only` remain visible. A failed or later Stage cannot erase an active predecessor unknown merely by omitting it.

## Historical compatibility

`ev4-stage-anchor@1.1.0` and `ev4-stage-anchor@1.2.0` remain readable as historical evidence only. They cannot authorize current continuation and are never silently upgraded.
