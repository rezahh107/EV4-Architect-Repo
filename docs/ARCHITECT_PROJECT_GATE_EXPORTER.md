# Architect Project Gate Exporter

Status: `implemented_pending_independent_review`

Command classification: `PROPOSED_NEW_IMPLEMENTED`

## Purpose

This repository-owned command converts the active machine-readable Architect Stage Payload into one Project Gate-ready JSON artifact:

```text
Architect Stage Payload
→ Stage Evidence Bundle
→ Producer Gate Export
→ architect-project-gate.json
```

It accepts only `ev4-architect-stage-payload@1.0.0`. It does not infer architecture facts from Markdown, `FINAL BUILDER HANDOFF`, or other prose.

## Official command

Run from a clean named-branch checkout of `rezahh107/EV4-Architect-Repo`:

```bash
python scripts/export-architect-project-gate.py \
  --payload path/to/architect-stage-payload.json \
  --run-id <actual-architect-run-id> \
  --output architect-project-gate.json
```

Repository identity, named ref, full commit SHA, active schema identities, handoff target and canonical hashes are derived or verified by the exporter.

## Overwrite policy

`--overwrite` is intentionally fail-closed:

```text
ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED
```

The exporter never quarantines, removes, restores or destructively replaces an existing destination. A prior artifact must be archived by the operator before a new no-clobber export is attempted. That manual archive is not treated as validation evidence.

## Ancestry-bound POSIX publication

The final file inode alone is not sufficient evidence that the artifact remains in the repository. On supported POSIX systems, the transaction binds the complete repository-root-to-output-parent namespace chain.

The exporter:

1. resolves and opens the repository root once with `O_DIRECTORY | O_NOFOLLOW`;
2. traverses each output-parent component relative to the retained preceding directory descriptor;
3. rejects symbolic links and non-directory components;
4. retains descriptors and device/inode identities for the root and every traversed directory;
5. creates the staged candidate relative to the retained output-parent descriptor;
6. publishes with descriptor-relative `os.link(..., src_dir_fd=..., dst_dir_fd=..., follow_symlinks=False)`;
7. opens and retains the published file descriptor relative to that same parent descriptor;
8. verifies exact bytes, file identity, component identities and parent relationships before commit and receipt emission;
9. independently walks `..` from the retained output parent to prove that the retained repository root remains an ancestor.

A parent rename, exchange, removal, intermediate symlink replacement, repository-root identity change, or move outside the repository fails with a stable ancestry diagnostic. A rename outside the repository followed by a symlink at the original parent path cannot produce a success receipt, even when the output file inode itself is unchanged.

Relevant diagnostics include:

```text
ARCH_EXPORT_ANCESTRY_BINDING_UNSUPPORTED
ARCH_EXPORT_OUTPUT_ANCESTRY_UNSAFE
ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED
ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT
ARCH_EXPORT_OUTPUT_ANCESTRY_CREATE_FAILED
```

## Platform support

### POSIX/Linux

POSIX ancestry binding is implemented with descriptor-relative filesystem operations, `fcntl.flock`, `O_DIRECTORY`, `O_NOFOLLOW`, `dir_fd`, and hard-link/no-replace publication. Exact-head Linux GitHub Actions are the executed platform evidence.

### Windows

Windows is intentionally unsupported for authoritative publication because the current implementation cannot establish the same complete descriptor-bound ancestry invariant with the available Python interfaces. It fails closed with:

```text
ARCH_EXPORT_ANCESTRY_BINDING_UNSUPPORTED
```

The prior Windows lock branch remains non-authoritative and does not weaken the ancestry requirement.

### Other platforms

Any platform lacking the required directory-descriptor, no-follow, descriptor-relative stat/link/unlink/mkdir, or locking behavior fails closed. There is no pathname-based fallback.

## Destination preflight

Destination inspection uses one guarded descriptor-relative `stat(..., follow_symlinks=False)` operation.

