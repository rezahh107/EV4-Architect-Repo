# Architect Pipeline Stage Artifact v1

Status: active additive_nonbreaking intermediate contract
Schema identity: `ev4-architect-pipeline-stage-artifact@1.0.0`
Schema path: `schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json`
Receipt schema: `ev4-architect-stage-validation-receipt@1.0.0`
Validator: `scripts/check-architect-pipeline-stage-boundary.py`

## Purpose

This contract owns intermediate Architect pipeline Stage Artifacts for `/decompose`, `/architectures`, `/score-evidence`, and `/score-audit`. It does not replace `ev4-architect-stage-payload@1.0.0`, which remains the final Architect-to-Project-Gate payload.

## Envelope

Every artifact uses one common envelope:

```yaml
artifact_schema: ev4-architect-pipeline-stage-artifact@1.0.0
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

## Commands

```bash
python scripts/check-architect-pipeline-stage-boundary.py --artifact path/to/artifact.json --write-receipt path/to/receipt.json
python scripts/check-architect-pipeline-stage-boundary.py --sequence path/to/sequence-directory --format json
python scripts/check-architect-pipeline-stage-boundary.py --fixtures
```
