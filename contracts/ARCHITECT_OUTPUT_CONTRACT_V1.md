# Architect Output Contract v1

Status: contract_definition_v1  
Schema: `ev4-architect-output-contract@1.0.0`  
Owning repo: `rezahh107/EV4-Architect-Repo`  
Consumer: `constructability_engineer`  
Runtime authority: non-executable Architect output only

## Purpose

This contract resolves the Architect-to-CE boundary by making Architect output strict, deterministic, and safe for CE ingestion.

Architect may describe the approved architecture and preserve locked design intent. Architect must not emit a Builder runtime package, prove constructability, or authorize execution.

## Contract boundary

Architect output under this contract is:

```yaml
packet_purpose: ce_intake_source
intended_consumer: constructability_engineer
ce_review_required: true
builder_executable_allowed: false
builder_ready_status: not_builder_ready_without_ce_proof
production_ready_allowed: false
```

CE may use this package only as structured input for constructability review.

Builder must not consume this package as execution authorization.

## Required schema

Use:

```text
schemas/ev4-architect-output-contract.v1.schema.json
```

The schema is strict:

- `additionalProperties: false`
- locked identity fields are required
- class names are explicit and unique
- approved structure is represented as deterministic nodes
- CE review units are explicit
- evidence gaps are explicit
- ambiguity/freeform intent fields are not allowed
- Builder-ready or production-ready claims are forbidden

## Removed ambiguity fields

The following conceptual/freeform fields must not appear in v1 output:

```text
desired_outcome
high_level_design_intent
experience_intent
source_visual_evidence_registration
reference_screenshot_instruction
unknowns_to_preserve
audit_flags_to_preserve
first_suggested_builder_batch
confirmation_request_seed
first_builder_batch
confirmation_request
compatibility_note
```

If a concept matters for CE, it must be converted into one of:

```text
approved_structure_tree
approved_class_names
class_creation_application_map
widget_mapping_table
ce_review_units
evidence_gaps_for_ce
responsive_qa_seed
forbidden_work
source_payload_ledger
```

## Deterministic conversion rules

1. Preserve `selected_candidate_id` exactly.
2. Require `selected_candidate_locked: true`.
3. Derive `approved_class_names` by flattening and de-duplicating class names from `class_creation_application_map` and approved structure nodes.
4. Convert every executable or potentially executable node into one `ce_review_units[]` item.
5. Do not infer geometry, anchors, assets, overlay, responsive behavior, interaction, Dynamic Loop, accessibility, or exact Elementor UI paths.
6. Missing proof must become an explicit `evidence_gaps_for_ce[]` item.
7. Any unmapped conceptual field is a validation failure.
8. Any Builder-ready claim is a validation failure.

## Architect-to-CE mapping summary

| Architect v1 path | CE intake path | Rule |
|---|---|---|
| `selected_candidate_id` | `selected_candidate_id` | copy exact |
| `selected_candidate_locked` | `selected_candidate_locked` | must be `true` |
| `approved_structure_tree[]` | `approved_structure_tree[]` | copy normalized nodes |
| `approved_class_names[]` | `approved_class_names[]` | copy exact after de-duplication |
| `class_creation_application_map[]` | `approved_class_names[]` + CE review context | flatten unique class names |
| `widget_mapping_table[]` | `ce_review_units[]` | normalize widgets into review units |
| `ce_review_units[]` | `ce_review_units[]` | copy exact |
| `evidence_gaps_for_ce[]` | `interrogation_inputs.*.state` | convert missing proof to `not_proven` or `blocked` |
| `responsive_qa_seed` | `interrogation_inputs.responsive` | map status without guessing |
| `forbidden_work[]` | CE boundary checks | enforce as negative constraints |

## Validation checklist before CE ingestion

- The payload validates against `ev4-architect-output-contract@1.0.0`.
- No additional properties are present.
- `packet_purpose` is `ce_intake_source`.
- `intended_consumer` is `constructability_engineer`.
- `builder_executable_allowed` is `false`.
- `production_ready_allowed` is `false`.
- `selected_candidate_locked` is `true`.
- `approved_class_names` is non-empty and unique.
- Every node that implies execution has a matching `ce_review_units[]` item.
- Every missing proof is represented in `evidence_gaps_for_ce[]`.
- No conceptual/freeform ambiguity fields remain.
- No Builder batch, confirmation request, or executable package is emitted.
