# Stage 9 - /final-audit

Status: draft_scaffolded
Version: 0.1.0
Payload schema: ev4-final-audit-payload@0.1.0

Purpose: audit the implementation plan before it is treated as ready for handoff.

Required anchor: source_stage=/implementation, target_stage=/final-audit, implementation payload, blockers, unresolved confirmations, debug trace id if present.

Core rule: audit the implementation plan against the approved architecture and project defaults.

Allowed:
- Check architecture preservation.
- Check editability, normal flow, overlay containment, responsive risk, accessibility, performance, and design-system fit.
- Check that unknowns and confirmations were not lost.
- Produce repair routing.
- Emit NEXT STAGE ANCHOR for /handoff-export if pass.

Forbidden:
- No new recommendation.
- No new implementation plan.
- No silent repair.
- No final approval if blockers remain.

Output sections:
1. Input authorization
2. Architecture Preservation Audit
3. Elementor-Native Audit
4. Editability Audit
5. Responsive Audit
6. Accessibility Audit
7. Performance Audit
8. Design-System Audit
9. Blockers and Repair Routes
10. Final Audit Status
11. NEXT STAGE ANCHOR

Final statuses:
- pass
- pass_with_minor_flags
- fail_requires_implementation_repair
- fail_requires_build_tree_repair
- fail_requires_recommendation_repair
- fail_missing_input

Pass criteria: all blockers checked, repair routes explicit, no recommendation leakage, no hidden assumptions, next anchor emitted only on pass or pass_with_minor_flags.

Requires hardening: final checklist details, severity taxonomy, repair examples, regression examples.
