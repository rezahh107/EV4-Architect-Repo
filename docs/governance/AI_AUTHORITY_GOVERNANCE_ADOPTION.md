# AI Authority Governance Adoption

Document status: normative when present on the default branch

Adoption layer: core repository policy

Machine enforcement status: not implemented by this document

Target standard: `AI Authority Deterministic Governance — Source of Truth v1.0.2`

## Purpose

This file maps the target governance standard into the existing authority structure of `rezahh107/EV4-Architect-Repo` without copying the standard, duplicating repository authorities, or claiming enforcement that does not exist.

The target standard defines the governance requirements. This repository proves implementation only through its own current files, schemas, validators, fixtures, workflows, exact-revision evidence, and independent review records.

## Authority Map

Use the following repository authorities for their bounded purposes:

1. The exact live default-branch revision and verified repository evidence are factual authority for what exists.
2. `STATUS.md` is the sole mutable authority for current project, stage, validation-track, and next-step status.
3. `02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md` owns active cross-cutting pipeline overrides.
4. Owning contracts, schemas, validators, fixtures, and diagnostics define artifact semantics and executable checks.
5. `manifests/architect-pipeline-manifest.v1.json` owns canonical pipeline stage identifiers, order, and validation-track classification. Its `stage_id` values are not governance capability identifiers.
6. `planning/DECISION_ESCAPE_ROUTES.yml` records bounded decision-escape-route evidence and enforcement state; it is not a general governance status registry.
7. This file owns the repository-specific interpretation of AI technical authority, evidence authority, Scope Gate and Progress Gate separation, independent review, and the minimum security profile.

When authorities conflict, stop and report the conflict. Do not silently combine incompatible claims. Unknown or missing evidence remains `insufficient_evidence`.

## Technical Decision and Evidence Authority

- AI is the technical decision authority for repository implementation, repair, validation interpretation, and merge recommendation.
- Repository evidence is the authority for factual claims about files, revisions, tests, CI, review identity, and implementation state.
- AI critique, confidence, or reviewer language is not factual evidence by itself.
- Human technical approval and owner acknowledgement must not be treated, accepted, or used as substitutes for repository evidence.
- The user may perform the administrative Merge action after a valid technical recommendation; that action is not technical approval and does not prove correctness.
- Missing evidence must not be normalized into success, completion, readiness, or enforcement.

## Scope Gate

The Scope Gate answers only whether a proposed change is authorized now.

Inputs include the exact default-branch revision, `STATUS.md`, active overrides, the pipeline manifest, owning contracts, dependencies, current PR state, and any approved frozen plan or increment.

Allowed Scope Gate results are:

```text
authorized
unauthorized
insufficient_evidence
```

Implementation must not start when the result is `unauthorized` or `insufficient_evidence`.

The Scope Gate does not prove that authorized work was completed correctly. A future enforcement increment may add a machine-readable carrier and validator; this policy document alone is `prose_only`.

## Progress Gate

The Progress Gate answers only whether authorized work is complete and eligible for an independent merge recommendation.

Completion requires, where applicable:

- the implementation matches the authorized scope;
- the exact current PR head is identified;
- required validation executed successfully on that exact head;
- evidence and status claims match the observed revision;
- no unresolved blocker or security finding remains;
- an independent AI review is bound to the exact current head;
- any head change invalidates the earlier review and requires fresh review.

The Progress Gate must remain separate from the Scope Gate. Authorization to work is not evidence of completion. This policy document does not by itself implement the Progress Gate.

## Independent Review and Merge Boundary

- The implementation model must not serve as the independent inspector of its own final revision.
- Review identity must bind to repository, base SHA, reviewed head SHA, protocol version, inspector identity, and relevant validation evidence.
- A review for an older head is stale immediately after any head change.
- `GREEN_MERGE_RECOMMENDED` may be issued only by a genuinely separate review context with matching exact-head evidence.
- The implementation model must not claim approval, final acceptance, Merge, deployment, or release without corresponding evidence.

## Capability and Stage Identity Boundary

- Existing `stage_id` values remain owned by `manifests/architect-pipeline-manifest.v1.json`.
- Governance adoption increment IDs such as `ARCH-GOV-CORE-001` are implementation units, not product capabilities.
- Do not invent a second stage registry or silently reinterpret stage IDs as governance capability IDs.
- A canonical capability lifecycle registry must be introduced only if a later enforcement increment demonstrates that it is required. Until then, capability completion claims remain bounded to existing repository authorities and exact evidence.

