# EV4 Stage Protocols Bundle

Status: release_candidate_quality_first_runtime  
Version: 1.2.0

## Common Runtime Protocol

Every logical Stage produces domain-specific Stage Output. One canonical evaluator derives the Stage Result:

```text
Stage Output + Run State + Manifest-owned checks
→ scripts/architect_quality_runtime.py#evaluate_stage
→ pass | needs_input | blocked
```

A serialized Stage Result is readable but non-authorizing. Stage Anchors, Validation Bundles, independent regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, and repository maintenance are not ordinary continuation prerequisites.

The Pipeline Manifest owns the finite recognized checks for each Stage. Missing, unknown, cross-Stage, failed, unresolved, or improperly `not_applicable` required checks block continuation.

## /intake

Capture usable input, defaults, constraints, non-blocking unknowns, and minimum blocking questions.

Forbidden: architecture, scoring, recommendation, build tree, invented exact values.

`pass → /research`.

## /research

Govern platform-capability evidence and version-sensitive claims.

Disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

The first three may pass. No external lookup receipt is required for a truthful `no_platform_question` result.

Forbidden: visual interpretation, scoring, recommendation, tree, implementation.

`pass → /decompose`.

## /decompose

Produce the visual-role map and preserve:

```text
observed
likely | inferred
unknown
not_allowed_yet
```

Forbidden: architecture choice, scoring, exact values, Elementor tree, DOM inference.

`pass → /architectures`.

## /architectures

Enumerate viable architecture families and prove coverage.

Forbidden: winner selection, scoring, final tree, implementation.

`pass → /score-evidence`.

## /score-evidence

Score every eligible candidate using the approved rubric and evidence.

```text
? = missing evidence
N/A = genuinely non-applicable
Unknowns are not numbers.
```

Forbidden: hidden recommendation, invented scores, candidate modification.

`pass → /score-audit`.

## /score-audit

Audit arithmetic, weights, denominator handling, evidence use, gate overrides, unknown discipline, cross-candidate consistency, and hidden recommendation.

Only an accepted state equivalent to `pass` or `pass_with_minor_flags`, with no material defect, permits recommendation.

`pass → /recommend`.

## /recommend

Select one candidate from the audited eligible set and establish:

```text
selected_candidate_id
selected_candidate_locked: true
```

Forbidden: re-scoring, new architecture, tree, implementation, invented exact values.

`pass → /build-tree`.

## Unknown Lifecycle

Active unknowns persist in Run State. Omission is not resolution.

Ordinary resolution requires an explicit type and note. A resolvable evidence reference is required only for downstream-critical or Artifact-dependent unknowns.

## /build-tree

Translate the locked candidate into canonical structured Build Tree content.

Required: node identities, parent relationships, wrapper justification, editable content, overlay boundaries, class intent, unknowns, and selected-candidate preservation.

The evaluator computes the digest from the actual structured content. Do not create a wrapper Artifact solely to obtain a digest.

Forbidden: re-architecture, final CSS, implementation settings, exact-value invention, caller-authored digest authority.

`pass → /implementation`.

## /implementation

Map the approved tree to Elementor elements, widgets, classes, variables, assets, responsive controls, interactions, accessibility, and scoped CSS needs.

The canonical structured Implementation content must contain the approved Build Tree representation. The evaluator derives both content identity and fidelity.

Forbidden: unsupported assets, breakpoints, interactions, values, UI paths, global CSS, readiness overclaim, `null == null` fidelity, fabricated digest equality.

`pass → /final-audit`.

## /final-audit

Audit candidate lock, tree/implementation fidelity, required content, responsive validity, accessibility, scoped CSS, unknown lifecycle, and handoff safety.

Blocker/high findings, candidate drift, unsupported exact values, invalid responsive strategy, missing required content, unresolved downstream-critical unknowns, or implementation/tree mismatch prevent pass.

`pass → /handoff-export`.

## /handoff-export

Package accepted outputs without adding decisions.

Required: candidate lock, actual canonical content identities, findings and unknowns preserved, and canonical Project Gate payload source.

Forbidden: new decisions, hidden repair, legacy export substitution.

`pass → /project-gate-export`.

## /project-gate-export

Produce the canonical Architect Producer Gate Export or a fail-closed blocked result.

A pass result must be derived from:

```text
actual canonical Architect Stage Payload
→ existing Schema and semantic validation
→ selected-candidate consistency
→ existing Producer Gate exporter
→ actual canonical export
→ contract and digest verification
```

Caller-authored Booleans do not authorize success. Preserve locked identity, canonical serialization, provenance, digest integrity, invalid-payload rejection, and legacy-output non-substitution.

This is terminal.

## Partial Rerun

Use the earliest Stage whose owned information changed. Invalidate dependent downstream Stage Results, preserve unaffected Run State, reactivate unknowns whose resolutions depended on invalidated work, and invalidate candidate lock only when the rerun reaches `/recommend` or earlier.

Do not add a general rerun ledger, cryptographic rerun receipt, or independent rerun authorization.

## Resume

Use the smallest available Stage Output and Run State. Do not create persistent storage, immutable receipts, content-addressable storage, or Artifact registries solely for resume.

## Optional Audit Tooling

Deterministic Artifact, Receipt, Boundary, Failure Event, Anchor, and Bundle transactions remain optional repository-audit and regression tools. They do not authorize ordinary Stage movement.
