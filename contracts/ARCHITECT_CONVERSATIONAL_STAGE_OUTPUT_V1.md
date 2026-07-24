# Architect Conversational Stage Output Contract v1

```yaml
contract_id: ev4-architect-conversational-stage-output
contract_version: 1.0.0
owner_repository: rezahh107/EV4-Architect-Repo
artifact_role: model_authored_evaluator_input
base_schema: ev4-architect-conversational-stage-output-base@1.0.0
```

## Purpose

After each Architect Stage, the model emits one complete standalone JSON Stage Output that can be passed directly to the existing official Architect Runtime for that Stage.

This contract does not replace `ev4-architect-stage-result@1.0.0`, the Pipeline Manifest, `evaluate_stage`, Run State, the Stage Claim Guard, or the Runtime Payload Assembler. It defines model-authored evaluator input only.

## Authority chain

```text
model-authored Stage content and non-authorizing check claims
→ conversational Base Schema
→ Stage Claim Guard deterministic predicates
→ evaluator-derived Stage Result and completion class
→ evaluator-owned Run State
→ Manifest-defined legal successor
→ Runtime-issued terminal Payload
→ existing Producer Gate exporter
→ Runtime-derived handoff
```

The Pipeline Manifest remains the sole authority for Stage identity, version, order, required quality-check keys, evaluation mode, legal successor, and terminal identity.

The official Runtime remains the sole authority for Base-Schema enforcement, check outcomes, completion class, Stage status, blocking issues, continuation, Candidate lock, Unknown ledger, Build Tree and Implementation digests, final-audit acceptance, handoff eligibility, terminal Payload, synthetic status, producer provenance, export validation, and Stage Result.

## Direct artifact shape

The artifact is the same top-level Stage Output object consumed by the Runtime. Do not add an `envelope` or `stage_output` wrapper.

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

`decision_input`, `canonical_content`, `research_disposition`, `final_audit_findings`, and other Stage-owned fields are conditional. Do not emit meaningless placeholders.

## Non-authorizing check claims

Every exact Manifest-owned `check_evidence` key carries a model claim, not an official result:

```yaml
claim: what the model believes was addressed
reason: why the model believes it was addressed
evidence_refs: optional Stage-owned references
limitations: optional explicit limitations
```

`result` is a deprecated legacy field. It may parse for historical compatibility, but the Runtime ignores it and records the affected keys in `runtime_context.legacy_check_results_ignored`. A model-authored `pass`, a non-empty reason, or a model-authored evidence reference never determines `quality_checks`, `stage_status`, continuation, or handoff.

Every Manifest check is explicitly classified as one of:

```text
DETERMINISTIC_PREDICATE
STRUCTURAL_COMPLETENESS
ATTRIBUTED_REASONING_ONLY
EXTERNAL_BOUNDARY
```

No required check is defined as “model supplied pass.”

## Completion classes

The Runtime derives one truthful completion basis:

```yaml
reasoning_complete:
  meaning: required structure and deterministic consistency checks passed
  does_not_mean: the analytical reasoning is objectively proven correct

validated_pass:
  meaning: consequential Runtime predicates or the external terminal boundary passed
```

`stage_status` remains compatible, but only the evaluator derives it. `completion_class` does not create a second evaluator or Stage inventory.

## Stage-specific content

Complete Stage-owned content must be preserved. A summary cannot replace canonical content.

- `/recommend` proposes a Candidate; Runtime verifies it against prior architecture and score-audit outputs and establishes the lock.
- `/build-tree` carries the canonical Build Tree.
- `/implementation` carries canonical Implementation content and the embedded approved Build Tree.
- `/final-audit` carries actual findings; Runtime derives acceptance.
- `/handoff-export` carries presentation/package content; Runtime derives eligibility.
- `/project-gate-export` carries only a non-authoritative export request or presentation note. It must not carry `project_gate_payload`.

The Runtime assembles the official `ev4-architect-stage-payload@1.0.0` from evaluated Stage Outputs, derived Stage Results, Run State, and Runtime-owned `RunContext`.

## Runtime Context and terminal truth

`RunContext.source_kind` is created by the host Runtime and is never model-authored:

```text
live_conversation
fixture
example
test_vector
```

The Runtime derives:

```python
synthetic = source_kind != "live_conversation"
```

