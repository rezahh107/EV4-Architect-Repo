# Stage 7 - /build-tree

Status: draft_scaffolded
Version: 0.1.0
Payload schema: ev4-build-tree-payload@0.1.0

Purpose: convert the audited /recommend result into an Elementor Structure Panel plan.

Required anchor: source_stage=/recommend, target_stage=/build-tree, selected candidate, blockers, unknowns, confirmations, build-tree readiness.

Core rule: build from the audited recommendation, not from visual preference.

Naming convention scaffold:
[section-role]__[content-group]--[variant]

Examples:
- hero__copy--primary
- hero__visual--dashboard
- feature-grid__card--default
- pricing__card--featured

Allowed:
- Produce container and widget hierarchy.
- Name groups for Elementor Structure Panel.
- Assign candidate class names.
- Map editable content, decoration, overlays, and responsive structure intent.
- Carry forward unknowns and confirmations.
- Emit NEXT STAGE ANCHOR for /implementation.

Forbidden:
- No final CSS.
- No final implementation code.
- No unapproved plugin dependency.
- No override of Stage 6.
- No dropping unknowns.

Output sections:
1. Input authorization
2. Elementor Structure Panel Tree
3. Naming Map
4. Content Editability Map
5. Overlay / Decoration Map
6. Responsive Structure Contract
7. Design-System Hook Map
8. Handoff to /implementation
9. NEXT STAGE ANCHOR

Pass criteria: valid anchor, audited recommendation used, clear tree, naming convention followed, unknowns preserved, no final implementation, next anchor emitted.

Requires hardening: tree depth limits, wrapper budget, widget constraints, responsive examples, build-tree calibration cases.