- `FileNotFoundError` means the destination is absent.
- a symbolic link is rejected with `ARCH_EXPORT_UNSAFE_OUTPUT_PATH`;
- a non-regular destination is rejected with `ARCH_EXPORT_OUTPUT_PATH_TYPE_INVALID`;
- other inspection failures are converted to `ARCH_EXPORT_OUTPUT_INSPECTION_FAILED`.

Filesystem races do not escape as raw `OSError` or traceback from the CLI.

## Validation and publication sequence

```text
strict UTF-8 JSON parsing
→ duplicate-key and non-finite-number rejection
→ official Architect semantic validation
→ initial Git repository/ref/HEAD/worktree verification
→ Stage Evidence Bundle and Producer Gate Export construction
→ active contract validation
→ canonical SHA-256 self-verification
→ lexical output containment check
→ descriptor-bound repository/output-parent ancestry capture
→ shared exclusive exporter lock
→ single guarded destination stat
→ descriptor-relative staged candidate creation, write and fsync
→ descriptor-relative candidate reread and validation
→ pre-publication Git provenance equality check
→ pre-publication ancestry verification
→ descriptor-relative hard-link/no-replace publication
→ retained published-file descriptor
→ post-publication ancestry, identity and exact-byte verification
→ post-publication contract and hash verification
→ final Git provenance equality check
→ final ancestry, identity, byte, contract and hash verification
→ publication commit boundary
→ success-boundary ancestry, identity and byte verification
→ historical receipt serialization and flush while the lock is held
→ descriptor and lock release
```

## Atomic no-clobber behavior

All cooperating exporters targeting the same absolute output path use the same exclusive lock. Publication uses a hard-link/no-replace primitive relative to the retained output-parent descriptor.

If a destination appears at the publication boundary, the exporter returns:

```text
ARCH_EXPORT_OUTPUT_EXISTS
```

It never deletes the concurrent destination. Rollback remains namespace-nondestructive: it may remove only the transaction-private staged candidate and close transaction-owned descriptors.

Non-cooperating writers are not trusted. File identity drift, byte drift and ancestry drift prohibit a success receipt.

## Receipt semantics

A successful result is a historical commit receipt:

```yaml
receipt_scope: historical_commit
current_destination_claim: false
output_committed: true
output_written: false
```

`output_committed: true` means that the artifact passed the complete file, ancestry, contract, hash and provenance checks at the commit boundary.

The receipt is serialized and flushed while the cooperating output lock and ancestry descriptors remain held. It is not a continuing assertion that arbitrary external writers cannot change the namespace after the historical boundary.

Reports distinguish:

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

No backup is created because overwrite is unsupported.

## Canonical identity and hashes

Canonical content uses UTF-8 JSON, sorted string keys, no insignificant whitespace, preserved Unicode, rejection of non-finite numbers, and one final newline in the published file.

```text
payload_hash = SHA-256(canonical Architect payload)
bundle_id = deterministic identity(repository + commit + run_id + payload_hash)
bundle_hash = SHA-256(canonical Stage Evidence Bundle)
export_id = deterministic identity(repository + commit + run_id + bundle_hash)
export_hash = SHA-256(canonical Producer Gate Export)
```

Repeated export of the same source commit, run ID and payload is byte-stable. A different `run_id` changes bundle/export identities.

## Git provenance

The exporter verifies:

- execution from the repository root;
- `origin` identity;
- attached named ref;
- unchanged full HEAD SHA;
- absence of unrelated staged, unstaged or untracked changes.

The selected payload, intended output and transaction-private candidate are the only bounded untracked allowances. HEAD, ref, tracked-worktree or active-contract drift prevents a success receipt.

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

invalid payload, unreliable Git provenance, filesystem race or ancestry drift
→ no successful receipt
→ handoff prohibited
```

## Evidence boundary

The automated cases are synthetic unit, contract, concurrency, ancestry and integration evidence only. They do not prove:

- a real non-synthetic Architect run;
- current Project Gate adoption of the resulting commit;
- CE semantic acceptance;
- Builder execution;
- browser/runtime validity;
- release or production readiness.

A fresh independent PR Inspector review bound to the exact resulting PR head remains required.
