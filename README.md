# EV4 Architect Repo

Status: Architect system active; Project Gate integration planned; Project Gate program not implemented.

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

The user will upload the Architect output and run one check. A successful result provides the CE package. A failed result provides a plain Persian repair package for the Architect-connected model. The corrected output is checked again before CE receives it.

The Python verifier and simple user interface are not implemented yet.

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

## Current Pipeline

```text
/intake → /research → /decompose → /architectures
→ /score-evidence → /score-audit → /recommend
→ /build-tree → /implementation → /final-audit
→ /handoff-export → /builder-feed-export
```

`/builder-feed-export` is an architecture handoff or CE intake source unless it has passed the CE gate.

## Companion Repositories

```text
https://github.com/rezahh107/EV4-Project-Gate
https://github.com/rezahh107/EV4-Constructability-Engineer-Repo
https://github.com/rezahh107/EV4-Builder-Assistant-Repo
https://github.com/rezahh107/EV4-Responsive-Architect
```

## Status

```yaml
role: architecture_decision_system
selected_candidate_authority: architect
constructability_gate_required: true
project_gate_handoff: documented
project_gate_runtime: not_implemented
production_ready: false
```
