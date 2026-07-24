# Architect Stage Result v1

Status: active  
Schema: `ev4-architect-stage-result@1.0.0`  
Schema path: `schemas/ev4-architect-stage-result.v1.schema.json`

## Purpose

`Stage Result` is an evaluator-derived normal-run record. It reports whether one logical Stage met its Runtime-owned completion predicates and whether the exact Manifest successor may run.

```text
model-authored Stage Output
+ evaluator-owned Run State
+ Runtime-owned RunContext
+ Manifest-owned Stage/check identity
→ conversational Base Schema
→ scripts/architect_stage_claim_guard.py
→ scripts/architect_quality_runtime.py#evaluate_stage
→ derived Stage Result
→ exact successor, minimum input, or repair route
```

A Stage Result is not a repository authorization ticket. It does not require an Anchor, Bundle, independent regeneration, exact-head CI, PR review, Merge evidence, or repository maintenance.

## Authority boundary

The Stage producer may provide Stage-owned canonical content, non-authorizing check claims, explicit blockers, Unknown proposals, and Stage-owned decision inputs.

The producer must not grant its own continuation authority. Caller-authored equivalents of any Stage Result property, nested `decision_state`, `runtime_context`, `project_gate_export` property, terminal Payload, Runtime Context, synthetic status, producer provenance, or legacy success/digest alias are forbidden at Stage Output top level.

Only `evaluate_stage` derives authoritative values. Runtime and conversational Base Schema share one Schema-derived forbidden set; drift is executable failure.

A serialized Stage Result remains readable as a summary, resume hint, compatibility record, fixture, or diagnostic. It cannot authorize continuation unless Runtime recomputes from Stage Output and Run State.

## User-facing Stage claim truth

A Stage heading is not a Stage Result.

A same-context self-audit is not independent review.

Without a valid derived Stage Result, report only:

```yaml
stage_status: not_evaluated
claim_basis: reasoning_output_only
```

With a derived result, display:

```yaml
stage_status:
completion_class:
evaluation_mode:
evaluated_stage_output_digest:
```

Interpret precisely:

- `reasoning_complete`: required structure and deterministic consistency passed; objective correctness of model reasoning is not proven.
- `validated_pass`: consequential deterministic predicates or the external boundary passed.
- `model_assessed`: Stage contains analytical work; this is not independent proof.
- `validator_backed`: active deterministic Runtime invariants were checked.
- `external_boundary_verified`: actual Runtime-issued Payload and Producer Gate export were validated.

Bare `PASS`, `COMPLETE`, `LOCKED`, `VALIDATED`, or `HANDOFF READY` claims are forbidden without the corresponding derived evidence.

## Data separation

### Stage Output

Actual domain work and non-authorizing check claims:

```yaml
check_evidence:
  manifest_check_key:
    claim:
    reason:
    evidence_refs: optional
    limitations: optional
```

Legacy `result` may parse for migration but is ignored. Runtime reports ignored keys in `runtime_context.legacy_check_results_ignored`.

### Stage Result

```yaml
run_id:
stage_id:
stage_version:
stage_status: pass | needs_input | blocked
completion_class: reasoning_complete | validated_pass
quality_check_basis:
quality_checks:
blocking_issues:
carried_unknowns:
next_stage:
decision_state:
runtime_context:
project_gate_export:
evaluation_mode:
evaluated_stage_output_digest:
```

### Run State

One small evaluator-owned state model:

```yaml
run_id:
current_stage:
completed_stages:
unknown_ledger:
selected_candidate_id:
selected_candidate_locked:
build_tree_digest:
implementation_digest:
evaluated_stage_outputs:
derived_stage_results:
```

The evaluated-output/result history is the bounded source for terminal Payload assembly and partial rerun. It is not a second Pipeline, database, event store, receipt chain, evidence graph, or approval model.

### RunContext

```yaml
source_kind: live_conversation | fixture | example | test_vector
verified_evidence_refs: host-verified references
synthetic: derived, not stored as caller input
```

The model cannot author RunContext. Runtime derives `synthetic = source_kind != live_conversation`.

## Status semantics

```yaml
pass:
  meaning: derived predicates passed and no blocker remains
  next_stage: exact Manifest successor or null for terminal

needs_input:
  meaning: minimum architecture-changing or required-evidence input is missing
  next_stage: null

blocked:
  meaning: Base-Schema, predicate, evidence, fidelity, or terminal defect remains
  next_stage: null
```

