# Schemas

## Architect Stage Validation Authority

Current machine-readable authority is split deliberately:

```text
manifests/architect-pipeline-manifest.v1.json
  sole topology and Stage-version authority
manifests/architect-stage-validation-profiles.v1.json
  Validation capability and grounding status only
schemas/architect-stage-validation-profiles.v1.schema.json
  strict Registry shape
```

Current generated carrier schemas are `ev4-stage-anchor@1.4.0` in
`schemas/ev4-stage-anchor.v1.4.schema.json` and
`ev4-architect-validation-bundle@1.2.0` in
`schemas/ev4-architect-validation-bundle.v1.2.schema.json`. Historical Anchor
1.1.0–1.3.0 and Bundle 1.1.0 records remain readable, non-authorizing evidence.
An Anchor alone authorizes nothing.

## Architect Project Gate Payload

Active Architect-owned schema added by this migration step:

```text
schemas/ev4-architect-stage-payload.v1.schema.json
schema identity: ev4-architect-stage-payload@1.0.0
owner: rezahh107/EV4-Architect-Repo
```

This schema defines the Architect-specific payload that may be wrapped inside the common Project Gate Stage Evidence Bundle envelope.

Legacy schemas remain available and are not retired in this PR:

```text
schemas/ev4-architect-output-contract.v1.schema.json
schemas/ev4-architect-builder-feed-export.schema.json
schemas/ev4-builder-context-package.schema.json
```

The legacy builder-facing exports are migration-pending compatibility surfaces. They are not the new canonical Architect Stage Evidence payload.
