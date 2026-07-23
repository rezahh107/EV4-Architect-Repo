# Project Instructions — Active Overrides

Status: active  
Version: 0.10.0  
Applies to: current EV4 Architect Project Instructions and release-pack mirrors

## Authority

Read and apply first:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
contracts/ARCHITECT_STAGE_RESULT_V1.md
contracts/ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1.md
manifests/architect-pipeline-manifest.v1.json
scripts/architect_quality_runtime.py#evaluate_stage
scripts/architect_stage_claim_guard.py
```

This file supersedes only authorization-driven continuation clauses in older instructions and mirrors. All non-conflicting quality controls remain active.

## Normal Run Continuation

```text
model-authored Stage content and check claims
+ evaluator-owned Run State
+ Runtime-owned RunContext
→ conversational Base Schema
→ Stage Claim Guard
→ evaluator-derived Stage Result
→ exact Manifest successor, minimum input, or repair route
```

`ev4-architect-stage-result@1.0.0` remains the active result identity. The Runtime derives `stage_status`, `completion_class`, check outcomes, blocking issues, Candidate lock, Unknown ledger, digests, continuation, terminal Payload, synthetic status, and handoff.

A model-authored or serialized Stage Result is readable but non-authorizing. Resume recomputes from Stage Output and Run State. Do not create a persistent store, receipt chain, or second Pipeline for resume.

A Stage must not stop solely because an Anchor, Validation Bundle, independent regeneration, exact-head CI, PR review, Merge evidence, or repository maintenance is absent.

## Completion truth

```yaml
reasoning_complete:
  applies_to:
    - /intake
    - /research
    - /decompose
    - /architectures
    - /score-evidence
  meaning: required structure and deterministic consistency passed
  not_claimed: objective correctness of model reasoning

validated_pass:
  applies_to:
    - /score-audit
    - /recommend
    - /build-tree
    - /implementation
    - /final-audit
    - /handoff-export
    - /project-gate-export
  meaning: consequential Runtime predicates or the external boundary passed
