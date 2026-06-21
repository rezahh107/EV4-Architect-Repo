# E2E-001 Fixture — Smart Home Connector Hero Section

Status: active_fixture
Version: 1.0.0
Fixture schema: ev4-e2e-fixture@1.0.0
Intended test plan: `experiments/END_TO_END_PIPELINE_TEST_PLAN.md`

---

## Purpose

This fixture provides the first realistic, text-described mockup input for the EV4 end-to-end validation run.

It is not a final design recommendation. It is a controlled stress fixture used to test whether the EV4 pipeline preserves visible evidence, unknowns, anchors, scoring gates, repair routes, and handoff boundaries across all stages.

---

## Input Type

```text
input_type: realistic_mockup_description
section_family: smart-home connector / IoT landing hero
viewport_basis: desktop-first with expected tablet/mobile adaptation
visual_source_quality: textual mockup, no raster screenshot attached
```

Because this fixture is textual rather than an actual screenshot, all purely visual details must be treated as described evidence only. Any unstated exact size, spacing, breakpoint, z-index, asset filename, animation timing, or Elementor setting remains unknown.

---

## User-Facing Section Goal

Create an Elementor V4 landing-page hero section for a smart-home automation product that helps users connect devices, monitor rooms, and automate daily routines.

The section should feel modern, clean, technical, trustworthy, and automation-oriented.

---

## Visible Mockup Description

The section is a full-width hero block with a two-column composition.

Left side:

- eyebrow label: `SMART HOME AUTOMATION`
- large headline: `Connect every room. Automate every routine.`
- short paragraph: `Control lights, sensors, scenes, and energy usage from one calm dashboard.`
- primary CTA: `Start automation`
- secondary CTA: `View devices`
- three small feature chips:
  - `No-code scenes`
  - `Energy insights`
  - `Device groups`

Right side:

- one large rounded dashboard card showing a simplified smart-home interface;
- the card contains:
  - a top mini status bar;
  - four repeated device tiles;
  - one circular energy chart;
  - one small room-status list;
- two decorative connector lines appear behind or around the dashboard card;
- three small floating device nodes sit around the dashboard card:
  - thermostat node;
  - light node;
  - lock node.

Background:

- soft off-white / very light warm neutral background;
- subtle pale grid or radial glow behind the right visual area;
- no heavy dark background;
- no photographic image required.

---

## Required Stress Features

This fixture intentionally includes the minimum E2E stress signals:

| Stress feature | Fixture element | Expected pipeline behavior |
|---|---|---|
| Repeated component group | four device tiles | should become a repeatable editable group, not a flattened image |
| Meaningful visual core | dashboard card with status/tiles/chart/list | should remain semantically represented in build tree |
| Decorative layer | connector lines and radial/grid glow | should be classified as decorative and contained |
| Responsive risk | two-column hero + floating nodes | should carry mobile stacking and collision risk forward |
| Unknown to preserve | exact breakpoints, spacing, z-index, asset choice, animation | must remain unknown unless later evidence provides values |
| Editability requirement | headline, paragraph, CTAs, chips, tiles | must remain editable text/widgets where possible |
| CSS-scope risk | connector lines and glow | if CSS is needed, it must be section-scoped |
| Final-audit block risk | hidden absolute visual nodes on mobile | Stage 9 should flag/block if implementation hides meaningful content or leaks CSS |

---

## Hard Constraints For The E2E Test

```text
- Prefer Elementor-native containers/widgets/classes/variables.
- Do not require Elementor Pro unless a stage explicitly proves and justifies the dependency.
- Do not use third-party plugins as default.
- Preserve normal-flow content first.
- Decorative connector lines may use scoped CSS only if native controls are insufficient.
- Do not flatten meaningful dashboard content into one image unless the pipeline marks that as a deliberate tradeoff and audits editability loss.
- Do not invent exact pixels, breakpoints, z-index values, image URLs, icon libraries, or animation timings.
```

---

## Known Unknowns To Carry Forward

```text
U-E2E-001: exact desktop/tablet/mobile breakpoints are not provided.
U-E2E-002: exact spacing scale is not provided.
U-E2E-003: exact color tokens are not provided beyond light neutral + modern technical mood.
U-E2E-004: exact dashboard tile content beyond labels is not provided.
U-E2E-005: exact icon source/library is not provided.
U-E2E-006: exact connector-line geometry and z-index are not provided.
U-E2E-007: whether animation is required is not provided.
U-E2E-008: whether Elementor Pro is available is not provided.
U-E2E-009: whether the right dashboard is purely illustrative or should use dynamic data is not provided.
```

---

## Expected Stage Pressure Points

### `/decompose`

Must classify:

- left text content as meaningful content;
- CTA buttons as meaningful interactive controls;
- feature chips as meaningful supporting content;
- dashboard card as visual core with meaningful substructure;
- connector lines and glow as decorative;
- floating device nodes as ambiguous: meaningful visual labels if carrying device meaning, decorative only if not needed for comprehension.

### `/architectures`

Must enumerate at least these candidate families:

- native container/card/widget composition;
- hybrid native composition plus section-scoped decorative CSS;
- flattened right-side visual asset approach, with editability penalty;
- custom-heavy absolute-position visual stage, with responsive and maintenance risk.

It must not recommend a winner in this stage.

### `/score-evidence`

Must score only from fixture evidence, rubric, and approved candidates.

It must not boost scores because TUYA or RAG generally likes design-system structure. Unknown values must not become numeric evidence.

### `/score-audit`

Must catch:

- unknowns converted to scores;
- hidden recommendation language;
- editability penalty ignored for flattened visual asset;
- responsive collision risk softened too much.

### `/recommend`

Should recommend only from audited eligible candidates. If native+scoped-CSS and native-only tie too closely, it must preserve tie/confirmation state instead of forcing a preference.

### `/build-tree`

Must produce an Elementor-readable Structure Panel tree with meaningful text and repeated device tiles editable.

### `/implementation`

Must produce settings maps and scoped CSS needs without inventing exact values.

### `/final-audit`

Must block handoff if meaningful content is hidden, CSS leaks globally, unknowns disappear, or implementation changes architecture.

### `/handoff-export`

Must package only final-audited decisions and preserve all audit flags. It must not introduce new CSS, new widgets, new architecture, or new visual details.

---

## Fixture Pass Use

This fixture can be used for:

```text
E2E test id: E2E-001
run mode: full pipeline validation
required output schema: ev4-e2e-test-report@1.0.0
release effect: may reduce but not automatically remove release blocker unless the report passes every required gate
```

---

## Fixture Self-Audit

```text
fixture_has_repeated_group: yes
fixture_has_meaningful_visual_core: yes
fixture_has_decorative_layer: yes
fixture_has_responsive_risk: yes
fixture_has_unknowns_to_preserve: yes
fixture_uses_realistic_section_type: yes
fixture_is_actual_screenshot: no
limitation: textual mockup can validate contracts and propagation but cannot validate pixel-accurate visual interpretation
```