Optional repository-audit evidence cannot create `needs_input` or `blocked` by itself.

## Completion classes

Reasoning stages:

```text
/intake
/research
/decompose
/architectures
/score-evidence
```

They may derive `reasoning_complete` when required content exists, identity/Unknown rules hold, forbidden decisions are absent, and no deterministic contradiction exists.

Consequential stages:

```text
/score-audit
/recommend
/build-tree
/implementation
/final-audit
/handoff-export
/project-gate-export
```

They derive `validated_pass` only from explicit Runtime predicates or the external boundary.

## Finite Stage checks

The Pipeline Manifest owns exact check keys. The Stage Claim Guard owns one explicit basis per key:

```text
DETERMINISTIC_PREDICATE
STRUCTURAL_COMPLETENESS
ATTRIBUTED_REASONING_ONLY
EXTERNAL_BOUNDARY
```

No required check is defined as a model-supplied pass. A claim/reason is explanatory input; it never becomes official `quality_checks` merely by being non-empty.

## Research disposition

`/research` records one of:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

The first three may pass. External lookup receipts are not required when no platform-capability claim needs active lookup.

## Unknown lifecycle

Active Unknowns persist in Run State. Omission is not resolution.

Ordinary resolution requires explicit type and note. A downstream-critical resolution additionally requires an evidence reference present in `RunContext.verified_evidence_refs`; a caller-authored string is not verified evidence by itself.

## Candidate and fidelity state

At `/recommend`, Runtime verifies the proposed Candidate exists in prior architecture and audited eligible sets before locking it.

At `/build-tree`, Runtime verifies canonical root/node content, Candidate preservation, and architecture-drift absence, then derives Build Tree identity.

At `/implementation`, Runtime requires an embedded approved Build Tree, compares it with the prior canonical tree, and derives Implementation identity.

Caller-fabricated digest fields, missing content, Candidate drift, or approved-tree mismatch block pass.

## Final Audit and handoff

The model provides findings; Runtime derives Final Audit acceptance from required audit scope, severe-finding absence, Candidate lock, Implementation fidelity, and active critical Unknowns.

At `/handoff-export`, Runtime derives eligibility from accepted Final Audit, Candidate lock, required outputs, fidelity, and Unknown ledger.

## Final Project Gate boundary

The `/project-gate-export` Stage Output contains only a non-authoritative export request or presentation note. Caller-supplied `project_gate_payload` is rejected.

```text
evaluated Stage Outputs
+ derived Stage Results
+ Run State
+ RunContext
→ Runtime Payload Assembler
→ ev4-architect-stage-payload@1.0.0
→ existing Schema and semantic validation
→ producer provenance from actual Git checkout
→ existing Producer Gate exporter
→ contract and digest verification
→ Runtime-derived handoff
```

The terminal `project_gate_export` records:

```yaml
canonical_payload_valid:
legacy_export_substituted:
source_payload_digest:
export_digest:
validator_identity:
validation_result:
export_id:
runtime_issued_payload:
functional_eligibility:
  would_allow:
  blockers:
execution_context:
  source_kind:
  synthetic:
handoff_allowed:
```

Synthetic fixtures/examples/test vectors may have `would_allow: true`, but `handoff_allowed` remains false. A valid `live_conversation` context may reach allowed handoff.

Caller-controlled success Booleans, Payloads, synthetic values, provenance mappings, or digests cannot substitute for Runtime derivation.

## Resume and partial rerun

Resume uses the smallest available Stage Output and Run State. Partial rerun starts at the earliest affected Stage, invalidates dependent outputs/results, reactivates affected Unknowns, and preserves or invalidates Candidate lock according to Stage ownership.

Do not introduce a database, external registry, immutable receipt, or content-addressable store solely for resume.

## Optional audit tooling boundary

Anchor, Receipt, Boundary, Failure Event, Validation Bundle, independent regeneration, exact-head CI, and PR review remain optional repository-development or historical tooling. Their absence does not prevent a valid normal Run.

## Compatibility

Historical `ev4-architect-stage-result@1.0.0` records remain schema-readable as informational evidence. New optional derived fields strengthen current Runtime truth without making historical records authoritative.

The Pipeline Manifest remains the sole authority for Stage inventory, order, versions, successor edges, and terminal identity.

The Architect producer still emits `ev4-architect-stage-payload@1.0.0`; the correction changes how Runtime creates it, not its canonical consumer contract. Cross-repository consumer compatibility is not established until each consumer implements and tests the new Runtime entry points and terminal semantics.
