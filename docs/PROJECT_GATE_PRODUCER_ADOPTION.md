# Project Gate Producer Adoption — Architect

Status: `runtime_internal_export`

> Direct Project Gate export from a caller-supplied Payload file is unsupported and has been removed.

## Contract chain

```text
model-authored Architect Stage Outputs
→ official evaluator replay
→ Runtime-derived Stage Results and Run State
→ ev4-architect-stage-payload@1.0.0
→ stage-evidence-bundle.v1
→ producer-gate-export.v1
→ ce-intake
```

```yaml
architect_payload: ev4-architect-stage-payload@1.0.0
stage_bundle: stage-evidence-bundle.v1
producer_gate_export: producer-gate-export.v1
handoff_target: ce-intake
acquisition_mode: producer_emitted_gate_artifact
silent_fallback_allowed: false
```

The vendored Project Gate contracts remain pinned. Their wire format is
preserved; only the retired caller-Payload authority path is removed.

The Runtime terminal transaction owns Payload issuance, checkout provenance,
canonical hashes, validator identity, export construction, and Handoff
authorization. Stage Outputs remain model-authored evidence. Stage Results are
evaluator-derived. The Payload is Runtime-issued. The Project Gate artifact and
receipt are exporter- and validator-issued.

Synthetic execution remains non-authorizing. This repository does not claim CE
acceptance, Builder executability, Responsive completion, live Elementor
execution, release readiness, or production readiness without downstream
evidence.
