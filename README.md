# Elementor V4 Architect Prompt Pack

سیستم پرامپت معماری المنتور

This repository stores the stable instructions, stage specifications, rubrics, calibration cases, and examples for a GPT Project that works as an Elementor V4 layout architect and auditor.

## Core Idea

The system is a staged prompt pipeline, not one giant prompt.

Planned pipeline:

1. `/intake`
2. `/research`
3. `/decompose`
4. `/architectures`
5. `/score-evidence`
6. `/score-audit`
7. `/recommend`
8. `/build-tree`
9. `/implementation`
10. `/final-audit`

## Current Status

Current confirmed stage:

- Stage 1 — `/intake`: Project Defaults + Exception Check

See:

- `STATUS.md`
- `01_PROJECT_INSTRUCTIONS.md`
- `stages/01_INTAKE.md`
