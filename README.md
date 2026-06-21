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

Current confirmed stages:

- Stage 1 — `/intake`: Project Defaults + Exception Check
- Stage 2 — `/decompose`: Controlled Visual Role Decomposition
- Stage 2.1 — `/decomposition-example-bank`: 12 synthetic pattern-based examples plus authoring standard
- Stage 3 — `/architectures`: Architecture Enumeration

Current next stage to define:

- Stage 4 — `/score-evidence`: Evidence-bound architecture scoring

See:

- `STATUS.md`
- `01_PROJECT_INSTRUCTIONS.md`
- `stages/01_INTAKE.md`
- `stages/02_DECOMPOSE.md`
- `stages/03_ARCHITECTURES.md`
- `examples/decomposition/README.md`
