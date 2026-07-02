# Stage 11 — /builder-feed-export

Status: role_aligned_ce_intake_export_v1.3.0  
Version: 1.3.0  
Authoritative CE intake source schema: `ev4-architect-output-contract@1.0.0`  
Compatibility feed schema: `ev4-architect-builder-feed-export@1.0.0` is legacy/adapter input only  
Retired Architect-side schema id: `ev4-builder-context-package@1.0.0`  
Anchor required: yes  
Applies after: `/handoff-export`

## Purpose

`/builder-feed-export` packages the audited `/handoff-export` as a non-executable Architect handoff and CE intake source.

It does not produce a Builder runtime intake package. It does not permit Builder execution and it must not bypass the Constructability Engineer.

Production flow:

```text
Architect → CE → Builder → Responsive
```

Architect emits a CE-intended source package. CE proves implementation strategy. Builder receives only CE/Gate accepted runtime intake. Responsive receives Builder output and build evidence with CE/Builder provenance.

## Boundary

Stage 11 packages only approved handoff data.

It preserves:

```text
selected_candidate_id
approved_structure_tree
class_creation_application_map
approved widget/content/decoration maps
forbidden_work
visible audit flags
unknowns_to_preserve
production_ready_allowed: false
```

It does not add classes, widgets, breakpoints, CSS, clickability, Dynamic Loop assumptions, mobile/tablet connector behavior, Golden Reference locking, Builder package-gate approval, executable strategy, or Responsive production handoff approval.

## Required Architect Output Contract

The authoritative Stage 11 CE intake source is:

```yaml
Architect_Output_Contract:
  schema: ev4-architect-output-contract@1.0.0
  source_stage: /builder-feed-export
  source_handoff_stage: /handoff-export
  packet_purpose: ce_intake_source
  intended_consumer: constructability_engineer
  ce_review_required: true
  builder_executable_allowed: false
  builder_ready_status: not_builder_ready_without_ce_proof
  selected_candidate_locked: true
  production_ready_allowed: false
```

CE's ingestion contract consumes this identity through `ev4-architect-to-ce-input-package@1.0.0`.

## Compatibility Feed

`ev4-architect-builder-feed-export@1.0.0` remains a legacy compatibility feed for historical Stage 11 data and adapter/gate migration. It is not the preferred CE intake identity and is not Builder runtime intake.

Any compatibility feed must keep these invariants:

```yaml
packet_purpose: ce_intake_source
intended_consumer: constructability_engineer
ce_review_required: true
requires_constructability_engineer_review: true
builder_executable_allowed: false
builder_ready_status: not_builder_ready_without_ce_proof
production_ready_allowed: false
```

## Retired Architect-side `ev4-builder-context-package@1.0.0`

Historical Architect exports previously reused:

```yaml
schema: ev4-builder-context-package@1.0.0
```

That schema id is now reserved for Builder runtime intake in `rezahh107/EV4-Builder-Assistant-Repo`.

Architect must not emit new payloads with that schema discriminator. Historical Architect payloads that need machine-readable migration must use:

```yaml
schema: ev4-architect-legacy-builder-context-export@1.0.0
legacy_schema_alias: ev4-builder-context-package@1.0.0
compatibility_note: architect_export_legacy_name_not_builder_runtime_intake
```

The file `schemas/ev4-builder-context-package.schema.json` is a tombstone and intentionally rejects Architect payloads.

## Architect-Owned Intent Fields

Architect may own and emit design-level intent only:

```yaml
reference_role: inspiration_only | visual_direction | candidate_source_evidence
desired_outcome: string
high_level_design_intent: string
experience_intent: advisory object
source_visual_evidence_registration:
  evidence_id:
  evidence_type:
  source_ref:
  allowed_use: design_level_reference_only
```

Architect must not own:

```text
- final Golden Reference locking
- Builder Executable Package issuance
- Builder runtime intake approval
- Builder batch execution strategy
- final visual parity result
- responsive tablet/mobile reference-family approval
```

## Required User-Facing Sections

Stage 11 output includes Persian user-facing sections while keeping technical identifiers in English. It must say explicitly that the output is not Builder-ready until CE emits an executable package and Builder validates the runtime intake package.
