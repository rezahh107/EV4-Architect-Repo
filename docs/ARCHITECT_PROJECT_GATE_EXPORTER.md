# Architect Project Gate Exporter

Status: `implemented_pending_independent_review`

Command classification: `PROPOSED_NEW_IMPLEMENTED`

## Purpose

This repository-owned command converts the active machine-readable Architect Stage Payload into one complete Project Gate-ready JSON artifact:

```text
Architect Stage Payload
→ Stage Evidence Bundle
→ Producer Gate Export
→ architect-project-gate.json
```

The command does not parse `FINAL BUILDER HANDOFF`, Markdown reports, or other prose to infer architecture facts. It accepts only the active Architect machine payload:

```text
ev4-architect-stage-payload@1.0.0
```

## Source payload

The source artifact is a persisted JSON instance of `ev4-architect-stage-payload@1.0.0`, validated by:

```text
schemas/ev4-architect-stage-payload.v1.schema.json
scripts/check-architect-stage-payload.py
```

Architect truth is carried by the payload's architecture identity, approved structure, intent maps, evidence register, unresolved evidence, forbidden work, boundary assertions, and Kernel decision records. `payload_status` controls whether the payload is complete or `insufficient_evidence`.

The exporter never repairs or rewrites semantic content. Invalid input produces diagnostics only and no export.

## Official command

Run from a clean `rezahh107/EV4-Architect-Repo` checkout on a named branch:

```bash
python scripts/export-architect-project-gate.py \
  --payload path/to/architect-stage-payload.json \
  --run-id <actual-architect-run-id> \
  --output architect-project-gate.json
```

`--run-id` is an explicit run input because two independent Architect executions must not receive the same execution, bundle, or export identity merely because their semantic payload content is equal.

The operator does not provide repository identity, branch/ref, commit SHA, schema identities, handoff target, validation status, payload hash, bundle hash, or export hash. These are derived or verified by the exporter.

Use `--overwrite` only when intentionally replacing an existing output after all validation succeeds.

## Validation sequence

```text
strict UTF-8 JSON parsing
→ duplicate-key and non-finite-number rejection
→ active Architect JSON Schema validation
→ official Architect semantic validation
→ Git repository, branch, commit, and worktree verification
→ Stage Evidence Bundle construction and validation
→ Producer Gate Export construction and validation
→ canonical SHA-256 self-verification
→ atomic write
→ post-write re-read, contract validation, and hash verification
```

The active contracts are reused without local forks or version changes:

```text
Architect payload: ev4-architect-stage-payload@1.0.0
Stage bundle: stage-evidence-bundle.v1
Producer export: producer-gate-export.v1
Handoff target: ce-intake
Acquisition mode: producer_emitted_gate_artifact
```

## Identity and hash rules

Canonical content hashing uses UTF-8 JSON with sorted object keys, no insignificant whitespace, preserved Unicode, and rejection of `NaN`/`Infinity`.

```text
payload_hash = SHA-256(canonical Architect payload)
bundle_id = deterministic identity over repository + commit + run_id + payload_hash
bundle_hash = SHA-256(canonical Stage Evidence Bundle)
export_id = deterministic identity over repository + commit + run_id + bundle_hash
export_hash = SHA-256(canonical Producer Gate Export)
```

Repeated export of the same unchanged run, payload, and source commit is byte-stable. A different `run_id` changes run, bundle, and export identities while preserving the semantic payload hash when the payload is unchanged.

## Git and provenance rules

Before emission, the exporter verifies:

- execution inside the Git repository root;
- `origin` identifies `rezahh107/EV4-Architect-Repo`;
- HEAD is attached to a named branch;
- HEAD is a full commit SHA;
- no unrelated staged, unstaged, or untracked changes exist.

The selected payload path and intended output path may be untracked run artifacts. Any other dirty-worktree state fails closed. Absolute private checkout paths are not written into the export.

## Handoff behavior

```text
valid + complete + non-synthetic + no Architect/CE transition blocker
→ successful or successful_with_flags
→ handoff.allowed: true

synthetic payload
→ valid blocked export
→ handoff.allowed: false

payload_status: insufficient_evidence
→ valid insufficient-evidence export
→ handoff.allowed: false

invalid payload or unreliable Git provenance
→ no export
→ handoff prohibited
```

Unresolved items that belong only to later Builder, Responsive, or production boundaries remain visible and may produce `successful_with_flags`; they are not silently removed. Any unresolved item that blocks Architect payload acceptance or the CE transition prohibits handoff.

## Output

The output is one canonical JSON file:

```text
architect-project-gate.json
```

On success or valid blocked emission, the command reports:

```text
status
output_path
export_id
payload_hash
bundle_hash
export_hash
producer_commit
handoff_target
handoff_allowed
output_written
```

On failure it reports a stable diagnostic code, failed stage, concise reason, repair owner, output-written state, and `handoff_prohibited: true`.

## Evidence boundary

The automated test vectors are synthetic unit, fixture, contract, and integration evidence only. They do not prove a real non-synthetic Architect run, current Project Gate adoption of the new source commit, CE semantic acceptance, Builder execution, browser/runtime validity, release readiness, or production readiness.

A real operator run and a fresh independent `ARCH-02` audit bound to the exact PR head remain required before stronger claims.
