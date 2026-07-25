# EV4 Architect Repo

Status: Runtime interface v2 and its exact public entry points are merged. The official Stage-QC consumer is also merged against the reviewed Runtime Authority Manifest and authority-file compatibility model. Real non-synthetic downstream acceptance and production readiness remain `insufficient_evidence`.

Role: `architecture_decision_system`

## Purpose

EV4 Architect decides what should be built and preserves the selected candidate, approved structure, class intent, forbidden work, unknowns, and architecture handoff.

```text
Architect says what should be built.
CE proves how it can be safely built.
Builder executes proven strategy.
Responsive validates post-build responsive behavior.
```

Approved architecture is not automatically approved implementation strategy.

## Quick Start

In a new user-facing Architect session with repository instructions loaded, send:

```text
شروع
```

If no screenshot, section description, active run, or resumable runtime material is present, the assistant returns the fixed intake message from:

```text
manifests/architect-conversation-bootstrap.v1.json
```

If usable project input is supplied with the trigger, run `/intake` directly.

The controlled opening sequence is:

```text
/intake → /research → /decompose
```

Do not skip `/research`.

## Canonical Pipeline

```text
/intake → /research → /decompose → /architectures
→ /score-evidence → /score-audit → /recommend
→ /build-tree → /implementation → /final-audit
→ /handoff-export → /project-gate-export
```

Canonical machine-readable authority:

```text
manifests/architect-pipeline-manifest.v1.json
```

`/builder-feed-export` remains a legacy compatibility output, not canonical Project Gate Producer Export.

## Runtime Authority

The active public Runtime interface is:

```text
ev4-architect-quality-runtime@2.0.0
```

Its machine-readable authority and consumer surface are defined by:

```text
manifests/architect-runtime-authority-manifest.v1.json
contracts/ARCHITECT_RUNTIME_HISTORY_REPLAY_V1.md
scripts/architect_quality_runtime.py
```

The Runtime owns replay, evaluator-derived Stage Results, Run State, Unknown state, candidate lock, Payload issuance, provenance, and Project Gate finalization. A caller-authored Stage Result, Run State, Payload, PASS claim, digest, provenance field, or Handoff Boolean is non-authorizing.

Canonical public operations are exposed through the wrapper and manifest. Consumers must use those public entry points rather than copying Runtime modules or importing private implementation surfaces.

## Minimal Quality-First Continuation

