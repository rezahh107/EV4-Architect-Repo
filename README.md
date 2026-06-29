# EV4 Architect Repo

Status: constructability_gate_alignment_planned  
Current GitHub slug: `elementor-v4-architect-prompt-pack`  
Recommended slug: `EV4-Architect-Repo`  
Role: `architecture_decision_system`  
Primary downstream gate: `EV4-Constructability-Engineer-Repo`

---

## Summary

`EV4 Architect` decides **what should be built** for an Elementor V4 section.

It is a staged architecture, scoring, audit, recommendation, and handoff system. It is not the interactive Builder and it is not the Constructability Engineer.

```text
Architect says what should be built.
Constructability Engineer proves how it can be safely built.
Builder executes only proven strategy.
Responsive Architect validates and repairs post-build responsive behavior.
```

Core principle:

```text
Approved architecture ≠ approved implementation strategy.
```

This repo may approve a high-level architecture and selected candidate. That approval does not automatically prove that every implementation detail is ready for Builder execution.

---

## Repository Role

This repository owns:

```text
- visual intake and decomposition
- architecture candidate generation
- architecture scoring and audit
- selected_candidate_id decision
- approved structure tree
- approved class names
- handoff/export packaging
- architecture-level forbidden work
```

This repository must not:

```text
- act as the interactive Elementor Builder
- perform checkpoint-based live build execution
- silently resolve execution dependencies
- claim geometry, overlay, responsive, interaction, or Dynamic Loop execution is proven unless evidence exists
- change selected_candidate_id after lock
- claim production readiness without downstream QA evidence
```

---

## Constructability Gate Alignment

The downstream path is now:

```text
EV4 Architect Repo
        │
        ▼
EV4 Constructability Engineer Repo
        │
        ▼
EV4 Builder Assistant Repo
        │
        ▼
EV4 Responsive Architect Repo
```

The Architect output is an approved architecture handoff, not a final Builder-executable package.

Before Builder receives execution instructions, the Constructability Engineer must inspect whether implementation strategy is actually proven.

Examples of execution dependencies the Architect may leave under-specified:

```text
- connector geometry
- source and target anchors
- asset source or placeholder policy
- overlay containment
- z-index / positioning model
- responsive scope
- interaction behavior
- Dynamic Loop / data binding approval
- accessibility evidence
- exact Elementor UI control evidence
```

If these are not proven, the package must go to the Constructability Engineer first, not directly to Builder.

---

## Current Pipeline

```text
/intake
/research
/decompose
/architectures
/score-evidence
/score-audit
/recommend
/build-tree
/implementation
/final-audit
/handoff-export
/builder-feed-export
```

### Stage 11 — `/builder-feed-export`

`/builder-feed-export` remains the compatibility export stage for producing downstream package data.

Its output must be treated as an Architect handoff or Constructability intake source unless it has passed the Constructability Engineer gate.

It must not allow Builder to decide strategy. It must not imply that execution dependencies are proven merely because the architecture is approved.

---

## Smart Home Connector Lesson

The Smart Home Connector case exposed the missing middle role.

Architect approved:

```text
- decorative connector layer
- Association Lines / SVG node
- connector visual intent between feature cards and central house visual
```

But safe execution also required:

```text
- source anchors for feature cards
- target anchor for the central visual
- connector geometry strategy
- overlay containment
- z-index / positioning model
- repair policy for drift
```

The Builder should not have been forced to choose between one integrated SVG, six independent SVG connectors, CSS lines, or temporary skip.

That choice belongs to the Constructability Engineer or requires Architect/User evidence.

Rule:

```text
Silence from Architect is not proof of executability.
not proven executable → not builder-ready
```

---

## Output Contract

Architect output should preserve:

```yaml
selected_candidate_locked: true
selected_candidate_id: <approved candidate id>
approved_structure_tree: present
approved_class_names: present
forbidden_work: visible
production_ready_allowed: false
```

Architect output may include:

```text
- implementation notes
- visual intent
- decoration-only map
- editable content map
- first suggested execution batch
```

But these do not bypass Constructability review if execution dependencies remain unproven.

---

## Companion Repositories

```text
EV4 Architect Repo
Current: https://github.com/rezahh107/elementor-v4-architect-prompt-pack
Recommended: https://github.com/rezahh107/EV4-Architect-Repo

EV4 Constructability Engineer Repo
https://github.com/rezahh107/EV4-Constructability-Engineer-Repo

EV4 Builder Assistant Repo
https://github.com/rezahh107/EV4-Builder-Assistant-Repo

EV4 Responsive Architect
https://github.com/rezahh107/EV4-Responsive-Architect
```

---

## Important Files

```text
STATUS.md
STATUS_0.16.1_BUILDER_FEED_EXPORT.md
02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
contracts/STAGE_ANCHOR_CONTRACT.md
contracts/PARTIAL_RERUN_CONTRACT.md
contracts/BUILD_TREE_NAMING_AND_STRUCTURE_CONTRACT.md
diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md
stages/10_HANDOFF_EXPORT.md
stages/11_BUILDER_FEED_EXPORT.md
schemas/ev4-builder-context-package.schema.json
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_PROTOCOL.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md
```

---

## Production Boundary

This project may produce a controlled architecture handoff or Constructability intake package.

It must not claim:

```text
production-ready
release-ready
pixel-perfect
live Elementor validated
export JSON / EDIS validated
browser validated
responsive final QA complete
```

unless matching downstream evidence exists.

---

## Current Status

```yaml
project_status:
  role: architecture_decision_system
  selected_candidate_authority: architect
  constructability_gate_required: true
  builder_direct_execution_allowed: false_unless_constructability_ready
  live_elementor_rendering: not_validated
  real_elementor_export_json_or_EDIS: not_validated
  exact_pixel_matching: not_validated
  production_ready: false
```
