# Behavioral Rule Coverage — Prompt 01 Producer Adoption

Status: active_prompt_01_addendum

This addendum preserves existing `A-R01` through `A-R12` and adds new stable Prompt 01 rule IDs. Enforcement status is limited to Architect repository carriers, validators, fixtures, and CI wiring. No Project Gate runtime, CE, Builder, Responsive, or downstream enforcement is claimed here.

| rule_id | concept | risk | prose_source | schema_carrier | validator_rule | valid_fixture | invalid_fixture | CI_step | downstream_contract | enforcement_status |
|---|---|---|---|---|---|---|---|---|---|---|
| A-R13 | canonical Architect pipeline manifest exists | stage drift | manifest doc | `schemas/ev4-architect-pipeline-manifest.v1.schema.json` | `A_MANIFEST_*` | `manifests/architect-pipeline-manifest.v1.json` | synthetic mutation cases | `validate-architect-producer-gate-adoption` | none | ci_enforced_in_architect |
| A-R14 | mandatory stage omission is rejected | silent stage skip | manifest doc | manifest schema | `A_MANIFEST_FINAL_EXPORT_MISSING` | manifest | mutation cases | workflow | none | ci_enforced_in_architect |
| A-R15 | stage complete without output is rejected | false completion | Producer Export schema | Project Gate schema | `A_EXPORT_*` | blocked export fixture | export cases | workflow | none | fixture_tested |
| A-R16 | final Project Gate export is mandatory | no run artifact | manifest doc | manifest schema | `A_MANIFEST_FINAL_EXPORT_MISSING` | manifest | manifest mutations | workflow | none | ci_enforced_in_architect |
| A-R17 | Build Tree remains primary Architect product | lossy handoff | semantic fidelity contract | Build Tree fixture | `A_TREE_*` | voice assistant fixture | collapsed cases | workflow | none | ci_enforced_in_architect |
| A-R18 | source semantic roles must map to tree nodes | omitted content | semantic coverage fixture | Build Tree fixture | `A_TREE_MISSING_SOURCE_ROLE` | voice assistant fixture | missing role case | workflow | none | ci_enforced_in_architect |
| A-R19 | unauthorized role collapse is rejected | lossy tree | semantic fidelity contract | Build Tree fixture | `A_TREE_UNAUTHORIZED_ROLE_COLLAPSE` | voice assistant fixture | collapse case | workflow | none | ci_enforced_in_architect |
| A-R20 | synthetic reference cannot be real export | false evidence | fixture notice | fixture metadata | `A_TREE_SYNTHETIC_LABELED_REAL` | voice assistant fixture | synthetic-labeled-real | workflow | none | ci_enforced_in_architect |
| A-R21 | user summary cannot replace machine artifact | missing payload | adoption doc | Build Tree fixture | `A_TREE_SUMMARY_REPLACED_MACHINE_ARTIFACT` | voice assistant fixture | summary case | workflow | none | ci_enforced_in_architect |
| A-R22 | Project Gate common contract cannot be redefined locally | contract drift | vendor doc | vendored schema + lock | `A_PG_*` | vendored bytes | hash/path cases | reusable workflow | none | ci_enforced_in_architect |
| A-R23 | vendored contract must match immutable bytes | hash drift | vendor doc | lock | `A_PG_CONTRACT_BYTE_MISMATCH` | exact vendored schema | mismatch cases | reusable workflow | none | ci_enforced_in_architect |
| A-R24 | moving Project Gate refs are forbidden | moving target | lock doc | lock | `A_PG_LOCK_MOVING_REF` | lock file | moving ref case | reusable workflow | none | ci_enforced_in_architect |
| A-R25 | silent fallback is forbidden | wrong artifact accepted | Producer Export | export fixture | `A_EXPORT_SILENT_FALLBACK_FORBIDDEN` | blocked export | silent fallback case | workflow | none | ci_enforced_in_architect |
| A-R26 | legacy handoff remains available | legacy regression | manifest doc | manifest | `A_MANIFEST_LEGACY_OUTPUT_NOT_PRESERVED` | manifest | mutation cases | workflow | none | schema_backed |
| A-R27 | legacy builder feed remains available | legacy regression | manifest doc | manifest | `A_MANIFEST_LEGACY_OUTPUT_NOT_PRESERVED` | manifest | mutation cases | workflow | none | schema_backed |
| A-R28 | Architect adoption does not prove CE acceptance | readiness overclaim | adoption doc | payload boundaries | status review | blocked export | none | human review | none | prose_only |
| A-R29 | Architect adoption does not prove Project Gate runtime integration | runtime overclaim | adoption doc | status docs | status review | blocked export | none | human review | none | prose_only |
| A-R30 | Architect adoption does not prove real Elementor execution | evidence overclaim | capability registry | registry | registry check | registry entries | none | workflow | none | ci_enforced_in_architect |
