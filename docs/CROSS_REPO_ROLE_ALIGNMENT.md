# Cross-Repo Role Alignment

Patch: Cross-repo contract drift repair  
Repo role: Architect / architecture decision system  
Shared Contracts status: future-planned only; no canonical schema migration in this patch.

## Production pipeline

```text
Architect → CE → Builder → Responsive
```

Architect does not hand production payloads directly to Responsive. Responsive may see Architect baseline only after CE and Builder provenance have been carried forward by the Builder/Project-Gate handoff.

## Architect owns

- `reference_role` at design-intent level.
- `experience_intent` as advisory design intent.
- `desired_outcome` and `high_level_design_intent`.
- Design-level source visual evidence registration.
- Approved architecture handoff, selected candidate, structure tree, and approved class names.
- The authoritative CE intake source identity: `ev4-architect-output-contract@1.0.0`.

## Architect does not own

- Final `golden_reference_contract` locking.
- Builder Executable Package issuance.
- Builder runtime intake approval.
- Builder action-batch execution strategy.
- Final visual parity pass/fail status.
- Tablet/mobile reference-family approval.
- Production Responsive start authorization.

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
- Builder-to-Responsive evidence/provenance handoff.

### Responsive owns

- Tablet/mobile adaptation review.
- Scoped reference-family extension.
- Responsive evidence gates.
- No raw screenshot authority.
- Requiring Builder/CE provenance before production Responsive intake starts.

### Future shared owner

A future `EV4-Shared-Contracts` may own schemas, enums, spatial lexicon, build-intent templates, reference-family schema, and compatibility manifest. This patch must not create that repo or move canonical schemas.

## Compatibility note

`ev4-builder-context-package@1.0.0` is the Builder runtime intake schema owned by `rezahh107/EV4-Builder-Assistant-Repo`.

Architect-side reuse of that schema id is retired. Historical Architect payloads must migrate to `ev4-architect-legacy-builder-context-export@1.0.0` with `legacy_schema_alias: ev4-builder-context-package@1.0.0`, or to the authoritative `ev4-architect-output-contract@1.0.0` CE intake source.
