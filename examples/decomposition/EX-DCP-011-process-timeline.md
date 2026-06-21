# EX-DCP-011 — Process Timeline

Status: active  
Stage: `/decompose`  
Pattern type: sequential steps with connectors  

---

## Synthetic input

A process section shows four or five steps arranged horizontally or vertically. Each step has a number, icon, title, short description, and a line or arrow connecting the steps.

---

## Expected decomposition

### 1. Visible Groups

- item: section header  
  role: framing content group  
  evidence: heading introduces the process or workflow  
  confidence: observed

- item: process step sequence  
  role: ordered repeated content group  
  evidence: multiple numbered or icon-based steps appear in sequence  
  confidence: observed

- item: connector line/arrow group  
  role: sequence relationship visual  
  evidence: lines or arrows visually link the steps  
  confidence: observed

### 2. Meaningful Content

- item: step numbers, titles, and descriptions  
  content_type: ordered instructional/process content  
  evidence: each step communicates one part of the process  
  confidence: observed

### 3. Repeated Component Candidates

- component_candidate: process step item  
  repeated_parts: number/icon, title, description, step container  
  evidence: same step structure repeats across the sequence  
  confidence: observed

### 4. Visual Core

- item: process step sequence  
  evidence: the ordered steps are the main section body  
  confidence: observed

### 5. Decoration Layers

- item: connector lines or arrows  
  decorative_function: communicate progression and continuity  
  evidence: visual connectors link the repeated steps  
  confidence: observed

### 6. Overlay / Connector Candidates

- item: timeline connector layer  
  relationship: visually links ordered steps  
  evidence: line or arrow spans between step items  
  implementation_status: unknown  
  confidence: observed

### 7. Responsive Risks

- risk: horizontal connector sequence may break on mobile  
  reason: desktop row may need vertical stacking or simplified connectors  
  confidence: likely

- risk: order semantics must remain clear after stacking  
  reason: process order is meaningful content, not decoration only  
  confidence: observed

### 8. Unknowns

- unknown: whether connector lines are meaningful or purely decorative  
  why_it_matters: affects accessibility and mobile simplification decisions  
  blocking: no

- unknown: whether steps are interactive links or static content  
  why_it_matters: affects content and widget choice later  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use Timeline widget  
  reason: widget choice belongs to `/architectures`

- assumption: draw connector with CSS border or SVG  
  reason: implementation choice belongs to `/architectures`

Allowed next step:
- `/architectures`
