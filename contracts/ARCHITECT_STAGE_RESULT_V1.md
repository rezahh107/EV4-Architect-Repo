# Architect Stage Result v1

Status: active  
Schema: `ev4-architect-stage-result@1.0.0`  
Schema path: `schemas/ev4-architect-stage-result.v1.schema.json`

## Purpose

`Stage Result` is the canonical normal-run continuation carrier. It records whether one logical Stage met its quality criteria and whether the exact Manifest successor may run.

```text
Stage output
→ Stage-specific quality evaluation
→ Stage Result
→ exact Manifest successor, minimum blocking input, or explicit repair route
```

It is not a repository authorization ticket and does not require a Stage Anchor, Validation Bundle, independent Bundle regeneration, exact-head CI, PR review, Merge evidence, or repository maintenance.

## Status semantics

```yaml
pass:
  meaning: Stage quality criteria are satisfied.
  next_stage: exact Manifest successor, or null for the terminal Stage.

needs_input:
  meaning: Minimum user or project evidence is required because the answer can change architecture or downstream correctness.
  next_stage: null
  blocking_issues: non-empty

blocked:
  meaning: A genuine quality, evidence, fidelity, or final-handoff defect prevents safe continuation.
  next_stage: null
  blocking_issues: non-empty
```

A Stage must not be blocked solely because optional repository-audit evidence is absent or a Validation Profile is not `full_transaction_implemented`.

## Research disposition

`/research` remains mandatory and records exactly one disposition:

```text
active_lookup_required
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

Only `blocked_by_missing_required_source` blocks, and only when a downstream decision genuinely depends on evidence that cannot be obtained.

## Required quality invariants

The normal-run validator enforces:

- exact Manifest Stage order and successor;
- no recommendation during `/intake`, `/research`, `/decompose`, `/architectures`, or `/score-evidence`;
- accepted `/score-audit` before `/recommend`;
- no hidden recommendation or conversion of unknown evidence into exact values;
- immutable `selected_candidate_id` after `/recommend`;
- build-tree and implementation fidelity;
- active unknown propagation until explicit evidence-backed resolution;
- blocker/high final-audit findings prevent handoff;
- canonical Project Gate payload validity;
- no legacy export substitution.

## Optional audit tooling boundary

The following remain useful but are not normal-run continuation authority:

```text
Stage Anchor
Validation Receipt
Boundary Record
Failure Event
Validation Bundle
independent Bundle regeneration
exact-head CI evidence
PR review evidence
```

They may support repository audits, deterministic validator regression, compatibility evidence, or resume diagnostics. Their absence does not prevent a valid project Run.

## Compatibility

The Pipeline Manifest remains the sole machine-readable authority for Stage inventory, order, versions, successor edges, and terminal identity.

The Validation Profiles Registry remains an optional repository-audit capability registry. Its `full_transaction_implemented` status describes available deterministic transaction tooling, not whether a user-facing Stage may continue.

The final Architect → Project Gate boundary remains fail-closed under the canonical Architect Stage Payload and Producer Gate Export contracts.
