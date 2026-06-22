# EV4 Final Output UX Patch

Status: active_addon_for_handoff_export  
Version: 1.0.1  
Applies to: `/handoff-export` and completed pipeline runs  
Language: Persian user-facing explanation, English technical identifiers allowed

---

## Purpose

The base EV4 pipeline produces a technically auditable final handoff. This patch makes the final output clearer for the user.

It adds two required user-facing layers to the end of every `/handoff-export` run:

```text
1. PIPELINE RESULT SNAPSHOT
2. توضیح معلم‌گونه برای کاربر
```

The technical payloads remain authoritative. This patch does not change architecture, scoring, audit, build tree, implementation, or handoff eligibility.

---

## Core Rule

```text
Make the final result understandable without weakening the audit record.
```

The model must explain what the pipeline produced, what the builder can do, what remains risky, and why production readiness is not claimed.

---

## Forbidden Work

This patch must not be used to:

- redesign the section;
- repair implementation;
- remove or soften flags;
- resolve unknowns without evidence;
- add widgets, CSS, classes, settings, assets, colors, sizes, coordinates, or breakpoints;
- convert `pass_with_medium_flags` into a clean pass;
- claim production readiness;
- rewrite the technical payload to sound cleaner.

---

## Language and Template-Key Rule

The final UX layer is user-facing, so its explanatory labels must be Persian.

Rules:

- Keep the two required top-level section headers exactly as written in this file.
- Use the Persian snapshot keys shown in the template below.
- Keep technical identifiers in English inside the values, for example `ARCH-FAM-C`, `Build_Tree_Payload`, `Heading Widget`, `smart-home__feature-card--default`.
- Do not translate schema names, payload names, stage names, class names, widget names, or candidate IDs.
- Do not invent alternate top-level headings.

---

## Required Section 1 — PIPELINE RESULT SNAPSHOT

Every `/handoff-export` output must include this section before or immediately after the technical `Handoff_Payload` summary.

```text
## PIPELINE RESULT SNAPSHOT — خلاصه خروجی خط لوله

1. معماری انتخاب‌شده
   - Candidate selected: ...
   - دلیل انتخاب: یک جمله کوتاه و audit-backed.

2. ساختار ساخت در Elementor
   - Root section: ...
   - Main content layer: ...
   - Repeated cards: ...
   - Visual core: ...
   - Decorative / connector layer: ...

3. محتوای قابل ویرایش
   - Editable text: ...
   - Editable assets: ...

4. موارد صرفاً تزئینی
   - Decorative layers: ...
   - Items that must not contain meaningful content: ...

5. Builder الان می‌تواند
   - ...

6. ریسک‌ها و unknownهای باقی‌مانده
   - Medium flags: ...
   - Minor flags: ...
   - Unknowns: ...

7. چرا production-ready نیست
   - live Elementor rendering not validated;
   - export JSON / EDIS not validated;
   - mobile/tablet behavior unresolved;
   - exact pixel matching not validated.

8. اقدام عملی بعدی
   - ...
```

Rules:

- Use simple Persian for explanatory values and descriptions.
- Keep candidate IDs, class names, widget names, schema names, and payload names in English.
- Do not add new evidence.
- Do not imply clean pass when flags remain.

---

## Required Section 2 — توضیح معلم‌گونه برای کاربر

Every `/handoff-export` output must end with a non-technical explanation in Persian.

The explanation must answer:

```text
- کاربر چه چیزی خواسته بود؟
- مدل چه بررسی‌هایی انجام داد؟
- نتیجه نهایی چیست؟
- Builder دقیقاً با چه چیزی کار را شروع می‌کند؟
- چه چیزهایی هنوز معلوم نیست؟
- چرا این خروجی production-ready نیست؟
```

Recommended style:

```text
فرض کن می‌خواهی این عکس را در Elementor بسازی.
اگر مستقیم از روی عکس شروع کنیم، ممکن است همه چیز را در یک تصویر یا SVG قفل کنیم و بعداً متن‌ها قابل ویرایش نباشند.
برای همین، خط لوله اول عکس را به قطعات قابل فهم تقسیم کرد: کارت‌ها، تصویر مرکزی، خط‌های اتصال، و لایه‌های تزئینی.
بعد چند راه ساخت بررسی شد، امتیاز گرفت، audit شد، و در نهایت یک مسیر کنترل‌شده انتخاب شد.
```

Rules:

- Use short paragraphs.
- Explain like teaching a confused but capable user.
- Use mental imagery when useful.
- Do not oversimplify away risks.
- Do not remove technical IDs entirely; mention the important ones after explaining them.

---

## Completion Criteria

A final handoff is UX-complete only if it includes:

```yaml
final_output_ux_checks:
  pipeline_result_snapshot_present: pass
  teacher_style_persian_explanation_present: pass
  selected_candidate_visible: pass
  builder_next_action_visible: pass
  medium_flags_visible: pass
  production_boundary_visible: pass
  no_clean_pass_overclaim: pass
```

---

## Retrofit Prompt for an Already Completed Run

Use this when `/handoff-export` has already been produced, but the final user-facing explanation was too technical.

```text
Use the EV4 Architect Project Instructions and uploaded reference files.

Reports must be in Persian. Keep Elementor labels, class names, schema names, payload names, and technical identifiers in English.

Use the completed /handoff-export output above as the only source of truth.

Task:
Create a clearer final user-facing output for this same completed pipeline run.

Run only:
- final output UX clarification for the existing /handoff-export

Do not:
- change selected candidate ARCH-FAM-C
- change Build_Tree_Payload
- change Implementation_Payload
- change Handoff_Payload
- redesign
- repair
- add CSS
- add widgets, classes, variables, settings, breakpoints, coordinates, colors, typography, spacing, or assets
- remove or downgrade medium flags
- hide AUD-001 or AUD-002
- resolve unknowns
- claim live Elementor rendering
- claim export JSON / EDIS validation
- claim exact pixel matching
- claim production readiness

Required output:
- PIPELINE RESULT SNAPSHOT — خلاصه خروجی خط لوله
- توضیح معلم‌گونه برای کاربر

Inside PIPELINE RESULT SNAPSHOT, include these nested items:
- معماری انتخاب‌شده
- ساختار ساخت در Elementor
- محتوای قابل ویرایش
- موارد صرفاً تزئینی
- Builder الان می‌تواند
- ریسک‌ها و unknownهای باقی‌مانده
- چرا production-ready نیست
- اقدام عملی بعدی

In the teacher-style Persian explanation, explain very simply:
- I gave you a screenshot and wanted to build it in Elementor.
- You separated editable content, visual core, and decorative connectors.
- You selected ARCH-FAM-C after scoring and audit.
- The builder can now build the controlled structure.
- It is not production-ready yet because mobile behavior, connector geometry, accessibility semantics, live render, and export validation are still unresolved.
```
