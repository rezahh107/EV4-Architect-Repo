# Stage 4 Scoring Calibration Examples

Status: active  
Applies to: Stage 4 `/score-evidence` and Stage 5 `/score-audit`

---

## Purpose

This folder contains synthetic scoring calibration cases.

They are used to prevent scoring drift in Stage 4 and to give Stage 5 concrete audit anchors.

The examples are not design recommendations. They show expected scoring behavior for evidence handling, arithmetic safety, gate enforcement, and non-applicable criteria.

---

## Active Calibration Cases

| ID | File | Teaches |
|---|---|---|
| SCORING-CAL-001 | `SCORING-CAL-001-contradicted-evidence.md` | Contradicted evidence should lower score or trigger a gate, not become `?` |
| SCORING-CAL-002 | `SCORING-CAL-002-absent-vs-contradicted.md` | Difference between `ABSENT_EVIDENCE` and `CONTRADICTED_EVIDENCE` |
| SCORING-CAL-003 | `SCORING-CAL-003-arithmetic-needs-audit.md` | Arithmetic `needs_audit`, provisional score, and tool verification |
| SCORING-CAL-004 | `SCORING-CAL-004-overlay-na.md` | Overlay Containment `N/A` and denominator exclusion |

---

## Usage Rules

Stage 4 must consult this folder when the case involves:

- contradicted evidence,
- absent evidence,
- non-applicable criteria,
- arithmetic uncertainty,
- immediate rejection gate risk,
- hidden gate override risk.

Stage 5 must use these cases as audit anchors when checking whether Stage 4 applied the scoring rules consistently.

---

## Calibration Rule

Examples calibrate behavior; they do not override the rubric.

If a calibration example and the rubric appear to conflict, the rubric controls and the example must be repaired.
