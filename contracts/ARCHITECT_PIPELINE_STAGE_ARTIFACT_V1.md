# Architect Pipeline Stage Artifact v1

Status: active additive_nonbreaking intermediate contract
Schema identity: `ev4-architect-pipeline-stage-artifact@1.1.0`
Schema path: `schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json`
Receipt schema: `ev4-architect-stage-validation-receipt@1.1.0`
Validator: `scripts/check-architect-pipeline-stage-boundary.py`

## Purpose

This contract owns intermediate Architect pipeline Stage Artifacts for `/decompose`, `/architectures`, `/score-evidence`, and `/score-audit`. It does not replace `ev4-architect-stage-payload@1.0.0`, which remains the final Architect-to-Project-Gate payload.

## Envelope

Every artifact uses one common envelope:

```yaml
artifact_schema: ev4-architect-pipeline-stage-artifact@1.1.0
artifact_id: stable artifact identity
run_id: stable run identity
stage_id: /decompose | /architectures | /score-evidence | /score-audit
stage_version: producer stage contract version
artifact_revision: integer revision
source_artifacts: []
payload: stage-specific payload
```

`source_artifacts[]` binds prior producer evidence by `artifact_id`, `artifact_schema`, exact `artifact_sha256`, `validation_receipt_id`, `validation_status`, and `source_stage`.

## Boundary rules

- ASB-R01: `/decompose` must include every canonical Stage 2 section.
- ASB-R02: Stage 2 unknown IDs must be stable and unique.
- ASB-R03: `/architectures` must include the Architecture Coverage Matrix for A01-A08.
- ASB-R04: `/architectures` must include a complete Unknown Propagation Ledger for every Stage 2 unknown.
- ASB-R05: downstream stages must not reconstruct, normalize, or infer missing required upstream artifacts.
- ASB-R06: a next-stage Anchor requires a valid machine receipt.
- ASB-R07: exact artifact digest and lineage must match.
- ASB-R08: `/score-audit` audits rather than repairs and cannot select or lock a Candidate.

## Runtime-unavailable behavior

If the executable validator is available, write the canonical Artifact, execute the validator, obtain the receipt, and emit a receipt-bound `NEXT STAGE ANCHOR` only after `status=valid`.

If execution is unavailable, do not claim machine validation, do not emit a validated `NEXT STAGE ANCHOR`, return `validation_required` or `insufficient_evidence`, provide the exact manual validator command, and preserve the Artifact for external validation.

## Anchor hash scope

`ev4-stage-anchor@1.2.0` is a separate handoff artifact produced after Stage Artifact validation. The Stage Artifact SHA-256 is calculated over the exact UTF-8 bytes of the Stage Artifact file only; the anchor is not embedded in that hashed file and is not part of the artifact digest scope. This avoids a circular design where a file would need to contain the SHA-256 or Receipt ID derived from its own complete bytes.

## Commands

Single-stage validation without upstream lineage, valid for `/decompose`:

```bash
python scripts/check-architect-pipeline-stage-boundary.py --artifact path/to/decompose.json --write-receipt path/to/decompose.receipt.json
```

Standalone validation for Stages 3-5 requires explicit upstream artifact and receipt inputs:

```bash
python scripts/check-architect-pipeline-stage-boundary.py \
  --artifact path/to/architectures.json \
  --upstream-artifact path/to/decompose.json \
  --upstream-receipt path/to/decompose.receipt.json \
  --write-receipt path/to/architectures.receipt.json
```

Canonical sequence validation can deterministically write every generated receipt and separate receipt-bound anchor:

```bash
python scripts/check-architect-pipeline-stage-boundary.py \
  --sequence path/to/sequence-directory \
  --write-receipts path/to/receipts-directory \
  --write-anchors path/to/anchors-directory \
  --format json
```

Validate a separate anchor against authoritative generated evidence:

```bash
python scripts/check-architect-pipeline-stage-boundary.py \
  --anchor path/to/architectures.anchor.json \
  --anchor-source-artifact path/to/architectures.json \
  --anchor-source-receipt path/to/architectures.receipt.json
```

Fixture-suite validation:

```bash
python scripts/check-architect-pipeline-stage-boundary.py validate-run --sequence fixtures/architect-pipeline-stage-boundary/valid/complete-sequence --output /tmp/ev4-validation-bundle --format json
```


## Canonical Run Validation Transaction

The production-authoritative command is:

```bash
python scripts/check-architect-pipeline-stage-boundary.py \
  validate-run \
  --sequence <artifact-directory> \
  --output <validation-bundle-directory> \
  --format json
```

Receipts are generated outputs only. Caller-supplied receipts, anchors, boundary records, and manifests are untrusted assertions and do not authorize continuation. Machine authorization derives only from a valid generated `ev4-architect-validation-bundle@1.0.0` manifest and its generated `ev4-stage-boundary-record@1.0.0` records. User handoff anchors remain model-continuity context and must not independently authorize continuation.

Current schema identities for new generated evidence are `ev4-architect-pipeline-stage-artifact@1.1.0`, `ev4-architect-stage-validation-receipt@1.1.0`, `ev4-stage-boundary-record@1.0.0`, `ev4-stage-anchor@1.2.0`, and `ev4-architect-validation-bundle@1.0.0`. Historical v1.0 stage artifacts and receipts may be read only as historical evidence; they are not current authorization records.
