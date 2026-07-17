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

## Validation and publication sequence

```text
strict UTF-8 JSON parsing
→ duplicate-key and non-finite-number rejection
→ active Architect JSON Schema validation
→ official Architect semantic validation
→ initial Git repository, named-ref, HEAD, and worktree verification
→ Stage Evidence Bundle construction and validation
→ Producer Gate Export construction and validation
→ canonical SHA-256 self-verification
→ exclusive non-blocking overwrite transaction lock
→ same-filesystem candidate staging, fsync, re-read, contract validation, and hash verification
→ pre-publication Git provenance equality recheck
→ atomic publication
→ post-publication identity, byte, contract, and hash verification
→ final Git provenance equality and worktree recheck
→ second final destination identity, byte, and hash verification
→ publication commit point
→ obsolete backup cleanup with operator-visible warnings
→ post-commit destination identity, byte, and hash verification before success
```

The active contracts are reused without local forks or version changes:

```text
Architect payload: ev4-architect-stage-payload@1.0.0
Stage bundle: stage-evidence-bundle.v1
Producer export: producer-gate-export.v1
Handoff target: ce-intake
Acquisition mode: producer_emitted_gate_artifact
```

## Atomic output rules

Without `--overwrite`, the staged candidate is published with an atomic hard-link/no-replace primitive. If any file, directory, or symbolic link exists at the destination at the publication boundary, publication fails with `ARCH_EXPORT_OUTPUT_EXISTS`. Destination bytes remain unchanged, temporary files are removed, and `output_written` remains false.

With explicit `--overwrite`, cooperating exporter processes are serialized by an exclusive, non-blocking output transaction lock. Each transaction records the destination identity observed before lock acquisition. A transaction that loses the lock or observes identity drift before quarantine fails closed, so two overlapping overwrite exporters cannot both report authoritative success.

An existing regular output is moved to a same-directory quarantine backup while preserving its device/inode identity. The candidate is published with the same no-replace primitive and receives its own recorded device/inode identity. Before rollback restores a backup or removes a published candidate, the exporter verifies that the current destination is absent or still matches the identity owned by that transaction.

If another process creates or replaces the destination, rollback never overwrites that concurrent artifact. The exporter fails with `ARCH_EXPORT_ROLLBACK_CONFLICT`, preserves the concurrent destination, and retains the previous output in its quarantine backup for operator recovery. The diagnostic identifies the retained backup by filename.

Symbolic-link destinations and non-regular overwrite targets are rejected. Candidate and backup artifacts use unpredictable same-directory names and are included only in the exporter's bounded clean-worktree allowance. Backup cleanup is attempted twice after the commit point. A transient cleanup failure and retry, or retained backup residue after repeated failure, is reported through `cleanup_warnings` without invalidating the already verified output.

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

The exporter verifies at initial capture, immediately before publication, and again before successful completion:

- execution inside the Git repository root;
- `origin` identifies `rezahh107/EV4-Architect-Repo`;
- HEAD is attached to the same named branch;
- HEAD remains the same full commit SHA;
- no unrelated staged, unstaged, or untracked changes exist.

The selected payload path, intended output path, staged candidate, and bounded overwrite backup may be untracked run artifacts. Any other dirty-worktree state fails closed. Absolute private checkout paths are not written into the export.

A concurrent checkout, reset, commit, branch switch, or tracked contract/schema modification prevents success. Drift before publication writes nothing. Drift after publication triggers bounded rollback and prevents the artifact from being reported as successful under stale provenance.

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
→ no successful export
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
cleanup_warnings
```

`cleanup_warnings` is an empty list when post-commit cleanup is complete. Retry or retained-quarantine diagnostics are returned explicitly when cleanup is degraded.

On failure it reports a stable diagnostic code, failed stage, concise reason, repair owner, output-written state, and `handoff_prohibited: true`.

## Evidence boundary

The automated test vectors are synthetic unit, fixture, contract, concurrency, and integration evidence only. They do not prove a real non-synthetic Architect run, current Project Gate adoption of the new source commit, CE semantic acceptance, Builder execution, browser/runtime validity, release readiness, or production readiness.

A real operator run and a fresh independent `ARCH-02` audit bound to the exact PR head remain required before stronger claims.
