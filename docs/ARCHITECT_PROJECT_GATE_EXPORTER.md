# Architect Project Gate Exporter

Status: `runtime_internal_only`

> Direct Project Gate export from a caller-supplied Payload file is unsupported and has been removed.

## Supported authority chain

```text
model-authored Stage Output JSON files
→ Stage-QC evaluator replay
→ evaluator-derived Stage Results and Runtime Run State
→ Runtime-issued canonical Architect Stage Payload
→ Runtime-internal Project Gate exporter and validator
→ Project Gate artifact and receipt
```

Authority ownership is explicit:

| Artifact | Authority |
|---|---|
| Stage Output | model-authored evidence |
| Stage Result | official evaluator-derived |
| Architect Stage Payload | Runtime-issued from replayed state |
| Project Gate artifact and receipt | exporter- and validator-issued |

The repository does not expose a `--payload` command, Payload-path argument,
compatibility entrypoint, preview command, Windows wrapper, WSL wrapper, or
lower-level raw-dictionary export API. A JSON object that merely matches the
Payload Schema cannot authorize Handoff.

## Runtime boundary

The terminal `/project-gate-export` transaction derives the Payload only from:

- contiguous Stage Output history;
- evaluator-derived Stage Results;
- Runtime Run State and RunContext;
- selected-candidate lock state;
- the Runtime Unknown ledger;
- the canonical Payload assembler;
- actual checkout provenance.

The internal exporter consumes a one-shot process-local capability bound to the
exact Payload object created during that terminal evaluator transaction. Copies,
mutations, decoded JSON files, fabricated provenance, and caller-populated
`runtime_issued`, `payload_status`, `synthetic`, or handoff fields are not
capabilities and fail closed.

## Preserved behavior

- Pipeline order and Stage count are unchanged.
- Stage Output contracts are unchanged.
- Stage-QC continues to consume model-authored Stage Output JSON files.
- Valid live Runtime execution may authorize Handoff.
- Synthetic Runtime execution cannot authorize actual Handoff.
- Architect/CE transition blockers remain fail-closed.
- Downstream-only obligations remain visible as `successful_with_flags`.
- Existing Project Gate artifact contracts remain unchanged.

## Historical exporter material

Earlier operator-exporter documents and status records describe a retired path.
They are historical evidence only and are not executable instructions. No
backward compatibility is provided for caller-supplied Payload export.
