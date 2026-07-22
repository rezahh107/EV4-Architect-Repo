# EV4 Project Release Pack v1

Status: release_candidate_quality_first_runtime  
Pack schema: `ev4-project-release-pack@1.0.0`  
Date: 2026-07-22  
Target runtime: ChatGPT Project

## Purpose

This folder packages EV4 Architect into a compact operational subset. The repository remains the source of truth.

## Runtime Model

Normal internal continuation is quality-driven through `ev4-architect-stage-result@1.0.0` and `contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md`.

```text
Stage output
→ Stage quality checks
→ pass | needs_input | blocked
→ exact Manifest successor, minimum input, or repair route
```

Stage Anchors, Validation Bundles, independent regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, and repository maintenance are optional audit/repository workflow evidence and are not ordinary project-run transition requirements.

## Quality Controls Retained

```text
mandatory Stage order
mandatory /research disposition
observation/inference separation
architecture option coverage
evidence-bound scoring
Score Audit before recommendation
selected candidate lock
unknown lifecycle
build-tree fidelity
implementation fidelity
Final Audit
fail-closed Project Gate export
legacy-output non-substitution
```

## Release Files

```text
PROJECT_INSTRUCTIONS_FINAL.md
EV4_CORE_CONTRACTS_BUNDLE.md
EV4_STAGE_PROTOCOLS_BUNDLE.md
EV4_EXAMPLES_AND_CALIBRATION_BUNDLE.md
EV4_FIRST_RUN_GUIDE.md
PROJECT_SOURCE_MANIFEST.md
EV4_RUN_COPILOT_INSTRUCTIONS.md
```

## Release Boundary

Validated only after exact-Head CI:

```text
quality-first logical pipeline regression through /project-gate-export
negative coverage for Stage skipping, premature recommendation, candidate drift, unknown loss, fidelity failure, and invalid final export
bootstrap and Manifest authority alignment
```

Not established by the release pack:

```text
live ChatGPT/model-host enforcement
live Elementor rendering
real Elementor export JSON
browser/device QA
exact pixel matching
downstream acceptance of a real non-synthetic Run
production readiness
```

## Recommended Setup

Use `PROJECT_INSTRUCTIONS_FINAL.md` as Project Instructions and upload the five core release files listed in `PROJECT_SOURCE_MANIFEST.md`.
