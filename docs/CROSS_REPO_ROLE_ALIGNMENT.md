# Cross-Repo Role Alignment

Patch: Patch 1 — Cross-Repo Role Alignment  
Repo role: Architect / architecture decision system  
Shared Contracts status: future-planned only; no canonical schema migration in this patch.

## Architect owns

- `reference_role` at design-intent level.
- `experience_intent` as advisory design intent.
- `desired_outcome` and `high_level_design_intent`.
- Design-level source visual evidence registration.
- Approved architecture handoff, selected candidate, structure tree, and approved class names.

## Architect does not own

- Final `golden_reference_contract` locking.
- Builder Executable Package issuance.
- Builder runtime intake authorization.
- Builder action-batch execution strategy.
- Final visual parity pass/fail status.
- Tablet/mobile reference-family authorization.

## Stage 10 handoff boundary

Stage 10 Builder-facing wording is pre-CE handoff eligibility only. Terms such as `builder_handoff_allowed`, `FINAL BUILDER HANDOFF`, or `ready_for_builder_handoff` must not be interpreted as Builder-runtime authorization or Builder-executable readiness.

Current boundary:

```yaml
stage_10_builder_facing_language:
  allowed_meaning: pre_ce_handoff_eligibility
  builder_runtime_authorization: false
  builder_executable_by_default: false
  ce_proof_required_before_execution: true
  builder_side_validation_required_before_execution: true
  boundary_note: stages/10_HANDOFF_EXPORT_PATCH_1_BOUNDARY_NOTE.md
```

## Cross-repo responsibilities

### CE owns

- Constructability review.
- Execution strategy proof.
- `golden_reference_contract` locking/carrying after evidence review.
- `reference_paradigm_lock`.
- `paradigm_to_structure_map`.
- `build_intent_brief` structured execution seed.
- Builder package gate.
- Builder Executable Package only when zero decisions remain.

### Builder owns

- Runtime intake validation.
- Deterministic Build Intent rendering.
- Action batch execution.
- Checkpoint and evidence loop.
- Visual parity report.
- Completion wording gate.
- No design invention.

### Responsive owns

- Tablet/mobile adaptation review.
- Scoped reference-family extension.
- Responsive evidence gates.
- No raw screenshot authority.

### Future shared owner

A future `EV4-Shared-Contracts` may own schemas, enums, spatial lexicon, build-intent templates, reference-family schema, and compatibility manifest. This patch must not create that repo or move canonical schemas.

## Compatibility note

`ev4-builder-context-package@1.0.0` has historical drift. Architect exports must now use `ev4-architect-builder-feed-export@1.0.0` or carry an explicit compatibility note saying the Architect export is a CE intake source, not Builder runtime intake.
