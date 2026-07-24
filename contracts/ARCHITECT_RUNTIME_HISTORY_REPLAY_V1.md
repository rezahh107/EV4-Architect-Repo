# Architect Runtime History Replay v1

Status: active canonical runtime authority  
Owner: `rezahh107/EV4-Architect-Repo`  
Runtime interface: `ev4-architect-quality-runtime@2.0.0`

## Authority

This contract supersedes conflicting normal-run resume, state-passing, partial-rerun, terminal-assembly, and provenance clauses in older Runtime prose. It does not change the Pipeline Manifest Stage inventory, Stage order, Stage versions, Stage predicates, Stage Output contract, Stage Result Schema, Payload Schema, Build Tree semantics, or Project Gate contract.

## Persistent truth

The only persistent run input is an ordered list of accepted model-authored Stage Output artifacts. Run State, Stage Results, quality-check outcomes, Unknown ledger, Candidate lock, digests, current Stage, completion class, Payload, provenance, and handoff are Runtime-derived projections.

A caller-supplied Run State or serialized Stage Result is non-authorizing. The compatibility-shaped `evaluate_stage(...)` call reads only `run_state.evaluated_stage_outputs` as model-authored history and discards all caller-supplied derived fields.

## Canonical public operations

```python
session = resume_run(
    prior_stage_outputs,
    run_context=run_context,
    repository_root=root,
)
result = session.advance(next_stage_output)
final = session.finalize()
```

`resume_run` starts from the canonical initial state and replays one exact contiguous Manifest prefix through the existing internal evaluator and existing Stage predicates. Missing, skipped, duplicate, reordered, unknown, or mixed-run Stage Outputs fail closed.

`RuntimeSession` owns accepted Stage Output history and derived state internally. A failed advance does not mutate the last valid session projection. Successful non-terminal progression is incremental; process resume and imported history use replay.

## Terminal boundary

Before terminal Payload issuance, the complete Stage Output history is replayed from the initial state. Exactly one passing Stage Output is required for every mandatory Manifest Stage. Payload assembly consumes only the replay-derived state. Caller-supplied Stage Results, digests, locks, Unknown state, terminal completion, Payload, provenance, and handoff values are ignored or rejected.

## Partial rerun

Partial rerun truncates accepted Stage Output history immediately before the selected rerun Stage and replays the retained prefix. Unknowns, results, digests, locks, and completion state disappear or remain only because replay derives them. No manual ledger or state surgery is authoritative.

## Provenance

For `source_kind: live_conversation`, Runtime internally selects the subprocess-backed Git provider and validates repository root, repository identity, actual checked-out Head, and clean checkout. Caller provider injection is rejected with `RUNTIME_LIVE_GIT_PROVIDER_INJECTION_FORBIDDEN`.

Fixture provider injection remains available only for `fixture`, `example`, and `test_vector` contexts.

## CSS target referential integrity

`scripts/architect_css_target_validation.py` owns one shared CSS target rule. Every CSS need must reference a non-empty node ID reachable from the approved structure root. The Runtime Payload assembler and the independent Payload semantic validator both call this operation. Missing targets use `PAYLOAD_CSS_TARGET_REQUIRED`; unknown or disconnected targets use `PAYLOAD_CSS_TARGET_UNKNOWN`.

## Architecture boundary

This contract adds no second Runtime, Pipeline, Manifest, evaluator, state machine, ledger, capability system, cryptographic mechanism, or security framework. The existing evaluator core remains the only implementation of Stage evaluation.
