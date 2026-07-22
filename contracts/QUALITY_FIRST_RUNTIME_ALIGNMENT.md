# Quality-First Architect Runtime Alignment

Status: active_canonical_alignment  
Version: 1.1.0  
Applies to: normal user-facing EV4 Architect Runs

## Authority and precedence

This contract defines normal-run continuation semantics. It supersedes only clauses that make internal authorization carriers, repository workflow evidence, or Validation Profile completeness prerequisites for ordinary Stage continuation.

All controls that materially protect evidence quality, scoring, candidate selection, unknown lifecycle, architecture fidelity, Final Audit, and the final Project Gate handoff remain active.

Machine-readable authority:

```text
Stage topology, order, versions, successor, and terminal identity
→ manifests/architect-pipeline-manifest.v1.json

Canonical continuation evaluator
→ scripts/architect_quality_runtime.py#evaluate_stage

Derived Stage Result shape
→ ev4-architect-stage-result@1.0.0

Optional deterministic transaction capability
→ manifests/architect-stage-validation-profiles.v1.json

Final Architect → Project Gate handoff
→ canonical Architect Stage Payload and Producer Gate Export contracts
```

## Selected runtime architecture

```text
Stage Output
+ current Run State
+ fixed Stage rules
→ evaluate_stage
→ evaluator-derived Stage Result
+ updated Run State
+ exact Manifest continuation decision
```

Stage quality determines progression.

A caller-authored or serialized Stage Result is not continuation authority. A serialized Stage Result remains readable as a summary, resume hint, compatibility record, fixture, or diagnostic artifact, but the runtime must recompute the decision from the corresponding Stage Output and Run State.

There is one pipeline, one Stage order, one continuation evaluator, and one final fail-closed Project Gate boundary. No alternative lean, strict, enterprise, legacy, or feature-flagged runtime is introduced.

## Small data model

### Stage Output

Contains the actual domain work produced by the Stage and structured assessment evidence for that Stage.

### Stage Result

Contains only the evaluator-derived decision, including:

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

Contains only state required for pipeline correctness:

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

Do not add a general event store, evidence graph, immutable receipt chain, capability system, approval model, or repository-governance state machine.

## Stage Result semantics

```yaml
pass:
  blocking_issues: []
  next_stage: exact Manifest successor or null for the terminal Stage

needs_input:
  blocking_issues: minimum architecture-changing or required-evidence question
  next_stage: null

blocked:
  blocking_issues: genuine quality, evidence, fidelity, or final-handoff defect
  next_stage: null
```

A Stage Result never becomes authoritative merely because it conforms to JSON Schema. The schema preserves historical readability; `evaluate_stage` remains the sole active continuation-decision authority.

## Internal carrier migration

```yaml
stage_anchor:
  active_runtime_role: optional_resume_checkpoint
  authorization_role: none
  required_for_internal_continuation: false

validation_bundle:
  active_runtime_role: none
  authorization_role: none
  optional_roles:
    - repository_audit_tool
    - compatibility_evidence
    - deterministic_validator_regression

validation_profiles_registry:
  active_runtime_role: none
  authorization_role: validation_capability_only
  full_transaction_implemented_required_for_normal_run: false
```

Receipt, Boundary, Failure Event, Anchor, Bundle, independent regeneration, and `authorization_valid` remain optional historical or repository-audit tooling. They do not authorize ordinary Stage movement.

The following cannot block a normal Run by themselves:

```text
Anchor missing
Validation Bundle missing
independent regeneration not executed
Validation Profile not full_transaction_implemented
profile status blocked_missing_semantics
exact-head CI unavailable
PR review unavailable
Merge evidence unavailable
repository reconciliation pending
repository maintenance not performed
```

## Required Stage order

```text
/intake
→ /research
→ /decompose
→ /architectures
→ /score-evidence
→ /score-audit
→ /recommend
→ /build-tree
→ /implementation
→ /final-audit
→ /handoff-export
→ /project-gate-export
```

No mandatory logical Stage may be skipped. Continuation to a non-successor Stage is invalid.

## Research no-op completion

`/research` remains a mandatory logical Stage, but active external lookup is conditional.

The evaluator supports exactly these runtime dispositions:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

`existing_evidence_sufficient` and `no_platform_question` are valid passing outcomes. A normal Run must not be blocked merely because no external lookup was necessary.

Do not require citations, URLs, retrieval metadata, source receipts, or repository-maintenance evidence when no platform-capability claim requires active research.

Research still enforces:

```text
platform capability ≠ project-specific behavior
official documentation does not decide visual interpretation
research does not score or recommend architecture
unsupported claims remain unknown
version-sensitive claims require version-aware evidence
```

## Minimal Stage check authority

The Pipeline Manifest owns one finite list of recognized checks for each Stage. Do not duplicate the same check inventory in another registry.

The evaluator rejects:

