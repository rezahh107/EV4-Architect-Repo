# EV4 Stage Protocols Bundle

Status: release_candidate_quality_first_runtime  
Version: 1.1.0

## Common Stage Result

Every logical Stage closes with `ev4-architect-stage-result@1.0.0`:

```text
pass → exact Manifest successor
needs_input → minimum architecture-changing or required-evidence question
blocked → explicit evidence-based repair route
```

Stage Anchors, Validation Bundles, independent regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, and repository maintenance are not ordinary continuation prerequisites.

All detailed Stage quality and hardening controls remain active. Only old transition-authorization clauses are superseded by `contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md`.

## /intake

Capture usable input, defaults, constraints, non-blocking unknowns, and minimum blocking questions.

Forbidden: architecture, scoring, recommendation, build tree, invented exact values.

`pass → /research`.

## /research

Govern platform capability evidence and version-sensitive claims.

Disposition:

```text
active_lookup_required
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

Forbidden: visual interpretation, scoring, recommendation, tree, implementation.

`pass → /decompose`.

## /decompose

Produce the visual role map and preserve:

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

Only accepted state equivalent to `pass` or `pass_with_minor_flags` with no material defect permits recommendation.

`pass → /recommend`.

## /recommend

Select one candidate from the audited eligible set.

```text
selected_candidate_id
selected_candidate_locked: true
```

Forbidden: re-scoring, new architecture, tree, implementation, invented exact values.

`pass → /build-tree`.

## /build-tree

Translate the locked candidate into an auditable Elementor Structure Panel tree.

Required: node identities, parent relationships, wrapper justification, editable content, overlay boundaries, class intent, unknowns, stable tree digest.

Forbidden: re-architecture, final CSS, implementation settings, exact-value invention.

`pass → /implementation`.

## /implementation

Map the approved tree to Elementor elements, widgets, classes, variables, assets, responsive controls, interactions, accessibility, and scoped CSS needs.

Required: exact candidate/tree preservation.

Forbidden: unsupported assets, breakpoints, interactions, values, UI paths, global CSS, readiness overclaim.

`pass → /final-audit`.

## /final-audit

Audit candidate lock, tree/implementation fidelity, required content, responsive validity, accessibility, scoped CSS, unknown lifecycle, and handoff safety.

Blocker/high findings, candidate drift, unsupported exact values, invalid responsive strategy, missing required content, unresolved downstream-critical unknowns, or implementation/tree mismatch prevent pass.

`pass → /handoff-export`.

## /handoff-export

Package accepted outputs without adding decisions.

Required: candidate lock, matching digests, findings and unknowns preserved, canonical Project Gate payload source.

Forbidden: new decisions, hidden repair, legacy export substitution.

`pass → /project-gate-export`.

## /project-gate-export

Produce the canonical Architect Producer Gate Export or a fail-closed blocked result.

Preserve canonical payload Schema/semantic validation, locked identity, canonical serialization, provenance, digest integrity, invalid-payload rejection, and legacy-output non-substitution.

This is terminal.

## Partial Rerun

Use the earliest Stage whose owned information changed. Reuse only unaffected outputs and close the rerun Stage with a new Stage Result.

## Optional Audit Tooling

Deterministic Artifact, Receipt, Boundary, Failure Event, Anchor, and Bundle transactions remain optional repository-audit and regression tools. They do not authorize ordinary Stage movement.
