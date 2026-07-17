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

The exporter never repairs or rewrites semantic content. Invalid input produces diagnostics only and no authoritative export receipt.

## Official command

Run from a clean `rezahh107/EV4-Architect-Repo` checkout on a named branch:

```bash
python scripts/export-architect-project-gate.py \
  --payload path/to/architect-stage-payload.json \
  --run-id <actual-architect-run-id> \
  --output architect-project-gate.json
```

`--run-id` is explicit because two independent Architect executions must not receive the same execution, bundle, or export identity merely because their semantic payload content is equal.

The operator does not provide repository identity, branch/ref, commit SHA, schema identities, handoff target, validation status, payload hash, bundle hash, or export hash. These are derived or verified by the exporter.

## Overwrite policy

`--overwrite` is intentionally fail-closed and returns:

```text
ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED
```

The exporter does not move an existing destination into quarantine and does not restore a backup over a destination. Python and the supported platform APIs do not provide a portable operation that atomically combines a device/inode ownership predicate with a destructive path replacement. An advisory lock cannot close that gap against editors, operators, or unrelated local processes.

To replace an existing artifact, the operator must first move or archive it outside the exporter transaction, inspect the retained artifact, and then run the exporter without `--overwrite`. The exporter itself never treats that manual action as validation evidence.

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
→ shared exclusive output lock for every exporter mode
→ same-filesystem candidate staging and fsync
→ staged candidate re-read, contract validation, and hash verification
→ pre-publication Git provenance equality recheck
→ atomic hard-link/no-replace publication
→ open and retain a descriptor for the published inode
→ exact identity and byte verification through the retained descriptor
→ post-publication contract and hash verification
→ final Git provenance equality and worktree recheck
→ second exact identity, byte, contract, and hash verification
→ publication commit point
→ historical receipt serialization and flush while the exporter lock is held
→ descriptor close and lock release
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

All supported exporter operations targeting the same absolute output path use the same exclusive transaction lock. This serializes overwrite and no-overwrite exporter processes with each other. The lock is not presented as protection against arbitrary non-cooperating writers.

Without `--overwrite`, the staged candidate is published with an atomic hard-link/no-replace primitive. If any file appears at the destination before the publication primitive completes, publication fails with `ARCH_EXPORT_OUTPUT_EXISTS`; that destination remains unchanged.

After publication, the exporter retains an open descriptor for the published inode and verifies:

- descriptor device/inode identity;
- current destination device/inode identity;
- exact canonical bytes including the final newline;
- strict JSON parsing;
- active contract validity;
- payload, bundle, and export hashes.

If identity or byte drift occurs, the exporter fails closed. Rollback is namespace-nondestructive: it does not unlink, move, replace, or restore the destination. A post-publication artifact may remain for operator inspection, but it is not reported as an authoritative current-path output.

Symbolic-link destinations and non-regular existing destinations are rejected. Candidate files use unpredictable same-directory names and are included only in the exporter's bounded clean-worktree allowance.

## Receipt semantics

A success result is explicitly a historical commit receipt, not a continuing assertion about the current destination path:

```yaml
receipt_scope: historical_commit
current_destination_claim: false
output_committed: true
output_written: false
```

`output_committed: true` means the transaction published and fully verified the artifact at its commit boundary.

`output_written` means the destination is still owned by the live transaction. Because the returned library result is observed after the transaction boundary ends, successful returned results use `output_written: false`.

The CLI serializes and flushes the historical receipt while the exporter lock is still held. The lock is released only after receipt serialization. The receipt still does not claim that arbitrary external writers cannot change the destination later.

The result and failure reports distinguish:

```text
output_written
output_committed
destination_present
concurrent_destination_preserved
backup_retained
backup_path
receipt_scope
current_destination_claim
cleanup_warnings
```

No backup is created by the fail-closed overwrite design, so `backup_retained` is false and `backup_path` is null. A concurrent replacement detected after no-clobber publication remains at the original destination path and is reported through `concurrent_destination_preserved`.

## Cleanup behavior

Rollback and close may remove only the transaction's private staged candidate and close transaction-owned descriptors and locks. They never conditionally remove or replace the destination.

Cleanup degradation is operator-visible through `cleanup_warnings`. A warning discovered only while releasing the lock is returned by the library API and emitted by the CLI as a `post_release_cleanup` receipt update on standard error.

The prior backup retry and retained-backup cleanup paths no longer exist because the exporter never creates a rollback backup. Tests assert that overwrite rejection occurs before backup creation or backup cleanup.

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

The exporter verifies at initial capture, immediately before publication, and again before the commit receipt:

- execution inside the Git repository root;
- `origin` identifies `rezahh107/EV4-Architect-Repo`;
- HEAD is attached to the same named branch;
- HEAD remains the same full commit SHA;
- no unrelated staged, unstaged, or untracked changes exist.

The selected payload path, intended output path, and staged candidate may be untracked run artifacts. Any other dirty-worktree state fails closed. Absolute private checkout paths are not written into the export.

Drift before publication writes nothing. Drift after publication prevents a success receipt and leaves the destination namespace untouched by rollback.

## Platform support

### POSIX

The implementation uses `fcntl.flock` for the shared exporter lock and `os.link` for atomic no-clobber publication. Linux GitHub Actions provide the current executed platform evidence. `--overwrite` remains unsupported and fail-closed.

### Windows

The implementation uses `msvcrt.locking` for the shared exporter lock and Python's `os.link` no-clobber primitive. The Windows branch is implemented but is not independently executed by the current Linux-only workflow. `--overwrite` remains unsupported and fail-closed.

### Other or unsupported platforms

If neither supported locking API is present, the exporter fails with:

```text
ARCH_EXPORT_OUTPUT_LOCK_UNAVAILABLE
```

If atomic hard-link/no-clobber publication is unavailable, it fails with:

```text
ARCH_EXPORT_ATOMIC_NO_CLOBBER_UNSUPPORTED
```

No fallback weakens the invariant.

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
→ no successful receipt
→ handoff prohibited
```

Unresolved items that belong only to later Builder, Responsive, or production boundaries remain visible and may produce `successful_with_flags`; they are not silently removed. Any unresolved item that blocks Architect payload acceptance or the CE transition prohibits handoff.

## Evidence boundary

The automated test vectors are synthetic unit, fixture, contract, concurrency, and integration evidence only. They do not prove a real non-synthetic Architect run, current Project Gate adoption of the new source commit, CE semantic acceptance, Builder execution, browser/runtime validity, release readiness, or production readiness.

A real operator run and a fresh independent `ARCH-02` audit bound to the exact PR head remain required before stronger claims.
