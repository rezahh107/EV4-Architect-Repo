# Prompt 01 Pipeline Conflict and Overlap Report

Status: active_prompt_01_audit

## Observed conflict

`README.md` described the current pipeline as ending with `/handoff-export → /builder-feed-export`.
`STATUS.md` listed `/handoff-export → /e2e-test → /e2e-screenshot-validation`.
`STATUS_0.16.0_RELEASE_PACK_READY.md` records E2E-002 screenshot validation as a release-pack validation result, not a normal per-run project execution stage.

## Resolution

`manifests/architect-pipeline-manifest.v1.json` is the canonical machine-readable Architect project execution manifest.

Canonical project execution now ends with:

```text
/handoff-export → /project-gate-export
```

`/builder-feed-export` remains a legacy compatibility output and is not canonical for the new Project Gate Producer Export.

`/e2e-test` and `/e2e-screenshot-validation` are validation tracks. They support release confidence and screenshot interpretation claims, but they are not mandatory per-run project execution stages for Producer Gate Export emission.

## Boundary

This adoption does not implement Project Gate runtime integration, CE acceptance, Builder execution, Responsive completion, real Elementor export validation, or production readiness.
