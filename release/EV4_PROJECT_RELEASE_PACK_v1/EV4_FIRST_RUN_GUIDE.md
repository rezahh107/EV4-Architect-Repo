# EV4 First Run Guide

Status: release_candidate_for_controlled_use  
Version: 1.4.1

## Fast Start

In a new user-facing Architect chat with the Project Instructions loaded, send only:

```text
شروع
```

When no screenshot, section description, active run, or resumable runtime material is present, return the exact response from:

```text
manifests/architect-conversation-bootstrap.v1.json
```

If the user supplies `شروع` together with a screenshot or usable section description, do not repeat the bootstrap questions. Run `/intake` using the supplied input.

The controlled opening sequence is:

```text
/intake → /research → /decompose
```

Do not skip `/research`.

## Recommended First Input

Upload one section screenshot and optionally include:

```text
Device context: Desktop, Tablet, Mobile, or unknown
Available assets
Known interaction or content requirements
Explicit constraints or exceptions
```

Do not repeat details already visible in the screenshot unless they are important constraints.

## Evaluator-Derived Stage Result

Every Stage supplies its Stage Output to:

```text
scripts/architect_quality_runtime.py#evaluate_stage
```

The evaluator derives:

```yaml
stage_status: pass | needs_input | blocked
blocking_issues: []
carried_unknowns: []
quality_checks: {}
next_stage: exact Manifest successor or null
evaluation_mode:
evaluated_stage_output_digest:
```

A producer-authored or serialized Stage Result is readable but does not authorize continuation. Resume uses the smallest available Stage Output and Run State; do not create a persistent store, immutable receipt, or Artifact registry solely for resume.

Internal Anchors, Bundles, independent regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, and repository maintenance are not ordinary Stage-continuation requirements.

## /intake

If intake quality criteria pass and no architecture-changing question remains, continue to `/research`.

If one minimum architecture-changing question remains, return `needs_input` and ask only that question.

Do not recommend, score, build a tree, or invent exact values during intake.

## /research

Record exactly one disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

`existing_evidence_sufficient` and `no_platform_question` are valid passing outcomes. Do not require external citations, URLs, retrieval metadata, or source receipts when no platform-capability claim requires active lookup.

`blocked_by_missing_required_source` blocks only when a downstream decision genuinely depends on unavailable evidence.

## /decompose

Continue to `/architectures` only after observed, inferred, unknown, and `not_allowed_yet` facts are separated. Do not infer the actual Elementor DOM or recommend architecture.

## /architectures

Continue to `/score-evidence` only after viable architecture families and coverage evidence exist. Do not choose a winner.

## /score-evidence

Use the approved rubric. Use `?` for missing evidence and `N/A` only when genuinely non-applicable. Do not convert unknowns into numbers or hide a recommendation.

## /score-audit

Only an accepted audit state equivalent to `pass` or `pass_with_minor_flags`, with no material defect, permits `/recommend`.

## /recommend

Select only from the audited eligible set and lock `selected_candidate_id`. User preference does not replace technical evidence.

## Unknown Lifecycle

Active unknowns persist in Run State and cannot disappear through omission.

Ordinary resolution requires an explicit type and explanatory note. A resolvable evidence reference is required only for downstream-critical or Artifact-dependent unknowns.

## /build-tree and /implementation

Preserve the selected candidate and approved tree. The canonical content is the existing structured Stage Output; do not create wrapper Artifacts merely to compute digests.

The evaluator computes digests from actual content. Reject missing content, fabricated SHA-like strings, `null == null`, candidate drift, and approved-tree mismatch.

Do not invent exact values, assets, breakpoints, interactions, or Elementor paths.

## /final-audit

Block handoff when blocker/high findings, candidate drift, unsupported exact values, missing required content, invalid responsive strategy, unresolved downstream-critical unknowns, or implementation/tree mismatch remain.

## /handoff-export and /project-gate-export

Package only accepted upstream outputs.

The terminal `/project-gate-export` pass result must come from the actual canonical Architect Stage Payload, existing Schema and semantic validation, selected-candidate consistency, existing Producer Gate exporter, actual canonical export, and contract/digest verification.

Caller-authored success Booleans cannot replace actual validation. Do not substitute `/builder-feed-export`.

## Partial Rerun

Start at the earliest Stage whose owned information changed. Invalidate dependent downstream results, preserve unaffected Run State, reactivate unknowns whose resolutions depended on invalidated work, and invalidate candidate lock only when the rerun reaches `/recommend` or earlier.

Do not require Anchor, Bundle, independent rerun authorization, or cryptographic rerun receipts.

## Quick Stop Rules

Stop or request minimum input only for genuine quality reasons:

```text
usable project input is missing
architecture-changing question is unanswered
required platform evidence cannot be obtained
mandatory Stage order is violated
required Stage check fails or remains unknown
observation and inference are mixed
architecture coverage is incomplete
score audit fails
selected candidate changes after lock
active unknown disappears or a critical unknown closes without resolvable evidence
canonical Build Tree or Implementation content is missing or mismatched
final audit has blocker/high findings
actual canonical Project Gate payload or export is invalid
```

Do not stop only because optional repository-audit carriers or repository workflow evidence are unavailable.

## Current Boundary

This release pack supports controlled architecture analysis and fail-closed final handoff generation. It does not establish live model-host enforcement, live Elementor rendering, real Elementor export JSON validity, browser/device QA, exact pixel matching, downstream acceptance, or production readiness.
