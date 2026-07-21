# EV4 Architect Repo

Status: Architect system active; Architect Stage Payload v1 implemented; Architect Producer Gate Export adoption merged; operator-facing Architect Project Gate exporter implemented pending independent review; Project Gate Architect-to-CE transition implemented at a pinned, fixture-verified scope; real non-synthetic handoff and current-live-head compatibility remain `insufficient_evidence`.

Role: `architecture_decision_system`

## Purpose

EV4 Architect decides what should be built and preserves the selected candidate, approved structure, class intent, forbidden work, and architecture handoff.

```text
Architect says what should be built.
CE proves how it can be safely built.
Builder executes proven strategy.
Responsive validates post-build responsive behavior.
```

Approved architecture is not automatically approved implementation strategy.

<!-- EV4_ARCHITECT_README_QUICK_START_START -->
## Quick Start

In a new user-facing Architect session with the repository instructions loaded, send:

```text
شروع
```

If no screenshot, section description, active run, or valid Stage Anchor is present, the assistant must return the fixed intake message defined in:

```text
manifests/architect-conversation-bootstrap.v1.json
```

If the user supplies `شروع` together with a screenshot or usable section description, do not repeat the bootstrap questions. Run `/intake` using the supplied input.

The controlled opening sequence is:

```text
/intake → /research → /decompose
```

See `release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md` for the operator prompts used after each stage.
<!-- EV4_ARCHITECT_README_QUICK_START_END -->

## EV4 Project Gate Workflow

```text
Architect output
→ EV4 Project Gate
→ accepted: CE Input Package
→ needs repair: Architect Repair Package
```

The complete planned line is:

```text
Architect → Gate → CE → Gate → Builder → Gate → Responsive → Gate
```

The user may submit Architect output to Project Gate. At the currently verified scope, Project Gate can validate the pinned Architect/CE contracts and produce a CE intake package or a fail-closed result with diagnostics. This fixture-tested, pinned-scope path is not evidence of a real-project handoff, compatibility with the current live heads, Builder authorization, or production readiness.

The Project Gate Python verifier, Architect-to-CE CLI transition, and initial local operator UI are implemented at their documented scopes. The transition remains fixture-tested against pinned owner revisions; real non-synthetic handoff and compatibility with the current live heads are not established.

## Architect Stage Payload v1

Canonical Architect payload identity:

```text
ev4-architect-stage-payload@1.0.0
```

This payload is Architect-owned evidence for the common Project Gate Stage Evidence Bundle envelope. It contains selected architecture identity, selected-candidate lock evidence, approved structure model, Architect intent maps, evidence register, unresolved evidence, forbidden work, and downstream-boundary assertions.

Implemented now:

```text
Architect Stage Payload v1 schema and semantic validation
Architect Producer Gate Export adoption merged in PR #14
Architect-owned operator exporter for architect-project-gate.json
Project Gate Architect-to-CE orchestration and CE intake validation at a pinned, synthetic-fixture-tested scope
```

Not implemented yet:

```text
real non-synthetic Architect-to-CE handoff
current-live-head compatibility for the Project Gate transition pins
Builder execution authorization
real Elementor export validation
legacy contract retirement
```

Legacy handoff and builder-feed contracts remain available during migration and are not retired.

## Architect Producer Gate Export

The canonical project execution manifest is:

```text
manifests/architect-pipeline-manifest.v1.json
```

Current project execution sequence:

```text
/intake → /research → /decompose → /architectures
→ /score-evidence → /score-audit → /recommend
→ /build-tree → /implementation → /final-audit
→ /handoff-export → /project-gate-export
```

`/builder-feed-export` remains a legacy compatibility output, not the canonical Producer Gate Export.

`/e2e-test` and `/e2e-screenshot-validation` are validation tracks, not mandatory per-run project execution stages for Producer Gate Export emission.

## Official Project Gate Export Command

The exporter accepts the real active Architect machine payload and produces one operator-facing Gate-ready file without manual JSON editing:

```bash
python scripts/export-architect-project-gate.py \
  --payload path/to/architect-stage-payload.json \
  --run-id <actual-architect-run-id> \
  --output architect-project-gate.json
```

It derives repository identity, branch, exact commit, schema identities, handoff target, and canonical hashes from active repository and run evidence. Invalid payloads produce no export. Synthetic, blocked, or insufficient-evidence inputs cannot produce an allowed handoff.

See `docs/ARCHITECT_PROJECT_GATE_EXPORTER.md` for deterministic identity, Git provenance, atomic writing, blocked-state, and evidence rules.

## Architect Handoff

Architect output should retain, when applicable:

```text
selected_candidate_id
selected_candidate_locked
approved_structure_tree
approved class names and scopes
forbidden_work
architecture and visual intent
known unknowns and missing evidence
production_ready_allowed: false
```

Unproven geometry, assets, overlays, responsive behavior, interaction, Dynamic Loop, accessibility, and version-sensitive UI paths remain explicit for CE review. Silence is not proof of executability.

## Authority

This repository remains authoritative for its own schemas, validators, fixtures, architecture rules, stage contracts, and output semantics.

EV4 Project Gate verifies the handoff. It may run official Architect validation and package existing evidence, but it does not create missing facts, change locked identity, replace Architect contracts, or silently repair the output.

When evidence cannot establish responsibility:

```yaml
status: insufficient_evidence
repair_owner: unresolved
```

## Boundaries

This repository does not perform interactive Elementor execution, prove constructability, complete responsive QA, or claim production readiness without downstream evidence.

## Companion Repositories

```text
https://github.com/rezahh107/EV4-Project-Gate
https://github.com/rezahh107/EV4-Constructability-Engineer-Repo
https://github.com/rezahh107/EV4-Builder-Assistant-Repo
https://github.com/rezahh107/EV4-Responsive-Architect
```

## Status Authority

Mutable project and stage status is maintained only in `STATUS.md`. The summary at the top of this README is derived for orientation and must not override `STATUS.md`, exact repository evidence, or the live default branch.
