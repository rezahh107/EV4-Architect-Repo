# Architect Stage Evidence Payload v1

Status: implemented_initial_v1
Schema identity: `ev4-architect-stage-payload@1.0.0`
Owner: `rezahh107/EV4-Architect-Repo`
Consumer boundary: common Project Gate Stage Evidence Bundle envelope

## Purpose

This contract defines the Architect-owned payload that may be placed inside the common EV4 Project Gate Stage Evidence Bundle.

The payload records Architect evidence and decisions only. It does not prove constructability, authorize Builder execution, complete responsive validation, or claim production readiness.

```text
Architect stages
→ Architect Stage Payload
→ common Stage Evidence Bundle
→ Project Gate envelope validation
→ future Architect-to-CE transition
```

Project Gate may validate the envelope and preserve hashes/provenance. Project Gate must not create missing Architect facts, change locked architecture identity, or silently repair the payload.

## Implemented Scope

Implemented in this contract:

- selected architecture identity;
- meaningful selected-candidate lock semantics;
- approved structure model;
- normal-flow, overlay, editable-content, class, asset, scoped-CSS, responsive, and Dynamic Loop intent;
- evidence register;
- unresolved evidence register;
- forbidden work;
- Architect/downstream boundary assertions;
- explicit extension policy;
- stable behavioral rule IDs.

Not implemented here:

- Project Gate Architect-to-CE transition;
- CE intake validation;
- Builder execution authorization;
- real end-to-end fixture validation;
- legacy contract retirement.

## Behavioral Rules

| rule_id | rule | enforcement target |
|---|---|---|
| `A-R01` | selected candidate must be explicit and meaningfully locked | schema + semantic validator + fixtures |
| `A-R02` | Architect must not claim Builder readiness | schema + semantic validator + fixtures |
| `A-R03` | Architect must not claim production readiness | schema + semantic validator + fixtures |
| `A-R04` | geometry, assets, breakpoints, and dynamic data must not be invented | semantic validator + fixtures |
| `A-R05` | unresolved evidence must be preserved | schema + semantic validator + fixtures |
| `A-R06` | class names must be deterministic | schema pattern + fixtures |
| `A-R07` | wrapper decisions require justification | semantic validator + fixtures |
| `A-R08` | scoped CSS intent must remain local and safe | schema + semantic validator + fixtures |
| `A-R09` | Dynamic Loop must not be inferred | semantic validator + fixtures |
| `A-R10` | mobile/responsive uncertainty must remain visible | schema + semantic validator + fixtures |
| `A-R11` | CE review is required before Builder execution | schema + semantic validator + fixtures |
| `A-R12` | canonical core intent must not use vague free-form objects | schema `additionalProperties:false` + fixtures |

Do not reuse a rule ID for a different meaning.

## Semantic Lock Requirement

A boolean such as:

```json
{ "selected_candidate_locked": true }
```

is not sufficient by itself.

A locked architecture must also include:

- `selected_candidate_id`;
- `architecture_family`;
- decision source stage and payload identity;
- `evidence_refs`;
- `locked_decision_refs`;
- `approved_structure_ref`;
- `source_evidence_refs`;
- an approved structure node matching the approved structure reference.

## Required Core Sections

```text
payload_identity
source_stage_lineage
architecture_identity
approved_structure_model
architect_intent
evidence_register
unresolved_evidence
forbidden_work
boundary_assertions
validation_contract
extension_records
```

Core sections are structurally constrained and use `additionalProperties:false` where practical.

## Boundary Assertions

The payload must assert these downstream-positive claims as false:

```text
constructability_proven
ce_approved
builder_ready
builder_executable
builder_runtime_intake_authorized
responsive_complete
production_ready
live_elementor_validated
real_export_json_validated
exact_pixel_match_validated
```

A positive value for any of these claims is invalid.

## Unresolved Evidence

Unknown or missing evidence must remain visible in `unresolved_evidence[]` and must state its owner, reason, blocked conclusion, and required-before boundary.

If the payload itself is insufficient, `payload_status` must be `insufficient_evidence` and unresolved evidence must explain what blocks acceptance.

## Extension Policy

Core sections must not accept arbitrary free-form objects.

Extensions are allowed only through `extension_records[]`. Each extension must include extension identity, owner, evidence state, evidence references, allowed consumer, `cannot_override_core_fields: true`, and `downstream_readiness_claims_allowed: false`.

Extensions must not override core fields or introduce downstream readiness claims.

## Validation

Run:

```bash
python -m pip install 'jsonschema>=4.22.0' 'pytest>=8.0.0'
python scripts/check-architect-stage-payload.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_architect_stage_payload_validator.py
```

The validator must fail closed, sort diagnostics deterministically, avoid repair or inference, and distinguish `invalid` from `insufficient_evidence`.