## Minimum Security Profile

```yaml
profile_id: personal_public_repository_minimum
repository_visibility_trigger: public
pull_request_workflow_trigger: active
```

Required controls for applicable GitHub Actions workflows:

- pin third-party actions to immutable commit SHAs;
- declare minimum explicit permissions, normally `contents: read` for validation-only workflows;
- checkout `${{ github.event.pull_request.head.sha }}` when exact-head PR validation is claimed;
- set `persist-credentials: false` unless a documented write requirement exists;
- fail closed when `git rev-parse HEAD` differs from the expected PR head;
- do not expose repository secrets to untrusted pull-request code;
- do not classify synthetic pull-request merge execution as exact-head execution;
- reevaluate this profile whenever repository visibility, workflow triggers, permissions, secret access, or external action usage changes.

This personal public-repository profile does not require enterprise controls such as merge queues, mandatory CODEOWNERS, broad SAST/DAST, SBOM attestations, or organization-wide policy infrastructure unless a later risk assessment authorizes them.

## Evidence States

Use explicit evidence states and do not conflate them:

```text
observed
validated
resolved
derived
proposed
unverified
insufficient_evidence
```

`prose_only` is not equivalent to schema-backed, fixture-tested, CI-enforced, sequence-enforced, runtime-enforced, independently reviewed, or production-ready.

## Current Adoption Boundary

This core policy establishes repository-specific governance semantics and the minimum security posture only.

It does not claim:

- machine-enforced startup governance;
- a machine-readable Scope Gate;
- a machine-readable Progress Gate;
- repository-wide governance coverage validation;
- exact-head independent review automation;
- merge recommendation automation;
- runtime or downstream governance enforcement;
- Project Gate runtime integration;
- production readiness.

Those enforcement carriers belong to later authorized increments and must be reported according to their actual evidence state.

## Architect Stage Boundary Validation Transaction

Stages `/decompose` through `/score-audit` use one additive deterministic transaction without replacing `ev4-architect-stage-payload@1.0.0`:

```yaml
artifact_schema: ev4-architect-pipeline-stage-artifact@1.1.0
receipt_schema: ev4-architect-stage-validation-receipt@1.1.0
failure_event_schema: ev4-architect-validation-failure-event@1.0.0
boundary_schema: ev4-stage-boundary-record@1.1.0
anchor_schema: ev4-stage-anchor@1.3.0
bundle_schema: ev4-architect-validation-bundle@1.1.0
```

The earliest owning producer boundary must fail when a required canonical Artifact is missing or semantically invalid. `failed_stage` records where validation detected failure; `repair_target_stage` records the earliest owning Stage that must change. They are not assumed equal.

Production authority is limited to:

```bash
python scripts/check-architect-pipeline-stage-boundary.py validate-run \
  --sequence <artifact-directory> \
  --output <validation-bundle> \
  --format json

python scripts/check-architect-pipeline-stage-boundary.py validate-bundle \
  --bundle <validation-bundle> \
  --format json
```

A Bundle authorizes continuation only when it independently regenerates from exact contained Artifact bytes with `bundle_integrity_status: valid`, `run_validation_status: valid`, and `authorization_valid: true`. A truthfully represented failed Run has valid Bundle integrity but no authorization. A malformed, forged, incomplete, or non-reproducible Bundle has invalid integrity.

Caller-supplied Receipts, Failure Events, Boundaries, Anchors, and Manifests are untrusted assertions. A user-facing Anchor never independently authorizes work. Historical Anchor and Bundle identities remain historical evidence only.

The legacy file-producing flags `--write-receipt`, `--write-receipts`, and `--write-anchors` are removed. Standalone Artifact diagnostics use `diagnose-artifact`, generate no authority files, and report `authorization_valid: false`.

Schema, Validator, fixture, mutation-test, and exact-Head Workflow evidence may establish repository CI enforcement for the exact tested Head. Runtime-tool enforcement and downstream enforcement remain `insufficient_evidence` until separately proven. Fresh independent PR Inspector review remains mandatory after every Head change.