Fixture, example, and test-vector contexts may expose `functional_eligibility.would_allow: true`, but actual `handoff_allowed` remains false. A valid live-conversation context may reach an allowed handoff after every functional gate passes.

The model must not author `source_kind`, authoritative `synthetic`, producer Git provenance, terminal Payload lineage, Payload digests, export identity, functional eligibility, or handoff status.

## Unknown lifecycle

Every Stage Output explicitly emits `unknown_introductions` and `unknown_resolutions`, including empty arrays.

An active Unknown cannot disappear through omission. Downstream-critical resolution requires an evidence reference present in `RunContext.verified_evidence_refs`. A model-authored evidence reference is not verified merely because it is non-empty. This contract does not create a second Unknown ledger.

## Authority boundary

Model-authored:

- Stage-specific content;
- non-authorizing check claims and reasons;
- Unknown introductions;
- explicit Unknown resolution requests;
- non-authorizing blockers;
- terminal export request/presentation note.

Evaluator-derived:

- Base-Schema validity;
- check outcomes and evaluation basis;
- `completion_class` and `stage_status`;
- blocking issues and continuation;
- Run State and Candidate lock;
- Unknown ledger;
- Build Tree and Implementation digests;
- Final Audit acceptance and handoff eligibility;
- Runtime-issued terminal Payload;
- Runtime Context and synthetic status;
- producer provenance from the actual checkout;
- Project Gate export and final handoff.

A conversational Stage Output must not author top-level authority fields. Runtime and Base Schema use the same Schema-derived forbidden set.

## Delivery behavior

Preferred delivery is an actual downloadable UTF-8 `.json` file. When attachment creation is unavailable, return one exact JSON code block, one proposed filename, and a truthful statement that no attachment was created.

Recommended filename: `NN-stage-name.json`. Filename is convenience only; identity remains inside the JSON.

## Multi-Stage continuation

Multiple reasoning Stages may continue when the Runtime permits it, but every Stage emits a separate immutable Stage Output. Before evaluation, presentation may use only:

```yaml
stage_status: not_evaluated
claim_basis: model_authored_stage_output_only
```

These labels are non-authorizing.

## Normative instruction mirror

The exact block between the markers below is mirrored in active Project Instructions and release-pack Stage instructions. Tests fail on drift.

<!-- BEGIN ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->
After completing each Stage, produce one complete standalone Runtime-compatible Stage Output JSON artifact for that Stage.

Use contract `ev4-architect-conversational-stage-output@1.0.0` and base Schema `ev4-architect-conversational-stage-output-base@1.0.0`. The JSON is model-authored evaluator input, not an evaluator-derived Stage Result.

Use the exact `run_id`, Manifest `stage_id`, Manifest `stage_version`, and exact Manifest-owned `check_evidence` keys. Each check record carries a non-authorizing `claim` and `reason`; do not author an official check result. Preserve complete Stage-specific canonical content, active Unknowns, and the locked Candidate. A summary must not replace canonical content.

Do not author official `PASS`, `stage_status`, `quality_checks`, `completion_class`, `next_stage`, continuation authority, official digests, `RunContext`, `source_kind`, authoritative `synthetic`, producer provenance, or `project_gate_payload`. At `/project-gate-export`, request export only; the Runtime assembles the official terminal Payload from the evaluated Run.

Emit one separate Stage Output artifact per Stage. A later Stage artifact must not replace or modify an earlier artifact. Until the official Runtime evaluates an artifact, any presentation label is only `stage_status: not_evaluated` with `claim_basis: model_authored_stage_output_only` and is non-authorizing.

Prefer an actual UTF-8 `.json` attachment. When attachment creation is unavailable, return one exact JSON code block, provide an explicit proposed filename, and state truthfully that no attachment was created.
<!-- END ARCHITECT_CONVERSATIONAL_STAGE_OUTPUT_V1 -->

## Validation

```bash
python scripts/check-architect-conversational-stage-output.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p no:cacheprovider -q \
  tests/test_architect_conversational_stage_output.py \
  tests/test_architect_conversational_stage_output_root_complete.py \
  tests/test_architect_runtime_truth_spine.py
```

Base-Schema success proves common structure only. `reasoning_complete` proves bounded Runtime completeness and consistency only; it does not prove objective analytical correctness, downstream acceptance, or production readiness.
