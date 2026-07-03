# Schemas

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
