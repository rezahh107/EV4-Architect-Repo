# Architect Conversational Stage Output Contract v1

```yaml
contract_id: ev4-architect-conversational-stage-output
contract_version: 1.0.0
owner_repository: rezahh107/EV4-Architect-Repo
artifact_role: model_authored_evaluator_input
base_schema: ev4-architect-conversational-stage-output-base@1.0.0
```

## Purpose

After each Architect Stage, the model emits one complete standalone JSON Stage Output that can be passed directly to the existing official Architect runtime for that Stage.

This contract does not replace `ev4-architect-stage-result@1.0.0`, the Pipeline Manifest, `evaluate_stage`, or Run State. It defines model-authored evaluator input only.

## Authority chain

```text
model-authored domain Stage content
→ Runtime-compatible Stage Output
→ current evaluator-owned Run State
→ scripts/architect_quality_runtime.py#evaluate_stage
→ evaluator-derived Stage Result
→ Manifest-defined legal successor
```

The Pipeline Manifest remains the sole authority for Stage identity, version, ordinal, mandatory status, required quality checks, allowed `not_applicable` checks, evaluation mode, legal successor, and terminal identity.

The official runtime remains the sole authority for Stage status, quality-check derivation, blocking issues, continuation, Candidate lock, Unknown ledger, Build Tree and Implementation digests, fidelity, final-audit blocking, terminal validation, Stage Result, and Run State.

## Direct artifact shape

The artifact is the same top-level Stage Output object consumed by the Runtime. Do not add an `envelope` or `stage_output` wrapper.

Common required fields:

```yaml
required_common_fields:
  - run_id
  - stage_id
  - stage_version
  - check_evidence
  - unknown_introductions
  - unknown_resolutions
  - blockers
```

`decision_input`, `canonical_content`, `research_disposition`, `final_audit_findings`, `project_gate_payload`, and other Runtime-supported fields are conditional and Stage-specific. Do not emit meaningless placeholders.

## Stage-specific content

The complete Stage-owned content must be preserved. A summary cannot replace canonical Stage content.

- `/recommend` carries the actual selected-candidate decision input required by the Runtime.
- `/build-tree` carries the actual canonical Build Tree content.
- `/implementation` carries the actual canonical Implementation content and the approved Build Tree representation required by the Runtime.
- `/final-audit` carries actual final-audit findings.
- `/handoff-export` carries the actual handoff content required by the active Stage protocol.
- `/project-gate-export` carries the actual canonical `project_gate_payload` required by the official terminal evaluator.

Stage-specific semantics are defined by existing executable Runtime, Stage protocols, contracts, Schemas, and validators. This contract does not duplicate them.

## Unknown lifecycle

Every Stage Output explicitly emits `unknown_introductions` and `unknown_resolutions`, including empty arrays when no change is proposed.

Unknown introduction records contain:

```yaml
unknown_id:
statement:
downstream_critical:
```

Runtime-supported extension fields may be added.

Unknown resolution requests contain:

```yaml
unknown_id:
resolution_type:
note:
evidence_ref: required when the Runtime requires it
```

An active Unknown cannot disappear through omission. Resolution uses only Runtime-supported resolution types. Downstream-critical resolution preserves the required resolvable evidence reference. Missing evidence must not be converted into an exact value. This contract does not create a second Unknown ledger.

## Authority boundary

Model-authored:

- Stage Output;
- structured check-evidence records;
- complete Stage-specific content;
- Unknown introductions;
- explicit Unknown resolution requests;
- non-authorizing blockers.

Evaluator-derived:

- Stage Result;
- `stage_status`;
- `quality_checks`;
- `blocking_issues`;
- `next_stage`;
- Run State;
- Candidate lock state;
- Build Tree and Implementation digests;
- continuation decision;
- terminal validation result.

A conversational Stage Output must not author top-level authority fields. The base Schema forbids the live Runtime authority fields and the additional conversational authority aliases documented there.

## Delivery behavior

Preferred delivery is an actual downloadable UTF-8 `.json` file.

When the environment cannot create an attachment, return:

1. one exact JSON code block;
2. one explicit proposed filename;
3. a truthful statement that no attachment was created.

Never claim that a file was attached or saved when it was not.

Recommended filename: `NN-stage-name.json`. The filename is convenience only. `run_id`, `stage_id`, and `stage_version` in file content remain authoritative.

A concise human-readable explanation may accompany the JSON, but it is not Stage Output, Stage Result, or continuation authority and cannot claim official `PASS` without an evaluator-derived Stage Result.

## Multi-Stage continuation

Multiple reasoning-only Stages may continue in one response when the official Runtime permits it, but each Stage emits a separate immutable Stage Output artifact. A later artifact must not retroactively replace or modify an earlier artifact.

Before evaluation, presentation may use only:

```yaml
stage_status: not_evaluated
claim_basis: model_authored_stage_output_only
```

These labels are non-authorizing.

## Normative instruction mirror

The exact block between the markers below is mirrored in active Project Instructions and active release-pack Stage instructions. Tests fail on drift.

<!-- BEGIN ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->
After completing each Stage, produce one complete standalone Runtime-compatible Stage Output JSON artifact for that Stage.

Use contract `ev4-architect-conversational-stage-output@1.0.0` and base Schema `ev4-architect-conversational-stage-output-base@1.0.0`. The JSON is model-authored evaluator input, not an evaluator-derived Stage Result.

Use the exact `run_id`, Manifest `stage_id`, Manifest `stage_version`, and exact Manifest-owned `check_evidence` keys. Preserve complete Stage-specific canonical content, active Unknowns, and the locked Candidate. A summary must not replace canonical content. Do not author official `PASS`, `stage_status`, `quality_checks`, `next_stage`, continuation authority, or official digests.

Emit one separate Stage Output artifact per Stage. A later Stage artifact must not replace or modify an earlier artifact. Until the official Runtime evaluates an artifact, any presentation label is only `stage_status: not_evaluated` with `claim_basis: model_authored_stage_output_only` and is non-authorizing.

Prefer an actual UTF-8 `.json` attachment. When attachment creation is unavailable, return one exact JSON code block, provide an explicit proposed filename, and state truthfully that no attachment was created.
<!-- END ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->

## Validation

```bash
python scripts/check-architect-conversational-stage-output.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p no:cacheprovider -q tests/test_architect_conversational_stage_output.py
```

Base-Schema success proves common structure only. It does not prove Stage pass, continuation, fidelity, terminal success, or production readiness.