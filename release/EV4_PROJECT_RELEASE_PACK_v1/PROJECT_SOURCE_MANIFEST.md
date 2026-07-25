# Project Source Manifest — EV4 Release Pack v1

Status: release_candidate_quality_first_runtime  
Version: 1.3.0  
Date: 2026-07-23

## Core Release Files

```text
release/EV4_PROJECT_RELEASE_PACK_v1/PROJECT_INSTRUCTIONS_FINAL.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CORE_CONTRACTS_BUNDLE.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_STAGE_PROTOCOLS_BUNDLE.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_EXAMPLES_AND_CALIBRATION_BUNDLE.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md
```

## Canonical Runtime Sources

```text
AGENTS.md
README.md
STATUS.md
02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
contracts/ARCHITECT_STAGE_RESULT_V1.md
schemas/ev4-architect-stage-result.v1.schema.json
manifests/architect-conversation-bootstrap.v1.json
schemas/architect-conversation-bootstrap.v1.schema.json
manifests/architect-pipeline-manifest.v1.json
schemas/ev4-architect-pipeline-manifest.v1.schema.json
scripts/architect_quality_runtime.py
scripts/check-architect-quality-runtime.py
fixtures/architect-quality-runtime/valid/full-pipeline.json
tests/test_architect_quality_runtime.py
scripts/check-architect-bootstrap.py
tests/test_architect_bootstrap_semantics.py
```

## Conversational Stage Output Sources

```text
contracts/ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1.md
schemas/architect-conversational-stage-output-base.v1.schema.json
scripts/architect_conversational_stage_output.py
scripts/check-architect-conversational-stage-output.py
examples/conversational-stage-output/**
fixtures/conversational-run/valid/minimal-complete-run/**
fixtures/conversational-run/valid/terminal/project-gate-export.json
tests/test_architect_conversational_stage_output.py
release/EV4_PROJECT_RELEASE_PACK_v1/CONVERSATIONAL_STAGE_OUTPUT_UPLOAD_SET.v1.json
```

These sources define and validate direct model-authored Stage Output input. They do not add a Pipeline, Stage inventory, evaluator, Run State, continuation authority, or per-Stage Schema family.

## Runtime Authority Model

```text
Pipeline topology/order/version/successor/terminal
→ manifests/architect-pipeline-manifest.v1.json

Normal internal continuation
→ ev4-architect-stage-result@1.0.0

Continuation alignment for existing detailed sources
→ contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md

Optional deterministic transaction capability
→ manifests/architect-stage-validation-profiles.v1.json

Final Architect handoff
→ ev4-architect-stage-payload@1.0.0 and Producer Gate Export contracts
```

Conversational Stage Output structural precheck:

```text
ev4-architect-conversational-stage-output-base@1.0.0
→ common structure and complete evaluator-owned top-level field rejection
→ no Stage pass or continuation claim
```

The Runtime classifies every top-level `ev4-architect-stage-result@1.0.0` property as either an explicitly shared Stage Output field or evaluator-owned. The conversational Base Schema carries the exact mechanically verified evaluator-owned set; any drift fails validation.

## Existing Detailed Sources Retained

All active Stage documents, hardening patches, RAG/TUYA source-access references, rubric files, schemas, validators, fixtures, examples, and debug contracts remain part of the repository source set.

Their non-conflicting quality controls remain active. Only clauses that make Anchor, Bundle, independent regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, or repository maintenance prerequisites for ordinary continuation are superseded.

## Optional Audit and Historical Tooling

```text
manifests/architect-stage-validation-profiles.v1.json
contracts/ARCHITECT_PIPELINE_STAGE_ARTIFACT_V1.md
contracts/STAGE_ANCHOR_CONTRACT.md
schemas/ev4-stage-anchor.v1.4.schema.json
schemas/ev4-architect-validation-bundle.v1.2.schema.json
scripts/architect_validation_*.py
scripts/check-architect-validation-profiles.py
scripts/check-architect-pipeline-stage-boundary.py
fixtures/architect-pipeline-stage-boundary/**
tests/test_architect_validation_profiles.py
tests/test_architect_pipeline_stage_boundary_validator.py
tests/test_architect_validation_transaction_mutations.py
```

These sources support repository audits, deterministic regression, compatibility evidence, and historical readability. They are not normal project-run transition tickets.

## Legacy Compatibility Outputs

Legacy Builder Feed remains preserved but is not canonical Project Gate export.

## Validation State

```yaml
quality_first_full_pipeline_fixture:
  status: authored_pending_exact_head_ci
bootstrap_quality_runtime_alignment:
  status: authored_pending_exact_head_ci
conversational_stage_output_contract:
  status: repaired_pending_exact_head_ci_and_fresh_rereview
conversational_prefinal_run_fixture:
  status: authored_pending_exact_head_ci
conversational_terminal_fixture:
  status: full_runtime_validation_authored_pending_exact_head_ci
conversational_release_upload_set:
  status: deterministic_manifest_and_schema_validation_authored_pending_exact_head_ci
optional_transaction_segment:
  status: preserved
final_project_gate_export:
  status: fail_closed_contract_preserved
live_chat_runtime_enforcement:
  status: insufficient_evidence
live_elementor_rendering:
  status: not_validated
real_elementor_export_json_or_EDIS:
  status: not_validated
downstream_real_run_acceptance:
  status: insufficient_evidence
production_readiness:
  status: not_claimed
```

## Recommended Upload Set

The exact minimum set is machine-readable at:

```text
release/EV4_PROJECT_RELEASE_PACK_v1/CONVERSATIONAL_STAGE_OUTPUT_UPLOAD_SET.v1.json#minimum_upload_paths
```

It contains:

```text
the five core release files
manifests/architect-pipeline-manifest.v1.json
contracts/ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1.md
schemas/architect-conversational-stage-output-base.v1.schema.json
all registered examples/conversational-stage-output/*.json files
```

The release validator derives every Stage ID, exact Stage version, and exact required `check_evidence` key from the live Pipeline Manifest, verifies the Contract and Base Schema identities, checks every registered example, and proves that a structurally valid common Stage Output can be constructed for every Manifest Stage. It does not manually duplicate the Manifest inventory.

Optional add-ons remain available according to the intended workflow.
