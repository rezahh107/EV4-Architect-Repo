# Architect Project Gate Exporter — ARCH-02 Historical Note

Status: `historical_non_executable`

> Direct Project Gate export from a caller-supplied Payload file is unsupported and has been removed.

ARCH-02 previously documented an operator-facing Payload-file publication
transaction. That command, its `--payload` argument, compatibility entrypoint,
filesystem transaction implementation, and Windows/WSL wrappers are retired.
This file remains only to preserve the historical meaning of ARCH-02 findings.

The active authority chain is:

```text
Stage Outputs
→ Stage-QC evaluator replay
→ Runtime-derived Stage Results and state
→ Runtime-issued Payload
→ Runtime-internal Project Gate exporter and validator
```

No instruction in this historical note is executable or supported. Current
behavior is documented in `docs/ARCHITECT_PROJECT_GATE_EXPORTER.md`.
