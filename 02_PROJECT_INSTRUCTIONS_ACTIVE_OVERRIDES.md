# Project Instructions — Active Overrides

Status: active  
Version: 0.8.0  
Applies to: current EV4 Architect Project Instructions and release-pack mirrors

## Authority

Read and apply first:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
contracts/ARCHITECT_STAGE_RESULT_V1.md
manifests/architect-pipeline-manifest.v1.json
scripts/architect_quality_runtime.py#evaluate_stage
```

This file supersedes only authorization-driven continuation clauses in `01_PROJECT_INSTRUCTIONS.md`, active Stage documents, hardening patches, source-access references, contracts, and release-pack mirrors. All non-conflicting quality controls remain active.

## Normal Run Continuation

Every Stage produces domain-specific Stage Output. One canonical evaluator combines it with current Run State and the finite Stage checks in the Pipeline Manifest:

```text
Stage Output + Run State + fixed Stage rules
→ evaluate_stage
→ evaluator-derived Stage Result
```

The derived result is compatible with:

```text
ev4-architect-stage-result@1.0.0
```

```yaml
pass:
  meaning: all Stage quality criteria are satisfied
  next_stage: exact Manifest successor

needs_input:
  meaning: minimum architecture-changing or required-evidence input remains
  next_stage: null

blocked:
  meaning: a genuine quality, evidence, fidelity, or final-handoff defect remains
  next_stage: null
```

A producer-authored or serialized Stage Result is readable but non-authorizing. Resume must resolve the smallest available corresponding Stage Output and Run State and recompute. Do not create a persistent store, immutable receipt, or Artifact registry solely for resume.

A Stage must not stop solely because:

```text
Stage Anchor is absent
Validation Bundle is absent
independent regeneration was not executed
Validation Profile is not full_transaction_implemented
exact-head CI is unavailable
PR review or Merge evidence is unavailable
repository maintenance is pending
```

The Pipeline Manifest remains authoritative for Stage order, legal successor, evaluation mode, and finite required checks. Stage quality determines continuation.

## Research Requirement

`/research` remains mandatory. Do not use `/intake → /decompose`.

Record exactly one disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

`existing_evidence_sufficient` and `no_platform_question` are valid passing outcomes. Do not require external citations, URLs, retrieval metadata, or source receipts when no platform-capability claim requires active lookup.

Only `blocked_by_missing_required_source` blocks, and only when a downstream decision genuinely depends on evidence that cannot be obtained.

Research continues to enforce:

- platform capability is not project-specific behavior;
- official documentation does not decide visual interpretation;
- research does not score or recommend architecture;
- unsupported and version-sensitive claims remain unknown.

## Finite Stage Checks

The evaluator rejects:

- a missing required check;
- an unknown or cross-Stage check;
- a failed or unresolved required check;
- forbidden `not_applicable`;
- an unresolved blocker;
- a non-successor continuation.

Conversational Stage checks may be supported by structured model assessment. This is not independent or deterministic repository proof.

## Partial Rerun

Use the latest valid Stage Output and current Run State.

Identify the earliest affected Stage, invalidate dependent downstream results, preserve unaffected state, reactivate unknowns whose resolutions depended on invalidated work, and invalidate candidate lock only when the rerun reaches `/recommend` or earlier.

Do not require Anchor, Bundle, independent rerun authorization, cryptographic rerun receipts, or a general rerun-event ledger.

## Unknown Lifecycle

An active unknown cannot disappear because a later Stage omits it.

Ordinary resolution requires an explicit type and explanatory note. A resolvable evidence reference is required only for downstream-critical or Artifact-dependent unknowns.

An arbitrary non-empty string cannot close a downstream-critical unknown.

Do not convert absent evidence into an exact value or numeric confidence.

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

`/score-evidence` uses the approved rubric, `?` for missing evidence, and `N/A` only when truly non-applicable. It must not hide a recommendation.

`/recommend` may run only after accepted `/score-audit` status equivalent to `pass` or `pass_with_minor_flags`, with no material defect.

After recommendation, `selected_candidate_id` is immutable unless a legitimate rerun reaches `/recommend` or earlier.

## Fidelity and Final Audit

For `/build-tree` and `/implementation`, canonical content means the existing structured Stage Output. Do not create a wrapper Artifact solely to compute a digest.

The evaluator computes digests from actual content and rejects missing content, fabricated SHA-like strings, `null == null`, candidate drift, and approved-tree mismatch.

Conversational Stage output does not require cryptographic identity.

`/final-audit` blocks handoff for at least:

```text
blocker finding
high-severity architecture drift
candidate-lock violation
unsupported exact value
missing required content
invalid responsive strategy
unresolved downstream-critical unknown
implementation/tree mismatch
```

## Final Project Gate Boundary

The terminal `/project-gate-export` pass result must be derived from:

```text
actual canonical Architect Stage Payload
→ existing Schema and semantic validation
→ selected-candidate consistency
→ existing Producer Gate exporter
→ actual canonical export
→ contract and digest verification
```

Caller-controlled success Booleans cannot replace actual validation. Preserve locked identity, canonical serialization, provenance, digest integrity, invalid-payload rejection, and legacy-output non-substitution.

## Optional Audit Tooling

Stage Anchors, Receipts, Boundary Records, Failure Events, Validation Bundles, Validation Profiles, independent regeneration, and `authorization_valid` remain optional repository-audit and deterministic-regression tooling.

They do not authorize ordinary internal Stage movement and their absence is not a project-run blocker.
