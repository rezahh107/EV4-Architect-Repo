# Architect Project Gate Finalization

Status: `runtime_owned_public_api_pending_cross_repository_review`

> Direct Project Gate export from a caller-supplied Payload file is unsupported and has been removed.

## Supported authority chain

```text
complete ordered model-authored Stage Output history
→ Architect Runtime evaluator replay
→ evaluator-derived Stage Results
→ Runtime Run State
→ Runtime-issued canonical Architect Stage Payload
→ one-shot Payload capability consumption
→ Project Gate artifact construction
→ Contract and hash validation
→ Architect-owned atomic publication
→ deterministic finalization receipt
```

Authority ownership is explicit:

| Artifact | Authority |
|---|---|
| Stage Output | model-authored evidence |
| Stage Result | official evaluator-derived |
| Architect Stage Payload | Runtime-issued from replayed state |
| Project Gate artifact and receipt | Architect Runtime finalization |

## Official public API

The exact supported wrapper is:

```text
scripts/architect_quality_runtime.py
```

Its Project Gate publication surface is:

```python
finalize_project_gate(
    stage_outputs,
    *,
    run_context,
    repository_root,
    output_directory,
    git_provider=None,
)
```

The API accepts only the complete ordered set of twelve Stage Output objects, an
explicit `RunContext`, the actual Architect repository root, an output directory,
and the existing test-only Git provider where Runtime policy permits it.

It does not accept a Payload, Payload path, Stage Results, Run State, eligibility,
Handoff booleans, digests, validator output, provenance, receipt, or serialized
capability. Caller authority fields embedded in Stage Output objects fail closed
before replay.

## Single replay and internal execution

`finalize_project_gate()` performs one canonical full replay. During the terminal
`/project-gate-export` evaluation, one explicit internal execution object carries:

- the approved public Stage Result summary;
- the exact Runtime-issued Payload object;
- the complete Project Gate artifact;
- canonical Payload, bundle, and export hashes;
- validation and functional-eligibility results;
- actual checkout provenance.

The normal public Stage Result receives only the existing summary mapping. The
complete Payload and artifact are not returned as public Stage Result fields and
are not passed into a second exporter call. No process-wide artifact cache or
mutable publication side channel is used.

## Capability boundary

The terminal Runtime transaction derives the Payload only from:

- contiguous Stage Output history;
- evaluator-derived Stage Results;
- Runtime Run State and `RunContext`;
- selected-candidate lock state;
- the Runtime Unknown ledger;
- the canonical Payload assembler;
- actual checkout provenance.

The internal exporter consumes a one-shot process-local capability bound to the
exact Payload object and canonical digest created during that terminal execution.
Copies, mutations, decoded JSON files, externally replay-derived Payloads, and
fabricated authority fields cannot recreate or consume the capability.

## Publication outputs

Successful finalization writes, outside the Architect repository:

```text
architect-project-gate.json
architect-project-gate-receipt.json
```

Publication is no-replace and atomic at the destination filename. The complete
artifact is Contract-validated and hash-verified before publication. The Runtime
re-reads and verifies committed artifact bytes before publishing the receipt. A
receipt-write failure does not report successful finalization and removes only an
exact-byte artifact owned by that failed transaction. Existing caller-owned files
are never replaced or deleted.

Receipt Schema:

```text
schemas/ev4-architect-project-gate-finalization-receipt.v1.schema.json
```

## Result semantics

`ProjectGateFinalizationResult.finalization_succeeded` and
`ProjectGateFinalizationResult.handoff_allowed` are independent.

A valid blocked or synthetic transaction may produce:

```yaml
finalization_succeeded: true
handoff_allowed: false
publication_status: published_blocked
```

Invalid history, invalid terminal evidence, evaluator failure, Contract failure,
hash failure, or publication failure produces:

```yaml
finalization_succeeded: false
handoff_allowed: false
publication_status: not_published
```

## Removed paths

The repository exposes no `--payload` command, Payload-path argument,
compatibility entrypoint, preview command, Windows wrapper, WSL wrapper, or
lower-level raw-dictionary authorization API. A JSON object that merely matches
the Payload Schema cannot authorize Handoff.

## Preserved behavior

- Pipeline order and twelve-Stage count are unchanged.
- Stage Output contracts are unchanged.
- Stage-QC continues to consume model-authored Stage Output JSON files.
- Valid live Runtime execution may publish an allowed Handoff.
- Synthetic Runtime execution may publish only a blocked actual Handoff.
- Architect/CE transition blockers remain fail-closed.
- Downstream-only obligations remain visible as `successful_with_flags`.
- Existing Project Gate wire contracts remain unchanged.

## Historical exporter material

Earlier operator-exporter documents and status records describe a retired path.
They are historical evidence only and are not executable instructions. No
backward compatibility is provided for caller-supplied Payload export.
