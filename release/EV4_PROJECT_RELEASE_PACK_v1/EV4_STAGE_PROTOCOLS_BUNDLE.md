# EV4 Stage Protocols Bundle

Status: release_candidate_quality_first_runtime  
Version: 1.4.0

## Common Runtime Protocol

```text
model-authored Stage content and check claims
+ evaluator-owned Run State
+ Runtime-owned RunContext
→ conversational Base Schema
→ scripts/architect_stage_claim_guard.py
→ scripts/architect_quality_runtime.py#evaluate_stage
→ evaluator-derived Stage Result
→ pass | needs_input | blocked
```

A serialized Stage Result is readable but non-authorizing. Stage Anchors, Validation Bundles, independent regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, and repository maintenance are not ordinary continuation prerequisites.

The Pipeline Manifest owns exact Stage/check keys. Model check records carry non-authorizing `claim` and `reason`; legacy `result` is ignored. The Stage Claim Guard derives every check outcome from an explicit evaluation basis.

Reasoning Stages use `completion_class: reasoning_complete`; this is bounded structural and consistency completion, not objective proof of reasoning quality. Consequential Stages and the terminal boundary use `completion_class: validated_pass` only after deterministic predicates pass.

## Conversational Stage Output Emission

<!-- BEGIN ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->
After completing each Stage, produce one complete standalone Runtime-compatible Stage Output JSON artifact for that Stage.

Use contract `ev4-architect-conversational-stage-output@1.0.0` and base Schema `ev4-architect-conversational-stage-output-base@1.0.0`. The JSON is model-authored evaluator input, not an evaluator-derived Stage Result.

Use the exact `run_id`, Manifest `stage_id`, Manifest `stage_version`, and exact Manifest-owned `check_evidence` keys. Each check record carries a non-authorizing `claim` and `reason`; do not author an official check result. Preserve complete Stage-specific canonical content, active Unknowns, and the locked Candidate. A summary must not replace canonical content.

Do not author official `PASS`, `stage_status`, `quality_checks`, `completion_class`, `next_stage`, continuation authority, official digests, `RunContext`, `source_kind`, authoritative `synthetic`, producer provenance, or `project_gate_payload`. At `/project-gate-export`, request export only; the Runtime assembles the official terminal Payload from the evaluated Run.

Emit one separate Stage Output artifact per Stage. A later Stage artifact must not replace or modify an earlier artifact. Until the official Runtime evaluates an artifact, any presentation label is only `stage_status: not_evaluated` with `claim_basis: model_authored_stage_output_only` and is non-authorizing.

Prefer an actual UTF-8 `.json` attachment. When attachment creation is unavailable, return one exact JSON code block, provide an explicit proposed filename, and state truthfully that no attachment was created.
<!-- END ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->

## /intake — reasoning_complete

Capture usable input, constraints, explicit Unknown introductions, and minimum blocking questions.

Deterministic boundaries: required `input_basis` exists; no Candidate or architecture is selected; unavailable exact values are not declared known.

Forbidden: architecture selection, scoring, recommendation, Build Tree, invented exact values.

`pass → /research`.

## /research — reasoning_complete

Record one canonical disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

The first three may pass. Research does not decide project-specific architecture, score Candidates, recommend, or convert unsupported claims into exact facts.

`pass → /decompose`.

## /decompose — reasoning_complete

Preserve separate observations, inferences, and explicit Unknowns. Do not select implementation or architecture.

`pass → /architectures`.

## /architectures — reasoning_complete

Provide distinct Candidate identities, architecture families, and explicit coverage. Do not select a winner. Coverage quality remains attributed reasoning; Candidate shape and absence of recommendation are Runtime-checkable.

`pass → /score-evidence`.

## /score-evidence — reasoning_complete

Represent every prior Candidate with structured coverage and evidence state. Do not hide a recommendation or turn unknown evidence into numeric fact.

`pass → /score-audit`.

## /score-audit — validated_pass

Runtime checks accepted audit status, material-defect absence, internal Candidate identity consistency, and rubric-set integrity. A model-authored `pass` cannot grant acceptance.

`pass → /recommend`.

## /recommend — validated_pass

The model proposes one Candidate. Runtime verifies it exists in both the architecture set and the audited eligible set, then establishes Candidate lock.

Forbidden: re-scoring, new architecture, Build Tree, implementation, invented exact values.

`pass → /build-tree`.

## Unknown Lifecycle

Active Unknowns persist in Runtime Run State. Omission is not resolution. Downstream-critical resolution requires an evidence reference present in `RunContext.verified_evidence_refs`; a caller string alone is not verified evidence.

## /build-tree — validated_pass

Translate the locked Candidate into canonical structured Build Tree content. Runtime verifies Candidate preservation, root/node structure, architecture-drift absence, and computes the Build Tree digest from actual content.

`pass → /implementation`.

## /implementation — validated_pass

Map the approved tree to implementation content. Runtime requires the embedded approved Build Tree, compares its digest with the prior canonical tree, and computes Implementation identity.

`pass → /final-audit`.

## /final-audit — validated_pass

The model provides findings. Runtime derives acceptance from required audit scope, absence of blocker/high findings, Candidate lock, Implementation fidelity, and active downstream-critical Unknowns.

`pass → /handoff-export`.

## /handoff-export — validated_pass

Package accepted outputs without adding decisions. Runtime derives eligibility from accepted Final Audit, Candidate lock, required Build/Implementation identities, no critical Unknowns, and preserved final-audit reference.

`pass → /project-gate-export`.

## /project-gate-export — validated_pass

The conversational Stage Output contains only a non-authoritative export request or presentation note. Caller-supplied `project_gate_payload`, `synthetic`, producer provenance, success Booleans, digests, or handoff status are forbidden.

```text
evaluated Stage Outputs
+ derived Stage Results
+ Run State
+ RunContext
→ Runtime Payload Assembler
→ ev4-architect-stage-payload@1.0.0
→ existing Schema and semantic validation
→ producer provenance from the actual checkout
→ existing Producer Gate exporter
→ contract and digest verification
→ Runtime-derived handoff
```

`RunContext.source_kind` is `live_conversation`, `fixture`, `example`, or `test_vector`. Runtime derives synthetic state. Synthetic contexts may report business `would_allow`, but actual handoff remains false. This is terminal.

## Partial Rerun

Use the earliest affected Stage. Invalidate dependent outputs/results, preserve unaffected Run State, reactivate affected Unknowns, and invalidate Candidate lock only when rerun reaches `/recommend` or earlier.

## Resume

Use the smallest available Stage Output and Run State. Do not create persistent storage, immutable receipts, content-addressable storage, or Artifact registries solely for resume.

## Optional Audit Tooling

Deterministic Artifact, Receipt, Boundary, Failure Event, Anchor, and Bundle transactions remain optional repository-audit and regression tools. They do not authorize ordinary Stage movement.
