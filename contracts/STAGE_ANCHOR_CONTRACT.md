# Stage Anchor Contract

Status: active
Version: 1.1.0
Applies to: all EV4 Architect stages after `/intake`

---

## Purpose

A `STAGE ANCHOR` is a compact, user-visible context block carried from one stage into the next stage.

It is designed to reduce long-context drift and prevent important unknowns, blockers, gates, payload schemas, hardening status, confidence changes, and repair routes from being buried in the middle of a long conversation.

Core rule:

```text
Anchor the next stage with the minimum facts required to continue safely.
```

The anchor is not hidden chain-of-thought. It is an external, auditable handoff summary.

---

## Required Use

Before starting any stage after `/intake`, the assistant must check for a valid `STAGE ANCHOR` from the previous stage.

If the anchor is missing, outdated, schema-mismatched, or clearly inconsistent with the previous stage output, the assistant must stop and request the correct anchor or regenerate it from the prior stage output.

Do not rely on conversational memory alone.

---

## Canonical Format

```text
STAGE ANCHOR — [Stage ID]
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: [previous stage]
target_stage: [next stage]
target_stage_hardening_status: confirmed | draft | scaffolded | unknown
project_status_version: [STATUS.md version if known]
payload_schema_in: [expected input payload schema]
payload_schema_out: [expected output payload schema]

Carry-forward facts:
- key_decisions:
- selected_or_active_candidates:
- rejected_or_blocked_candidates:
- critical_unknowns:
- confidence_delta:
  - item:
    previous_confidence: confirmed | likely | unknown | blocked | n/a
    current_confidence: confirmed | likely | unknown | blocked | n/a
    direction: increased | decreased | unchanged | resolved | new_unknown
    reason:
    downstream_impact:
- blocking_items:
- gate_results:
- audit_flags:
- tie_or_ambiguity_flags:
- required_user_confirmations:
- repair_routes:

Partial rerun state:
- reusable_until:
- invalidation_triggers:
- earliest_safe_rerun_stage:
- downstream_payloads_dependent_on_this_stage:

Stage input package:
- required_inputs_present:
- required_inputs_missing:
- files_or_sections_to_reference:

Stage boundary:
- allowed_work:
- forbidden_work:
- stop_conditions:

Debug trace:
- debug_trace_required: yes | no
- previous_debug_trace_id: optional
- expected_debug_trace_schema:
```

---

## Minimal Anchor Requirements

Every anchor must include at least:

- `anchor_schema`
- `source_stage`
- `target_stage`
- `target_stage_hardening_status`
- `critical_unknowns`
- `confidence_delta`
- `blocking_items`
- `gate_results`
- `audit_flags`
- `required_user_confirmations`
- `partial_rerun_state`
- `allowed_work`
- `forbidden_work`
- `stop_conditions`

If a field is not applicable, write `None`. Do not omit the field.

---

## Hardening Status Gate

The anchor must declare the target stage hardening status:

```text
target_stage_hardening_status: confirmed | draft | scaffolded | unknown
```

Rules:

- `confirmed`: the stage may run normally if all other inputs pass.
- `draft`: the stage may run only in review, test, or hardening mode.
- `scaffolded`: the stage must not run as production pipeline output unless the user explicitly confirms a scaffolded-stage run.
- `unknown`: stop and inspect `STATUS.md` before continuing.

If the target stage is `draft` or `scaffolded`, the assistant must say that the stage is not production-confirmed and ask whether to proceed in hardening/test mode.

---

## Confidence Delta Rule

The anchor must track whether the current stage changed confidence for important facts or unknowns.

Examples:

```text
confidence_delta:
- item: connector mobile behavior
  previous_confidence: unknown
  current_confidence: unknown
  direction: unchanged
  reason: no mobile view or user instruction provided
  downstream_impact: must remain carried into /implementation

- item: third-party plugin need
  previous_confidence: unknown
  current_confidence: likely_not_needed
  direction: increased
  reason: at least one native audited candidate passed without plugin dependency
  downstream_impact: no longer blocking for /build-tree
```

A confidence increase does not automatically mean the item is confirmed. It only records that the pipeline has more or less usable certainty than before.

Forbidden:

- Do not silently drop an unknown because it feels less important.
- Do not mark an unknown as resolved unless the resolving evidence is named.
- Do not use confidence delta as a recommendation signal.

---

## Anchor Placement Rule

The anchor must appear at the beginning of the user prompt or assistant-generated stage handoff before the next stage starts.

Recommended next-stage prompt shape:

```text
[PASTE STAGE ANCHOR HERE]

Run /target-stage using this anchor and the referenced stage files.
```

---

## Anchor Generation Rule

At the end of every stage, the assistant must emit a `NEXT STAGE ANCHOR` unless the stage fails and requires repair.

If the stage fails, emit a `REPAIR ANCHOR` instead.

---

## NEXT STAGE ANCHOR

Use this when the current stage passes.

```text
NEXT STAGE ANCHOR — [target stage]
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: [current stage]
target_stage: [next stage]
target_stage_hardening_status: confirmed | draft | scaffolded | unknown
...
```

---

## REPAIR ANCHOR

Use this when the current stage fails.

```text
REPAIR ANCHOR — [repair target]
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: [failed stage]
repair_target_stage: [/decompose | /architectures | /score-evidence | /score-audit | /recommend | /build-tree | /implementation | /final-audit | /handoff-export]
failure_type:
failure_evidence:
minimal_repair_instruction:
forbidden_shortcut:
```

---

## Relationship to Partial Rerun

`contracts/PARTIAL_RERUN_CONTRACT.md` defines when a stage may be rerun without restarting the whole pipeline.

Every anchor must preserve enough invalidation information to support partial reruns safely.

The anchor does not decide the rerun by itself; it supplies the state needed for a `PARTIAL RERUN PLAN`.

---

## Relationship to Debug Trace

`STAGE ANCHOR` is the compact handoff block.

`EV4_DEBUG_TRACE` is the detailed diagnostic record.

The anchor should not include full reasoning. It should include only the facts needed to safely start the next stage.

---

## Pass Criteria

A valid anchor passes if:

- It is compact enough to paste into the next prompt.
- It preserves critical unknowns and blockers.
- It records confidence deltas for important unknowns or resolved items.
- It declares target stage hardening status.
- It names gate/audit outcomes.
- It names required confirmations.
- It preserves partial rerun invalidation triggers.
- It defines allowed and forbidden work for the next stage.
- It does not expose hidden chain-of-thought.
- It does not introduce new claims not present in prior stage outputs.


## Receipt-Bound Stage Anchor v1.2.0

New Stage 2-5 outputs after activation use `ev4-stage-anchor@1.2.0` when they claim a validated next-stage boundary. Historical `ev4-stage-anchor@1.1.0` records remain readable as historical evidence only and are not silently upgraded.

Required binding:

```yaml
source_artifact:
  artifact_id:
  artifact_schema:
  artifact_sha256:
  stage_id:
source_validation:
  receipt_id:
  receipt_schema:
  validator_id:
  validator_version:
  status:
```

Rules: a `NEXT STAGE ANCHOR` may be emitted only when the machine-generated receipt status is `valid`; `invalid` or `insufficient_evidence` emits a `REPAIR ANCHOR`; the next stage verifies expected previous stage, artifact ID, schema, exact SHA-256, receipt status, and validator identity/version. A self-authored `gate_results: pass` is not a receipt. Changed artifact bytes invalidate the prior receipt and downstream Anchor. Do not claim chat runtime validation unless the validator actually executed.