Active continuation authority:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
contracts/ARCHITECT_STAGE_RESULT_V1.md
schemas/ev4-architect-stage-result.v1.schema.json
scripts/architect_quality_runtime.py#evaluate_stage
```

```text
Stage Output
+ replay-derived Run State
+ finite Manifest-owned Stage rules
→ evaluate_stage
→ evaluator-derived Stage Result
```

The normal Run does not require internal Stage Anchors, Validation Bundles, independent Bundle regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, or repository maintenance. Those controls remain optional repository-development, audit, compatibility, or deterministic-regression tooling.

## Quality Boundaries Preserved

The runtime rejects:

- mandatory Stage skipping or non-successor continuation;
- missing, unknown, cross-Stage, failed, or unresolved required checks;
- screenshot-to-Build-Tree shortcuts;
- recommendation before accepted `/score-audit`;
- hidden recommendation during scoring;
- conversion of unknown evidence into exact values;
- `selected_candidate_id` drift after lock;
- silent unknown disappearance;
- arbitrary closure of a downstream-critical unknown;
- missing canonical Build Tree or Implementation content;
- caller-fabricated digest authority and `null == null` fidelity;
- implementation/approved-tree mismatch;
- blocker/high Final Audit findings at handoff;
- invalid canonical Project Gate payload or export;
- legacy Builder Feed substitution.

All detailed evidence, RAG/TUYA source-access, scoring, accessibility, responsive, performance, and Stage hardening controls remain active unless they conflict only on continuation authorization.

## Research Stage

`/research` remains mandatory and records exactly one disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

Only genuinely required unavailable evidence blocks. Research establishes platform capability, not screenshot interpretation or architecture recommendation.

## Unknown Lifecycle

Active unknowns persist through replay-derived state. Omission from later output is not resolution. Ordinary resolution requires an explicit type and explanatory note. A resolvable evidence reference is required only for downstream-critical or Artifact-dependent unknowns.

## Candidate and Content Fidelity

After `/recommend`, `selected_candidate_id` is locked unless a legitimate rerun reaches `/recommend` or earlier.

For `/build-tree` and `/implementation`, canonical content means the existing structured Stage Output. Do not create wrapper Artifacts solely to compute digests.

```text
no real canonical content
→ no claimed digest
```

The evaluator computes content identities from actual canonical content and verifies Implementation against the approved Build Tree representation. Conversational Stage output does not require cryptographic identity.

## EV4 Project Gate Workflow

```text
model-authored Stage Output JSON files
→ Runtime replay and evaluator-derived projections
→ Runtime-issued canonical Architect Stage Payload
→ Runtime-internal Project Gate exporter and validator
→ accepted: CE Input Package
→ needs repair: Architect Repair Package
```

The terminal `/project-gate-export` boundary remains strongly fail-closed.

Direct Project Gate export from a caller-supplied Payload file is unsupported and has been removed.

A decoded JSON object that matches the Payload Schema is not Runtime issuance and cannot authorize Handoff.

Authority ownership:

- Stage Output: model-authored evidence;
- Stage Result and Run State: Runtime-derived;
- Payload: Runtime-issued from complete replay;
- Project Gate artifact and receipt: exporter- and validator-issued.

Canonical Architect payload identity:

```text
ev4-architect-stage-payload@1.0.0
```

## Official Stage-QC Consumer

`rezahh107/EV4-Architect-Stage-QC` is the official local Windows-first QC consumer. It:

- starts a fresh Python interpreter for each selected Architect operation;
- executes one bounded operation per child process;
- loads only the official public Runtime surface from the selected checkout;
- verifies repository identity, Runtime interface, committed authority blob identities, and exact working-tree bytes against its committed Lock;
- preserves actual checkout commit and reviewed Lock reference commit as distinct diagnostics;
- never accepts caller-owned Payload, Stage Result, Run State, provenance, or Handoff authority through the process boundary.

The Stage-QC Lock is a consumer compatibility artifact. Architect remains the sole owner of Runtime semantics, Pipeline order, Payload issuance, and Project Gate finalization.

## Optional Audit Tooling

The Stage Anchor/Bundle contracts, Validation Profiles Registry, and `architect_validation_*` modules remain preserved for repository audit, exact-byte deterministic regression, compatibility evidence, and historical readability. They are not active user-facing transition tickets.

## Validation

```bash
python -m pip install 'jsonschema>=4.22.0' 'pytest>=8.0.0' 'PyYAML>=6.0.0'
python scripts/check-architect-quality-runtime.py
python scripts/check-architect-bootstrap.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p no:cacheprovider -q \
  tests/test_architect_quality_runtime.py \
  tests/test_architect_bootstrap_semantics.py
```

Existing payload, governance, release-pack, Runtime-authority, public-entrypoint, and transaction-boundary suites remain applicable.

## Boundaries

This repository does not perform interactive Elementor execution, prove constructability, complete responsive QA, establish live model-host enforcement, or claim production readiness without downstream evidence.

## Companion Repositories

```text
https://github.com/rezahh107/EV4-Architect-Stage-QC
https://github.com/rezahh107/EV4-Project-Gate
https://github.com/rezahh107/EV4-Constructability-Engineer-Repo
https://github.com/rezahh107/EV4-Builder-Assistant-Repo
https://github.com/rezahh107/EV4-Responsive-Architect
```

## Status Authority

Mutable project and validation status is maintained only in `STATUS.md`. This README is orientation and does not override live repository evidence, the Pipeline Manifest, the Runtime Authority Manifest, active contracts, Schemas, or validators.
