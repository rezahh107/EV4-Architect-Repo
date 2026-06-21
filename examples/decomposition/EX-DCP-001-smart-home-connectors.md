# EX-DCP-001 — Smart Home Connector Section

Status: active  
Stage: `/decompose`  
Pattern type: visual-core section with side feature cards and connector decoration  

---

## Synthetic input

A section shows a central smart-home or house illustration. Three rounded feature cards appear on the left and three rounded feature cards appear on the right. Thin curved lines visually connect the side cards toward the central house. Each card contains an icon, a heading, and a short description.

---

## Expected decomposition

### 1. Visible Groups

- item: left feature-card group  
  role: side content group  
  evidence: three repeated rounded cards are visible on the left side  
  confidence: observed

- item: central house image area  
  role: visual focal area  
  evidence: a large house illustration anchors the center  
  confidence: observed

- item: right feature-card group  
  role: side content group  
  evidence: three repeated rounded cards are visible on the right side  
  confidence: observed

### 2. Meaningful Content

- item: feature cards  
  content_type: icon, heading, and short descriptive text  
  evidence: each card communicates a feature  
  confidence: observed

### 3. Repeated Component Candidates

- component_candidate: feature card  
  repeated_parts: icon, heading, short description, rounded surface  
  evidence: the same card pattern repeats six times  
  confidence: observed

### 4. Visual Core

- item: central house illustration  
  evidence: it is the largest central visual object and the connector lines point toward it  
  confidence: observed

### 5. Decoration Layers

- item: connector lines  
  decorative_function: visually associate feature cards with the central visual core  
  evidence: thin curved lines connect side groups toward the center  
  confidence: observed

### 6. Overlay / Connector Candidates

- item: connector line layer  
  relationship: visually bridges feature cards and central visual core  
  evidence: connector lines span between side groups and the center  
  implementation_status: unknown  
  confidence: observed

### 7. Responsive Risks

- risk: connector lines may fail when layout stacks  
  reason: desktop spatial relationships may not exist on mobile  
  confidence: likely

- risk: card text length can disturb visual symmetry  
  reason: card heights may diverge if descriptions change  
  confidence: likely

### 8. Unknowns

- unknown: whether the house image is available separately  
  why_it_matters: affects later architecture options  
  blocking: no

- unknown: whether connector lines must remain visible on mobile  
  why_it_matters: affects later responsive strategy  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use SVG for connector lines  
  reason: implementation choice belongs to `/architectures`

- assumption: use three-column Flex  
  reason: architecture choice belongs to `/architectures`

Allowed next step:
- `/architectures`
