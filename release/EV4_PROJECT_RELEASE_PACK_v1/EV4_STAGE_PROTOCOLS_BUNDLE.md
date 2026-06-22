# EV4 Stage Protocols Bundle

Status: release_candidate_for_controlled_use
Version: 1.0.0

---

## /intake

Purpose: read user input and project defaults, ask only blocking questions.

Forbidden: architecture, scoring, build tree.

Output: intake snapshot and anchor to `/decompose` or `/research` if platform capability is blocking.

---

## /research

Purpose: prove/disprove platform capabilities using official or approved sources.

Allowed: Elementor capability facts, source pinning, freshness notes.

Forbidden: visual interpretation, scoring, recommendation, build tree.

Payload: `ev4-research-payload@1.0.0`

---

## /decompose

Purpose: convert screenshot/description into visual role map.

Allowed: visible groups, meaningful content, visual core, decoration, repeated candidates, responsive risks, unknowns.

Forbidden: architecture choice, scoring, exact CSS, Elementor tree, RAG/TUYA/doc inference.

---

## /architectures

Purpose: enumerate viable Elementor V4 architecture candidates.

Required: coverage matrix, unknown propagation ledger, hidden recommendation ban, dynamic/loop guardrail, tradeoffs.

Forbidden: selecting winner, scoring, build tree, CSS implementation.

---

## /score-evidence

Purpose: score candidates with rubric and evidence.

Rules:

```text
Unknowns are not numbers.
Use ? for insufficient evidence.
Use N/A only for genuinely non-applicable criteria.
Use provisional_known_percent only when final score is incomplete.
```

Rubric total logic:

```text
Known weighted average × 20 = provisional_known_percent
Final normalized score only if all applicable criteria are known.
```

---

## /score-audit

Purpose: audit Stage 4 scoring mechanics.

Checks:

```text
arithmetic
unknown discipline
N/A denominator
gate override detection
hidden recommendation
inter-candidate consistency
responsive cap
payload schema
```

Stage 5 must not select a winner.

---

## /recommend

Purpose: select primary architecture only after Stage 5 pass/pass_with_minor_flags.

Must use audited candidate set only.

Tie rule: if no audited, provenance-backed tie break exists, ask minimal user question.

---

## /build-tree

Purpose: convert selected architecture into Elementor Structure Panel tree.

Must include:

```text
structure labels
class names
wrapper justification
editability map
decoration map
responsive structure contract
design-system hooks
carried unknowns
```

Naming convention:

```text
[section-role]__[content-group]--[variant]
```

---

## /implementation

Purpose: map approved tree to implementation-ready Elementor plan.

Allowed: widget mapping, settings plan, class/variable map, scoped CSS needs, assets/accessibility, responsive implementation plan.

Forbidden: re-architecture, new scoring, new recommendation, screenshot reinterpretation, unscoped CSS, flattening meaningful content.

Payload: `ev4-implementation-payload@1.0.0`

---

## /final-audit

Purpose: audit implementation before handoff.

Checks: preservation, source access, CSS scope, editability, responsive risk, accessibility, unknown survival, handoff readiness.

Payload: `ev4-final-audit-payload@1.0.0`

---

## /handoff-export

Purpose: package audited output for builder/reviewer.

Allowed: final builder handoff or blocked report.

Forbidden: new decisions, new CSS, new widgets, architecture repair.

Payload: `ev4-handoff-export-payload@1.0.0`

---

## /e2e-screenshot-validation

Purpose: validate that a raster screenshot can be interpreted without textual-fixture reliance.

Current result:

```text
E2E-002 screenshot validation: pass_with_minor_flags
```

Boundary: validates role interpretation for the screenshot, not live Elementor render/export.
