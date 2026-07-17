# Architect Project Gate Exporter — ARCH-02 Operational Contract

Status: `bounded_repair`

Prompt: `P-003-CONTINUATION`

Logical task: `ARCH-02`

This document is the repository-local ARCH-02 addendum to `docs/ARCHITECT_PROJECT_GATE_EXPORTER.md`. Where the earlier document describes post-publication checks as acceptance-invalidating, this addendum supersedes that sequence.

## Official command

Run from a clean named-branch checkout of `rezahh107/EV4-Architect-Repo`:

```bash
python scripts/export-architect-project-gate.py \
  --payload path/to/architect-stage-payload.json \
  --run-id <actual-architect-run-id> \
  --output architect-project-gate.json
```

`--overwrite` remains unsupported and fail-closed.

## Operational commit boundary

The transaction has three phases.

### 1. Pre-commit validation

Every check capable of invalidating semantic, contract, hash, repository, provenance, or ancestry acceptance completes before the canonical filename is published:

```text
strict input parsing
→ Architect Stage Payload semantic validation
→ initial repository/ref/HEAD/worktree verification
→ Stage Evidence Bundle and Producer Gate Export construction
→ contract validation
→ canonical hash self-verification
→ descriptor-bound candidate creation and write
→ candidate reread
→ candidate contract and hash validation
→ prepublication repository/ref/HEAD/worktree equality check
→ prepublication ancestry verification
→ immediate operational-commit repository/ref/HEAD/worktree equality check
→ immediate operational-commit ancestry verification
```

A failure in this phase returns a non-zero exporter failure code, reports `artifact_committed: false`, and leaves no newly created canonical operational output. An unrelated pre-existing or concurrent destination is never deleted or replaced.

### 2. Atomic operational commit

The operational commit point is the successful descriptor-derived hard-link/no-replace publication of the already validated candidate into the canonical destination name.

```text
os.link(/proc/self/fd/<owned-candidate-fd>, canonical-name, no-replace)
→ artifact_committed: true
```

Before the link succeeds, the transaction is uncommitted. After the link succeeds, the validated artifact is historically committed. The exporter never attempts pathname-based destructive rollback.

### 3. Post-commit auxiliary work

Published-descriptor observation, candidate release, directory synchronization, receipt emission, and lock/descriptor cleanup are post-commit operations. Receipt emission remains inside the cooperating exporter lock so another exporter cannot interleave with the historical acknowledgment. Their degradation is represented by stable warnings such as:

```text
ARCH_EXPORT_POST_COMMIT_OBSERVATION_WARNING:<diagnostic>
ARCH_EXPORT_RECEIPT_EMIT_FAILED:<exception>
ARCH_EXPORT_OUTPUT_DESCRIPTOR_CLOSE_FAILED:<exception>
```

A post-commit warning does not convert the committed artifact into a failed or rolled-back export. The canonical entry is retained. The result remains a historical commit receipt and does not claim that an unrelated external writer cannot later replace the pathname.

## Explicit result model

Successful and valid blocked exports expose these fields:

```yaml
result_status: SUCCESS | SUCCESS_WITH_RECEIPT_WARNING | SUCCESS_WITH_CLEANUP_WARNING | SUCCESS_WITH_WARNINGS
artifact_committed: true
receipt_emitted: true | false
cleanup_complete: true | false
handoff_allowed: true | false
output_committed: true
receipt_scope: historical_commit
current_destination_claim: false
cleanup_warnings: []
```

Presence of the filename alone is not the success contract. Operators must read the command result.

## Exit codes

| Condition | Exit code | Canonical output |
|---|---:|---|
| valid allowed export | `0` | committed |
| valid blocked export | `2` | committed, `handoff_allowed: false` |
| valid insufficient-evidence export | `2` | committed, `handoff_allowed: false` |
| pre-commit validation/publication failure | non-zero, normally `1` | no newly committed output |
| post-commit receipt or cleanup warning | same semantic exit code as the committed export | retained and historically committed |

## ARCH02-F02 identity decision

Decision: `PATH_IS_INTENTIONAL_IDENTITY_INPUT`.

The active Stage Evidence Bundle contract places source provenance inside the canonical bundle:

```text
final_stage_bundle.evidence[architect-stage-payload-canonical].source.reference
final_stage_bundle.provenance.source
```

Both fields contain `input_ref`. The active common schema defines no observation-only envelope outside the hashed Stage Evidence Bundle. Therefore the local Architect exporter preserves the current contract:

```text
payload_hash
  excludes input_ref

bundle_id
  excludes input_ref
  = repository + commit + run_id + payload_hash

bundle_hash
  includes the complete Stage Evidence Bundle
  therefore includes input_ref

export_id
  includes bundle_hash

export_hash
  includes the complete Producer Gate Export
```

Consequences:

- identical payload bytes, repository commit, run ID, and input path produce byte-stable output;
- relocating identical payload bytes changes `bundle_hash`, `export_id`, and `export_hash` intentionally;
- relocation does not change `payload_hash` or `bundle_id`;
- the pathname is provenance-bearing identity input, not non-identity display metadata.

Removing the path from the hashed bundle would require a shared common-contract decision or a new observation-only contract field. ARCH-02 does not make that cross-repository change.

## Filesystem and concurrency invariants

The repair preserves:

- atomic no-clobber publication;
- no overwrite;
- no destination deletion;
- no check-then-unlink rollback;
- no removal of a concurrent winner or replacement;
- descriptor/inode candidate ownership;
- at-most-once candidate release;
- retained fallback residue reporting;
- descriptor-bound output ancestry;
- cooperating-exporter locking through receipt emission.

`ARCH02-F06` remains a non-blocking potential local lock-namespace interference risk. No lock implementation change is made without reproduced evidence.

## Exact-head CI

Repository security governance requires a PR-context workflow to use the literal exact PR-head reference. ARCH-02 therefore uses two event-specific carriers for the same authoritative validation command surface rather than weakening that control:

- `.github/workflows/validate-architect-producer-gate-adoption.yml`
  - relevant `pull_request` events;
  - checks out `${{ github.event.pull_request.head.sha }}`;
  - asserts `git rev-parse HEAD` equals that exact PR head.
- `.github/workflows/validate-architect-producer-gate-adoption-main.yml`
  - relevant pushes to `main` and manual execution;
  - checks out `${{ github.sha }}`;
  - asserts `git rev-parse HEAD` equals the exact pushed or dispatched SHA;
  - contains no pull-request-only event dereference.

Both carriers run the same authoritative commands:

```bash
python -m py_compile scripts/export-architect-project-gate.py
python scripts/check-architect-stage-payload.py
python scripts/check-architect-producer-gate-adoption.py --format json
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_architect_producer_gate_adoption.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_architect_project_gate_exporter*.py
```

The PR carrier retains the complete pytest output as a short-lived artifact only when the exporter suite fails. This is diagnostic evidence, not a second validation authority.

## Evidence limitations

The bounded repair does not prove or implement:

- a real non-synthetic Architect Stage Payload run;
- Project Gate adoption of the repaired Architect commit;
- CE acceptance;
- Builder execution;
- browser/runtime validity;
- release or production readiness;
- Windows authoritative publication.

`real_run_evidence` remains `pending`. Final ARCH-02 closure requires validation against the exact merged `main` SHA after the repair PR is merged.
