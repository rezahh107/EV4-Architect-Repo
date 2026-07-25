# Project Gate Producer Adoption — Architect

Status: `runtime_finalization_api_pending_cross_repository_review`

> Direct Project Gate export from a caller-supplied Payload file is unsupported and has been removed.

## Contract chain

```text
complete ordered model-authored Architect Stage Outputs
→ official evaluator replay
→ Runtime-derived Stage Results and Run State
→ Runtime-issued ev4-architect-stage-payload@1.0.0
→ one-shot capability consumption
→ stage-evidence-bundle.v1
→ producer-gate-export.v1
→ Contract and hash validation
→ Architect-owned artifact and receipt publication
→ ce-intake
```

```yaml
architect_payload: ev4-architect-stage-payload@1.0.0
stage_bundle: stage-evidence-bundle.v1
producer_gate_export: producer-gate-export.v1
finalization_receipt: ev4-architect-project-gate-finalization-receipt@1.0.0
handoff_target: ce-intake
acquisition_mode: runtime_finalization_api
silent_fallback_allowed: false
```

## Consumer entrypoint

Stage-QC and other authorized consumers invoke only:

```python
scripts/architect_quality_runtime.py#finalize_project_gate(
    stage_outputs,
    *,
    run_context,
    repository_root,
    output_directory,
    git_provider=None,
)
```

The semantic input is the complete ordered twelve-Stage Output history. Payloads,
Payload paths, caller Stage Results, caller Run State, caller provenance, digests,
eligibility, validator output, or Handoff booleans are not accepted.

The Runtime performs one replay and one Payload assembly. The terminal evaluator
returns one explicit internal execution object carrying the complete artifact;
the normal public Stage Result contains only its existing summary. Architect then
publishes `architect-project-gate.json` and
`architect-project-gate-receipt.json` outside the repository.

The vendored Project Gate contracts remain pinned and their wire format is
preserved. The Runtime terminal transaction owns Payload issuance, checkout
provenance, canonical hashes, validator identity, export construction,
publication, receipt creation, and Handoff authorization.

Synthetic execution remains non-authorizing. A valid synthetic or otherwise
blocked transaction may finalize and publish official blocked outputs, while
`handoff.allowed` remains false. This repository does not claim CE acceptance,
Builder executability, Responsive completion, live Elementor execution, release
readiness, or production readiness without downstream evidence.