```

The Stage Claim Guard owns this distinction inside the existing evaluator. It is not a second evaluator or Stage inventory.

## User-Facing Stage Claim Truth

A Stage heading is not a Stage Result. Before using `PASS`, `COMPLETE`, `LOCKED`, `VALIDATED`, `HANDOFF READY`, or an equivalent Persian execution claim:

1. obtain the evaluator-derived Stage Result;
2. display `stage_status`;
3. display `completion_class`;
4. display `evaluation_mode`;
5. display `evaluated_stage_output_digest`.

Without a derived result, report only:

```yaml
stage_status: not_evaluated
claim_basis: reasoning_output_only
```

`reasoning_complete` is honest bounded completion, not machine proof of analytical quality. `external_boundary_verified` requires actual Runtime-issued Payload and Project Gate export evidence.

## Research Requirement

`/research` remains mandatory. Record exactly one disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

`existing_evidence_sufficient` and `no_platform_question` are valid. Research does not recommend architecture, convert unknown evidence into fact, or treat platform capability as project-specific behavior.

## Finite Stage Checks

The Pipeline Manifest owns the exact required check keys. Every required key has one explicit evaluation basis:

```text
DETERMINISTIC_PREDICATE
STRUCTURAL_COMPLETENESS
ATTRIBUTED_REASONING_ONLY
EXTERNAL_BOUNDARY
```

Model-facing `check_evidence` contains a non-authorizing `claim` and `reason`. Legacy `result` may parse but is ignored and reported in `legacy_check_results_ignored`.

The Runtime rejects missing or unknown check claims, Base-Schema defects, failed derived predicates, unresolved blockers, non-successor continuation, hidden recommendation, Candidate drift, invented exact values, and invalid terminal evidence.

## Partial Rerun

Use the latest valid Stage Output and current Run State. Start at the earliest affected Stage, invalidate dependent outputs and results, reactivate affected Unknowns, and invalidate Candidate lock only when rerun reaches `/recommend` or earlier.

Do not require an Anchor, Bundle, cryptographic rerun receipt, or event ledger.

## Unknown Lifecycle

An active Unknown cannot disappear by omission. Ordinary resolution requires an explicit type and note. A downstream-critical resolution also requires an evidence reference present in `RunContext.verified_evidence_refs`; a caller string alone is not verified evidence.

## Mandatory Pipeline

```text
/intake
/research
/decompose
/architectures
/score-evidence
/score-audit
/recommend
/build-tree
/implementation
/final-audit
/handoff-export
/project-gate-export
```

No visual-to-Build-Tree shortcut or non-successor continuation is allowed.

## Scoring and Recommendation

`/score-evidence` preserves evidence state and must not hide a recommendation. `/score-audit` must recompute internal consistency. `/recommend` proposes a Candidate only after accepted audit; Runtime verifies that Candidate against prior architecture and audit outputs and establishes the lock.

## Fidelity and Final Audit

For `/build-tree` and `/implementation`, canonical content is the existing structured Stage Output. Runtime derives Build Tree and Implementation digests and compares the embedded approved Build Tree.

`/final-audit` acceptance is derived from actual findings, required audit scope, Candidate lock, Implementation fidelity, and active critical Unknowns. A model-authored acceptance string or check result cannot grant pass.

## Handoff and Project Gate Boundary

`/handoff-export` carries presentation/package content; Runtime derives eligibility from accepted Final Audit, Candidate lock, required outputs, fidelity, and Unknown ledger.

`/project-gate-export` must not contain `project_gate_payload`. The official path is:

```text
evaluated Stage Outputs
+ derived Stage Results
+ Run State
+ Runtime-owned RunContext
→ Runtime Payload Assembler
→ ev4-architect-stage-payload@1.0.0
→ existing Schema and semantic validation
→ actual checkout provenance
→ existing Producer Gate exporter
→ contract and digest verification
→ Runtime-derived handoff
```

`RunContext.source_kind` is one of `live_conversation`, `fixture`, `example`, or `test_vector`. Runtime derives `synthetic = source_kind != live_conversation`. Synthetic contexts may report `functional_eligibility.would_allow`, but actual handoff remains denied. The model cannot author `RunContext`, producer provenance, terminal Payload, synthetic status, or handoff status.

## Optional Audit Tooling

Stage Anchors, Receipts, Boundary Records, Failure Events, Validation Bundles, Validation Profiles, independent regeneration, and `authorization_valid` remain optional repository-audit tooling. They do not authorize ordinary Stage movement.

## Conversational Stage Output Emission

<!-- BEGIN ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->
After completing each Stage, produce one complete standalone Runtime-compatible Stage Output JSON artifact for that Stage.

Use contract `ev4-architect-conversational-stage-output@1.0.0` and base Schema `ev4-architect-conversational-stage-output-base@1.0.0`. The JSON is model-authored evaluator input, not an evaluator-derived Stage Result.

Use the exact `run_id`, Manifest `stage_id`, Manifest `stage_version`, and exact Manifest-owned `check_evidence` keys. Each check record carries a non-authorizing `claim` and `reason`; do not author an official check result. Preserve complete Stage-specific canonical content, active Unknowns, and the locked Candidate. A summary must not replace canonical content.

Do not author official `PASS`, `stage_status`, `quality_checks`, `completion_class`, `next_stage`, continuation authority, official digests, `RunContext`, `source_kind`, authoritative `synthetic`, producer provenance, or `project_gate_payload`. At `/project-gate-export`, request export only; the Runtime assembles the official terminal Payload from the evaluated Run.

Emit one separate Stage Output artifact per Stage. A later Stage artifact must not replace or modify an earlier artifact. Until the official Runtime evaluates an artifact, any presentation label is only `stage_status: not_evaluated` with `claim_basis: model_authored_stage_output_only` and is non-authorizing.

Prefer an actual UTF-8 `.json` attachment. When attachment creation is unavailable, return one exact JSON code block, provide an explicit proposed filename, and state truthfully that no attachment was created.
<!-- END ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->
