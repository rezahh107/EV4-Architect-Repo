# Architect Project Gate Exporter — ARCH-02 Operational Contract

Status: `bounded_repair_pending_fresh_pr_inspector_rereview`

Prompt: `P-003-CONTINUATION`

Logical task: `ARCH-02`

This repository-local addendum supersedes earlier ARCH-02 wording where any
post-publication degradation was treated as ordinary warning-bearing success.
Historical artifact commitment, canonical repository destination proof, and
current Git-revision acceptance are separate states.

## Official command

```bash
python scripts/export-architect-project-gate.py \
  --payload path/to/architect-stage-payload.json \
  --run-id <actual-architect-run-id> \
  --output architect-project-gate.json
```

`--overwrite` remains unsupported and fail-closed.

## Transaction phases

### 1. Pre-commit validation

Every check available before publication completes before the canonical name is
created:

```text
strict input parsing
→ Architect Stage Payload semantic validation
→ initial repository/ref/HEAD/worktree verification
→ Stage Evidence Bundle and Producer Gate Export construction
→ contract validation
→ canonical hash self-verification
→ descriptor-bound candidate creation and write
→ retained-candidate reread
→ candidate contract and hash validation
→ prepublication repository/ref/HEAD/worktree equality check
→ prepublication ancestry verification
→ operational-commit repository/ref/HEAD/worktree equality check
→ operational-commit ancestry verification
```

A failure in this phase returns a non-zero exporter failure, reports no
historical commit, and leaves no newly created canonical operational output.
Existing and concurrent destinations are never removed or replaced.

### 2. Historical atomic commit

The successful descriptor-derived hard-link/no-replace operation remains the
historical commit point:

```text
os.link(/proc/self/fd/<owned-candidate-fd>, canonical-name, no-replace)
→ artifact_committed: true
```

The exporter never attempts pathname-based destructive rollback after this
point.

### 3. Post-link acceptance gate

Immediately after the link, the exporter separately proves:

1. the active repository, named ref, HEAD and tracked worktree still match the
   provenance embedded in the artifact;
2. the transaction-owned destination descriptor still identifies the staged
   candidate bytes;
3. the bound output parent still belongs to the canonical repository ancestry;
4. the claimed repository-relative destination still contains the committed
   artifact.

Failure of this gate does not erase the historical commit. It forces:

```yaml
artifact_committed: true
handoff_allowed: false
current_revision_accepted: false
result_status: COMMITTED_HANDOFF_BLOCKED | COMMITTED_HANDOFF_BLOCKED_WITH_WARNINGS
```

If canonical destination proof fails, the result also reports:

```yaml
canonical_destination_present: false
output_path: ""
committed_output_location: bound_parent_outside_canonical_ancestry | canonical_destination_unverified
```

The empty `output_path` intentionally prevents a false claim that the
repository-relative canonical path contains the artifact.

## Result fields

```yaml
result_status: string
artifact_committed: true | false
receipt_emitted: true | false
cleanup_complete: true | false
current_revision_accepted: true | false
canonical_destination_present: true | false
committed_output_location: string
handoff_allowed: true | false
output_committed: true | false
output_path: string
acceptance_blockers: []
cleanup_warnings: []
receipt_scope: historical_commit
current_destination_claim: false
```

`acceptance_blockers` are not cleanup warnings. They prevent an allowed handoff
when exact revision or canonical location cannot be proven.

## Exit codes

| Condition | Exit code | Artifact state |
|---|---:|---|
| valid allowed export | `0` | committed and accepted |
| valid blocked export | `2` | committed, handoff prohibited |
| valid insufficient-evidence export | `2` | committed, handoff prohibited |
| committed but post-link acceptance blocked | `2` | committed, handoff prohibited |
| pre-commit failure | non-zero, normally `1` | no newly committed output |
| receipt or cleanup warning without acceptance blocker | semantic exit code of the artifact | committed |

## PRF-001 — canonical ancestry at publication

A parent rename after the final pre-link ancestry check can cause the hard link
to be created through the retained descriptor in a directory no longer located
under the canonical repository path.

The repair preserves the link as historical evidence but blocks handoff unless
post-link descriptor ownership and canonical ancestry are both re-proven. It
never deletes the detached artifact or any recreated canonical path.

Mutation coverage performs this sequence:

1. bind the output parent;
2. complete the final ancestry check;
3. rename the bound parent outside the repository;
4. recreate the original parent pathname;
5. permit descriptor-relative publication;
6. verify `handoff_allowed: false`;
7. verify no root-relative canonical destination claim is emitted.

## PRF-002 — Git provenance at publication

The final pre-link Git observation alone cannot prove that repository state did
not change before `os.link`.

After the historical link, the exporter repeats repository/ref/HEAD/worktree
observation and compares it with the artifact provenance. Any mismatch records:

```text
ARCH_EXPORT_POST_COMMIT_PROVENANCE_BLOCKED:<diagnostic>
```

The artifact remains historically committed, but `current_revision_accepted`
and `handoff_allowed` are false.

## PRF-003 — output-lock cleanup taxonomy

The lock release implementation emits:

```text
ARCH_EXPORT_OUTPUT_LOCK_RELEASE_FAILED:<exception>
```

The cleanup classifier recognizes that exact prefix. A release failure therefore
produces:

```yaml
artifact_committed: true
cleanup_complete: false
result_status: SUCCESS_WITH_CLEANUP_WARNING
```

No output rollback or destination deletion occurs.

## PATH_IS_INTENTIONAL_IDENTITY_INPUT

The ARCH02-F02 decision remains unchanged. `input_ref` is part of canonical
Stage Evidence Bundle provenance.

```text
payload_hash: excludes input_ref
bundle_id: excludes input_ref
bundle_hash: includes input_ref
export_id: includes bundle_hash
export_hash: includes complete Producer Gate Export
```

Relocating identical payload bytes therefore intentionally changes
`bundle_hash`, `export_id`, and `export_hash`, while preserving `payload_hash`
and `bundle_id`.

## Preserved filesystem and concurrency invariants

- atomic no-clobber publication;
- no overwrite;
- no destination deletion;
- no check-then-unlink rollback;
- concurrent winner and replacement preservation;
- descriptor/inode candidate ownership;
- at-most-once candidate release;
- retained fallback residue reporting;
- descriptor-bound output ancestry;
- cooperating-exporter locking through receipt emission;
- valid blocked and insufficient-evidence exit code `2`.

## Exact-head CI

The pull-request workflow checks out and asserts the literal PR head. The
pushed-main workflow uses `github.sha` and contains no PR-only dereference.
Both run:

```bash
python -m py_compile scripts/export-architect-project-gate.py
python scripts/check-architect-stage-payload.py
python scripts/check-architect-producer-gate-adoption.py --format json
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_architect_producer_gate_adoption.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_architect_project_gate_exporter*.py
```

## Remaining evidence limitations

This repair does not establish:

- final independent PR Inspector acceptance;
- merge authorization or repository-hosted merge enforcement;
- exact merged-main closure;
- a real non-synthetic Architect Stage Payload run;
- Project Gate adoption;
- CE acceptance;
- Builder or Golden Path execution;
- Windows authoritative publication;
- release or production readiness.

All three findings remain `implemented_pending_rereview` until a fresh PR
Inspector review is bound to the final PR head.