- a missing required check;
- an unknown check;
- a check owned by another Stage;
- a failed or unresolved required check;
- forbidden `not_applicable`;
- unresolved blockers;
- a non-successor continuation.

For conversational Stages, structured model assessment may establish the check evidence. This is runtime assessment, not deterministic repository proof or independent evidence.

## Minimal unknown lifecycle

Active unknowns live in Run State and persist until the evaluator accepts an explicit resolution. Omission from a later Stage Output is not resolution.

Ordinary resolution requires:

```yaml
unknown_id:
resolution_type: user_confirmation | authoritative_source | validated_artifact | not_applicable
note:
resolved_at_stage:
evidence_ref: optional
```

A resolvable evidence reference is required only for downstream-critical or Artifact-dependent unknowns. An arbitrary string cannot close such an unknown.

Do not add a generalized typed-evidence framework, cross-run evidence graph, chained hash, immutable resolution receipt, or general transition-event schema.

## Candidate lock

After `/recommend`, the evaluator establishes and preserves the selected candidate identity. Downstream Stages cannot substitute, remove, or silently unlock it.

A partial rerun invalidates the lock only when the earliest affected Stage is `/recommend` or earlier.

## Canonical content and digest boundary

For `/build-tree` and `/implementation`, an Artifact means the existing canonical structured output owned by that Stage. It may be an existing JSON object, structured Stage Output, or another already-defined repository representation.

Do not create a wrapper Artifact, receipt, registry, or storage layer merely to compute a digest.

```text
no real canonical content
→ no claimed Artifact digest
```

The evaluator computes:

- the Build Tree digest from actual canonical Build Tree content;
- the Implementation digest from actual canonical Implementation content;
- the approved-tree comparison from the actual embedded Build Tree content.

It must reject `null == null`, equal fabricated digest strings, or caller-authored SHA-like values without corresponding content.

Ordinary conversational questions, prose, reasoning summaries, and analytical Stage output do not require cryptographic identity.

## Resume behavior

Resume validation uses the smallest available mechanism.

When Stage Output and Run State are already present in the active conversation or runtime object, evaluate them directly. If they are unavailable, request or regenerate only the minimum missing material.

Do not introduce persistent databases, content-addressable storage, external registries, immutable receipts, or new Artifact stores solely to resume a Run.

## Partial rerun

A partial rerun must identify the earliest affected Stage, invalidate dependent downstream results, preserve unaffected state, reactivate unknowns whose resolutions depended on invalidated work, and preserve or invalidate candidate lock according to Stage ownership.

Do not require Anchor, Bundle, independent rerun authorization, cryptographic rerun receipts, or chained invalidation proofs.

## Quality invariants preserved

The active runtime continues to enforce:

- lightweight `/intake` with only blocking or architecture-changing questions;
- no direct screenshot-to-Build-Tree path;
- observation versus inference separation;
- architecture-family coverage before scoring;
- evidence-backed scoring and `?` for missing evidence;
- no hidden recommendation or numeric conversion of unknowns;
- accepted `/score-audit` before `/recommend`;
- immutable selected candidate after lock;
- Build Tree and Implementation fidelity;
- persistent unknown lifecycle;
- blocker/high Final Audit findings prevent handoff;
- unresolved downstream-critical unknowns prevent final handoff.

## Final Project Gate boundary

The final Project Gate boundary remains fail-closed.

A terminal pass is derived only from:

```text
actual canonical Architect Stage Payload
→ existing Schema and semantic validator
→ selected-candidate consistency check
→ existing Producer Gate exporter
→ actual canonical export
→ contract and digest verification
→ derived terminal Stage Result
```

Caller-controlled values such as `canonical_payload_valid: true` or `legacy_export_substituted: false` are informational assertions only and cannot authorize success.

Preserve canonical payload validation, semantic validation, locked identity, canonical serialization, provenance, digest integrity, invalid-payload rejection, and legacy-output non-substitution.

## Test migration rule

Before changing an existing test, classify it as:

```yaml
preserved_quality_invariant:
obsolete_runtime_authorization_expectation:
historical_compatibility:
unrelated:
```

A test may be updated or retired only when it specifically asserts a runtime requirement intentionally removed by this repair.

Do not weaken tests protecting Stage order, evidence discipline, candidate locking, unknown preservation, Build Tree/Implementation fidelity, Final Audit, or Project Gate validation.

For changed authorization tests, replacement coverage must prove that the removed Anchor/Bundle/CI/review requirements no longer block normal runtime operation while the quality invariant remains protected.

## Repository repair separation

Tests, CI, exact revision identity, and independent review may validate the code change in PR #36. They are development-quality controls and do not become Architect runtime prerequisites.

Routine Stage failure returns a Run repair route. It does not automatically require repository repair.

## Validation boundary

Repository tests may prove deterministic contract behavior at an exact revision. They do not prove real ChatGPT host enforcement, live Elementor rendering, browser/device validity, downstream acceptance, release readiness, or production readiness.
