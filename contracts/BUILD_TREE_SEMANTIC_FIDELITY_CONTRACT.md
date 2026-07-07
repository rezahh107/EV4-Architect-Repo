# Build Tree Semantic Fidelity Contract

Status: active
Version: 1.0.0
Applies to: `/build-tree`, `/handoff-export`, `/project-gate-export`

## Normative rule

The detailed Elementor Build Tree is the primary product of the Architect pipeline.
Research, scoring, implementation planning, handoff, concise output, and Project Gate export must preserve and transfer the complete approved tree.
They must not reduce, merge, collapse, omit, or rename meaningful structure merely to shorten a user-facing response.

## Required semantic role coverage

Every authorized source role must either:

1. map to explicit Build Tree nodes; or
2. record an evidence-backed authorization to combine it.

Silent disappearance is invalid.

Required carrier:

```yaml
semantic_role_coverage:
  - source_role_id:
    source_role:
    source_evidence_refs:
    mapped_node_ids:
    disposition: separate_node | authorized_composite | not_applicable
    authorization_ref:
    unresolved_reason:
```

## Fixture boundary

`architect-tree-reference-voice-assistant` is a synthetic approved reference example for structural fidelity only. It is not a universal template, not a mandatory node count, not a real Elementor export, and not browser or WordPress evidence.

## Failure conditions

Reject at least: missing root, duplicate node IDs, orphan nodes, cycles, missing source roles, unauthorized collapse, meaningful content trapped in static SVG/HTML, vague labels, invalid class names, unjustified wrappers, overlays outside a named relative stage, dropped unknowns, missing responsive structural intent, and user-summary substitution for the full machine artifact.
