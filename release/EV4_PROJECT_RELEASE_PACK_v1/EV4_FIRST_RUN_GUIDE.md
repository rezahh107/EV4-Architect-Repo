# EV4 First Run Guide

Status: release_candidate_for_controlled_use  
Version: 1.3.0

## Fast Start

In a new user-facing Architect chat with the Project Instructions loaded, send only:

```text
شروع
```

When no screenshot, section description, active run, or resumable passed Stage Result is present, return the exact response from:

```text
manifests/architect-conversation-bootstrap.v1.json
```

If the user supplies `شروع` together with a screenshot or usable section description, do not repeat the bootstrap questions. Run `/intake` using the supplied input.

The controlled opening sequence is:

```text
/intake → /research → /decompose
```

## Recommended First Input

Upload one section screenshot and optionally include:

```text
Device context: Desktop, Tablet, Mobile, or unknown
Available assets
Known interaction or content requirements
Explicit constraints or exceptions
```

Do not repeat details already visible in the screenshot unless they are important constraints.

## Stage Result

Every Stage ends with:

```yaml
stage_status: pass | needs_input | blocked
blocking_issues: []
carried_unknowns: []
quality_checks: {}
next_stage: exact Manifest successor or null
```

Internal Anchors, Bundles, independent regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, and repository maintenance are not required for ordinary Stage continuation.

## /intake

If intake quality criteria pass and no architecture-changing question remains:

```text
stage_status: pass
next_stage: /research
```

If one minimum architecture-changing question remains:

```text
stage_status: needs_input
next_stage: null
```

Do not recommend, score, or build a tree during intake.

## /research

Record one disposition:

```text
active_lookup_required
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

The first three may pass to `/decompose` once their evidence obligations are satisfied. The final disposition blocks only when a required downstream decision depends on an unavailable authoritative source.

## /decompose

Continue to `/architectures` only after observed, inferred, unknown, and `not_allowed_yet` facts are separated. Do not infer the actual Elementor DOM or recommend architecture.

## /architectures

Continue to `/score-evidence` only after viable architecture families and coverage evidence exist. Do not choose a winner.

## /score-evidence

Use the approved rubric. Use `?` for missing evidence and `N/A` only when genuinely non-applicable. Do not convert unknowns into numbers or hide a recommendation.

## /score-audit

Only an accepted audit state equivalent to `pass` or `pass_with_minor_flags` with no material defect permits `/recommend`.

## /recommend

Lock `selected_candidate_id`. If a material tie requires preference, ask one minimum question. User preference does not replace technical evidence.

## /build-tree and /implementation

Preserve the selected candidate and approved tree. Do not re-architect or invent exact values, assets, breakpoints, interactions, or Elementor paths.

## /final-audit

Block handoff when blocker/high findings, candidate drift, unsupported exact values, missing required content, invalid responsive strategy, unresolved downstream-critical unknowns, or implementation/tree mismatch remain.

## /handoff-export and /project-gate-export

Package only accepted upstream outputs. Produce the canonical Architect Producer Gate Export or a fail-closed blocked result. Do not substitute `/builder-feed-export`.

## Quick Stop Rules

Stop or request minimum input for genuine quality reasons:

```text
usable project input is missing
architecture-changing question is unanswered
required platform evidence cannot be obtained
mandatory Stage order is violated
observation and inference are mixed
architecture coverage is incomplete
score audit fails
selected candidate changes after lock
active unknown disappears without evidence-backed resolution
build tree or implementation drifts
final audit has blocker/high findings
canonical final payload is invalid
```

Do not stop only because optional repository-audit carriers or repository workflow evidence are unavailable.

## Current Boundary

This release pack supports controlled architecture analysis and fail-closed final handoff generation. It does not establish live model-host enforcement, live Elementor rendering, real Elementor export JSON validity, browser/device QA, exact pixel matching, downstream acceptance, or production readiness.
