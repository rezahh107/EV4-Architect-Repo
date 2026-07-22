# Architect Stage Result v1

Status: active  
Schema: `ev4-architect-stage-result@1.0.0`  
Schema path: `schemas/ev4-architect-stage-result.v1.schema.json`

## Purpose

`Stage Result` is an evaluator-derived normal-run record. It reports whether one logical Stage met its finite quality criteria and whether the exact Manifest successor may run.

```text
Stage Output
+ current Run State
+ Manifest-owned Stage rules
→ scripts/architect_quality_runtime.py#evaluate_stage
→ derived Stage Result
→ exact successor, minimum blocking input, or explicit repair route
```

A Stage Result is not a repository authorization ticket. It does not require a Stage Anchor, Validation Bundle, independent regeneration, exact-head CI, PR review, Merge evidence, or repository maintenance.

## Authority boundary

The Stage producer may provide domain content, structured assessment evidence, explicit blockers, unknown proposals, and decision inputs owned by that Stage.

The producer must not grant its own continuation authority.

Caller-authored fields equivalent to the following are untrusted assertions:

```text
stage_status
quality_checks
next_stage
canonical_payload_valid
legacy_export_substituted
build_tree_digest
implementation_tree_digest
```

Only `evaluate_stage` derives the authoritative values.

A serialized Stage Result may remain readable as:

- a human-facing summary;
- a resume hint;
- a compatibility record;
- a fixture;
- a diagnostic artifact.

It cannot authorize continuation unless the runtime can recompute the decision from the corresponding Stage Output and Run State.

## User-facing Stage claim truth

A Stage heading is not a Stage Result. Narrative output is not a canonical Artifact, and a same-context self-audit is not independent review.

Visible Stage claims must follow these rules:

- When no valid evaluator-derived Stage Result exists, report `stage_status: not_evaluated` and `claim_basis: reasoning_output_only`.
- `not_evaluated` is presentation-only. It is not added to the canonical `stage_status` enum and cannot authorize continuation.
- When a valid derived Stage Result exists, display the canonical `stage_status`, `evaluation_mode`, and `evaluated_stage_output_digest` from that result.
- `model_assessed` means structured runtime assessment. It is not independent or deterministic repository proof.
- `validator_backed` means the active runtime invariants for that Stage were checked. It does not imply that an optional full Validation Transaction, Receipt, or independent regeneration ran.
- `external_boundary_verified` may be reported as passed only when the derived terminal result contains the actual `project_gate_export` evidence, including source payload digest, export digest, validator identity, validation result, and export identity.
- Bare words such as `PASS`, `COMPLETE`, `LOCKED`, `VALIDATED`, `HANDOFF READY`, or equivalent Persian claims must not be used as execution claims without the corresponding evaluator-derived evidence.

Multiple reasoning-only or model-assessed Stages may continue in one response when the Manifest and evaluator permit it. The claim truth rule changes reporting only; it does not add a Stage, turn boundary, approval layer, or parallel orchestration system.

## Minimal data separation

### Stage Output

The actual domain work and structured Stage-owned assessment evidence.

### Stage Result

The derived decision:

```yaml
run_id:
stage_id:
stage_status: pass | needs_input | blocked
quality_checks:
blocking_issues:
carried_unknowns:
next_stage:
evaluation_mode:
evaluated_stage_output_digest:
```

### Run State

Only the state required for pipeline correctness:

```yaml
run_id:
current_stage:
completed_stages:
unknown_ledger:
selected_candidate_id:
selected_candidate_locked:
build_tree_digest:
implementation_digest:
```

No event store, approval model, evidence graph, receipt chain, capability system, or governance state machine is required.

## Status semantics

```yaml
pass:
  meaning: all finite Stage checks passed and no blocker remains
  next_stage: exact Manifest successor or null for the terminal Stage

needs_input:
  meaning: minimum architecture-changing or required-evidence input is missing
  next_stage: null
  blocking_issues: non-empty

blocked:
  meaning: a genuine quality, evidence, fidelity, or final-handoff defect remains
  next_stage: null
  blocking_issues: non-empty
```

Optional repository-audit evidence cannot create `needs_input` or `blocked` by itself.

## Research disposition

`/research` remains mandatory and records exactly one active disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

`existing_evidence_sufficient` and `no_platform_question` are valid passing outcomes. External lookup metadata is not required when no platform-capability claim needs active research.

## Finite Stage checks

The Pipeline Manifest owns the recognized check inventory for each Stage. The evaluator rejects missing, unknown, cross-Stage, failed, unresolved, or improperly `not_applicable` checks.

For analytical Stages, structured model assessment may support the checks. This is labeled honestly and is not independent or deterministic proof.

## Unknown lifecycle

Active unknowns live in Run State and cannot disappear through omission.

Ordinary resolution requires an explicit type and explanatory note. A resolvable evidence reference is mandatory only when the unknown is downstream-critical or Artifact-dependent.

An arbitrary non-empty string cannot close a downstream-critical unknown.

## Candidate and fidelity state

After `/recommend`, the evaluator locks `selected_candidate_id`. Downstream Stages must preserve it unless a legitimate partial rerun reaches `/recommend` or an earlier Stage.

For `/build-tree` and `/implementation`, canonical content means the existing structured Stage Output. Do not create a wrapper Artifact solely to compute a digest.

The evaluator computes digests from actual canonical content and rejects:

- missing canonical content;
- `null == null` fidelity;
- caller-fabricated digest strings;
- an Implementation that does not contain the approved Build Tree content.

Conversational Stage output does not require a digest.

## Final Project Gate boundary

The terminal `/project-gate-export` result is derived from the actual Architect Stage Payload and actual Producer Gate export through the existing canonical validator and exporter chain.

A terminal result records the derived payload digest, export digest, validator identity, validation result, and export identity.

Caller-controlled success Booleans cannot substitute for actual validation.

## Resume and partial rerun

Resume uses the smallest available mechanism. When Stage Output and Run State are present, evaluate them directly. Do not introduce a database, immutable receipt, external registry, or content-addressable store solely for resume.

Partial rerun starts at the earliest affected Stage, invalidates dependent downstream results, reactivates unknowns whose resolutions depended on invalidated work, and preserves or invalidates candidate lock according to Stage ownership.

## Optional audit tooling boundary

Stage Anchor, Validation Receipt, Boundary Record, Failure Event, Validation Bundle, independent regeneration, exact-head CI, and PR review remain optional repository-development or historical tooling. Their absence does not prevent a valid project Run.

## Compatibility

Historical `ev4-architect-stage-result@1.0.0` records remain schema-readable as informational evidence. The evaluator always emits the stronger derived fields. Historical records do not acquire continuation authority.

The Pipeline Manifest remains the sole authority for Stage inventory, order, versions, successor edges, and terminal identity.

The final Architect → Project Gate boundary remains fail-closed under the canonical Architect Stage Payload and Producer Gate Export contracts.
