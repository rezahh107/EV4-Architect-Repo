# Architect Pipeline Stage Validation Transaction

Status: active

## Current carrier identities

```yaml
artifact_schema: ev4-architect-pipeline-stage-artifact@1.1.0
receipt_schema: ev4-architect-stage-validation-receipt@1.1.0
failure_event_schema: ev4-architect-validation-failure-event@1.0.0
boundary_schema: ev4-stage-boundary-record@1.1.0
anchor_schema: ev4-stage-anchor@1.4.0
bundle_schema: ev4-architect-validation-bundle@1.2.0
```

Historical `ev4-stage-boundary-record@1.0.0`, `ev4-stage-anchor@1.1.0`, `ev4-stage-anchor@1.2.0`, `ev4-stage-anchor@1.3.0`, `ev4-architect-validation-bundle@1.0.0`, and `ev4-architect-validation-bundle@1.1.0` are non-authorizing evidence only.

Pipeline topology and Stage versions are owned only by `manifests/architect-pipeline-manifest.v1.json`. Executable validation capability is owned only by `manifests/architect-stage-validation-profiles.v1.json`. Neither the Validator nor this contract maintains another authoritative transition or Stage-version table.

## Production authority

Only these commands participate in production authorization:

```bash
python scripts/check-architect-pipeline-stage-boundary.py validate-run \
  --sequence <artifact-directory> \
  --output <validation-bundle> \
  --format json

python scripts/check-architect-pipeline-stage-boundary.py validate-bundle \
  --bundle <validation-bundle> \
  --format json
```

`validate-run` generates the complete deterministic transaction. `validate-bundle` independently reconstructs it from the exact contained Artifact bytes and compares every deterministic carrier byte-for-byte. Caller-authored Receipts, Failure Events, Boundaries, Anchors, or Manifests are assertions, not authority.

Standalone diagnostics never generate authority files and always expose:

```yaml
status: invalid
diagnostic_only: true
authorization_valid: false
generated_authorization_files: []
```

The removed legacy file-producing flags are `--write-receipt`, `--write-receipts`, and `--write-anchors`.


## Executable Validation Profiles

The currently implemented transaction profiles, with Stage versions derived from the Manifest, are:

```yaml
/decompose: 1.0.0
/architectures: 1.1.0
/score-evidence: 1.3.0
/score-audit: 1.2.0
```

The Artifact Schema conditionals, semantic handlers, and fixtures must agree with the Registry's implemented Stage set. A Manifest Stage whose Validation Profile is not `full_transaction_implemented` produces no authorization Bundle. A legal edge never bypasses a blocked profile.

## Unknown lifecycle

Stage 3 may preserve active unknown states or close an unknown only through a supported inactive state: `resolved_with_evidence`, `not_applicable`, or `stale`. Inactive records require a non-empty resolution reason and named evidence; `resolved_with_evidence` additionally requires exact `resolving_evidence_refs` contained in `evidence_refs`. Active unknowns propagate to Stage 4. Valid inactive records remain audit evidence and are excluded from the Stage 4 active uncertainty register. Silent disappearance or evidence-free resolution fails at `/architectures`.

## Structural preflight failures

Missing Stages, duplicate Stages, filename/Stage mismatches, malformed JSON, and unrecognized Stage inputs are structural preflight failures. They return one deterministic structured result with:

```yaml
bundle_integrity_status: not_produced
run_validation_status: invalid
authorization_valid: false
output_published: false
```

No Bundle directory or partial carrier set is published. Semantic failures with exact failing Artifact bytes continue to produce a complete independently verifiable Failure Bundle.

## Stage 4 payload lineage

`/score-evidence.payload.validated_upstream_artifact_refs` contains exactly one reference and must equal the regenerated `/architectures` `artifact_ref` in every field. The independent top-level `source_artifacts` check remains required; one valid duplicate lineage surface cannot compensate for a forged or stale other surface.

## Output ownership and atomic publication

Before generation, the Validator resolves repository, Sequence, and output paths. It rejects filesystem root, repository root, every Sequence/output overlap or alias, and every unrelated existing directory. Replacement is permitted only when the existing directory has the exact current Validator-owned `manifest.json` sentinel. Generation occurs in a temporary sibling and is atomically published only after all carriers pass validation. Failed generation leaves no new partial output and does not replace an existing owned Bundle.

## State machines

Success:

```text
ARTIFACT_SEQUENCE_DISCOVERED
→ SEQUENCE_STRUCTURE_VALID
→ RUN_ID_CONTINUITY_VALID
→ ARTIFACT_SCHEMA_VALID
→ ARTIFACT_SEMANTICS_VALID
→ PREDECESSOR_LINEAGE_VALID
→ RECEIPT_GENERATED
→ SUCCESS_BOUNDARY_GENERATED
→ NEXT_STAGE_ANCHOR_GENERATED
→ VALID_BUNDLE_MANIFEST_GENERATED
→ BUNDLE_INDEPENDENTLY_REGENERATED
→ NEXT_STAGE_AUTHORIZED
```

Failure:

```text
ARTIFACT_SEQUENCE_DISCOVERED
→ VALIDATION_FAILED_AT_STAGE
→ INVALID_RECEIPT_GENERATED
→ FAILURE_EVENT_GENERATED
→ REPAIR_BOUNDARY_GENERATED
→ REPAIR_ANCHOR_GENERATED
→ INVALID_BUNDLE_MANIFEST_GENERATED
→ FAILURE_BUNDLE_INDEPENDENTLY_REGENERATED
→ NEXT_STAGE_BLOCKED
```

## Failure ownership

`failed_stage` is where validation detected the defect. `repair_target_stage` is the earliest owning Stage that must change. They are independent fields and may differ, for example:

```yaml
failed_stage: /architectures
repair_target_stage: /decompose
```

Every repair-causing diagnostic includes both `stage_id` and `repair_target_stage`. Selection is deterministic by pipeline order, explicit diagnostic priority, then diagnostic code.

## Bundle status dimensions

```yaml
bundle_integrity_status: valid | invalid
run_validation_status: valid | invalid | insufficient_evidence
authorization_valid: true | false
```

A truthfully reproduced failed Run has valid Bundle integrity and no authorization. `validate-bundle` exits `0` for either a valid success Bundle or a valid failure Bundle, and exits `1` only for malformed, forged, incomplete, or non-reproducible Bundle evidence.

## Failure Bundle invariant

A failure Bundle contains the validated prefix, the exact failing Artifact and invalid Receipt, exactly one `failure-event.json`, exactly one Repair Boundary, and exactly one Repair Anchor. It contains no Success Boundary, no `NEXT_STAGE_ANCHOR`, and no non-null `authorized_next_stage`.

## Determinism

Carrier identity excludes timestamps and other observational metadata. Artifact bytes are copied unchanged. JSON evidence is serialized with stable key ordering and newline termination. Both success and failure Bundles must regenerate byte-for-byte.

## Enforcement boundary

Schemas, Validator logic, deterministic generation, mutation tests, exact-Head CI, downstream rejection, and independent human review provide enforcement. Documentation, comments, examples, names, and PR prose do not authorize continuation.
