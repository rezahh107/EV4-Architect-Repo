# Project Instructions — Active Overrides

Status: active  
Version: 0.7.0  
Applies to: current EV4 Architect Project Instructions and release-pack mirrors

## Authority

Read and apply first:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
contracts/ARCHITECT_STAGE_RESULT_V1.md
manifests/architect-pipeline-manifest.v1.json
```

This file supersedes only authorization-driven continuation clauses in `01_PROJECT_INSTRUCTIONS.md`, active Stage documents, hardening patches, source-access references, contracts, and release-pack mirrors. All non-conflicting quality controls remain active.

## Normal Run Continuation

Every Stage produces a result compatible with:

```text
ev4-architect-stage-result@1.0.0
```

```yaml
pass:
  meaning: Stage quality criteria are satisfied.
  next_stage: exact Manifest successor

needs_input:
  meaning: minimum architecture-changing or required-evidence input remains.
  next_stage: null

blocked:
  meaning: a genuine quality, evidence, fidelity, or final-handoff defect remains.
  next_stage: null
```

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

The Pipeline Manifest remains authoritative for Stage order and legal successor. Stage quality determines continuation.

## Research Requirement

`/research` remains mandatory. `/intake → /decompose` is forbidden.

Record one disposition:

```text
active_lookup_required
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

Only `blocked_by_missing_required_source` blocks, and only when a downstream decision genuinely depends on evidence that cannot be obtained.

Research continues to enforce:

- platform capability is not project-specific behavior;
- official documentation does not decide visual interpretation;
- research does not score or recommend architecture;
- unsupported and version-sensitive claims remain unknown.

## Partial Rerun

Use `contracts/PARTIAL_RERUN_CONTRACT.md` with the latest valid Stage output and Stage Result.

Identify changed input, earliest safe rerun Stage, reusable outputs, invalidated outputs, required evidence, and minimum confirmation.

Do not require Anchor or Bundle authorization for an ordinary partial rerun.

## Unknown Lifecycle

An active unknown cannot disappear merely because a later Stage omits it.

It leaves the active set only through an explicit evidence-backed state:

```text
resolved_with_evidence
not_applicable
stale after valid rerun
```

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

No visual-to-build-tree shortcut or non-successor continuation is allowed.

## Scoring and Recommendation

`/score-evidence` uses the approved rubric, `?` for missing evidence, and `N/A` only when truly non-applicable. It must not hide a recommendation.

`/recommend` may run only after accepted `/score-audit` status equivalent to `pass` or `pass_with_minor_flags` with no material defect.

After recommendation, `selected_candidate_id` is immutable unless an explicit repair or rerun invalidates the recommendation.

## Fidelity and Final Audit

`/build-tree` preserves the selected architecture.

`/implementation` preserves the approved tree and must not invent exact values, assets, breakpoints, interactions, or Elementor paths.

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

Strong fail-closed validation remains mandatory at:

```text
Architect → Project Gate
```

Preserve canonical Architect Stage Payload validation, semantic validation, locked identity, canonical serialization, provenance, digest integrity, invalid-payload rejection, and legacy-output non-substitution.

## Optional Audit Tooling

Stage Anchors, Receipts, Boundary Records, Failure Events, Validation Bundles, Validation Profiles, independent regeneration, and `authorization_valid` remain optional repository-audit and deterministic-regression tooling.

They do not authorize ordinary internal Stage movement and their absence is not a project-run blocker.

## Repository Repair Separation

Routine Run repair and repository maintenance are separate.

A Stage quality failure first returns the current Run repair route. It must not automatically require a repository branch, PR, exact-head review, owner Merge, or status reconciliation.

An active Architect project Run must not perform repository write actions.

## Source Access

RAG and TUYA source-classification, evidence-state, freshness, conflict, and leakage controls remain active. Any older clause requiring Anchor, Bundle, independent regeneration, or profile completeness before ordinary source use is superseded.

## Validation Boundary

Normal-run validation:

```bash
python scripts/check-architect-quality-runtime.py
python scripts/check-architect-bootstrap.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p no:cacheprovider -q \
  tests/test_architect_quality_runtime.py \
  tests/test_architect_bootstrap_semantics.py
```

Optional transaction validation remains separate and does not replace the final `ev4-architect-stage-payload@1.0.0` contract.
