# EX-DCP-010 — Product / Portfolio Grid

Status: active  
Stage: `/decompose`  
Pattern type: repeated item cards with image and metadata  

---

## Synthetic input

A portfolio or product section shows a heading, filter tabs or category labels, and a grid of item cards. Each card includes an image, title, category/meta text, and possibly a button or hover indicator.

---

## Expected decomposition

### 1. Visible Groups

- item: section header  
  role: framing content group  
  evidence: heading introduces the grid  
  confidence: observed

- item: filter/category controls  
  role: possible interactive filtering group  
  evidence: tabs or category labels appear above the grid  
  confidence: likely

- item: item card grid  
  role: repeated visual/content group  
  evidence: multiple image-based cards repeat in a grid  
  confidence: observed

### 2. Meaningful Content

- item: card images, titles, meta/category text, and CTA indicators  
  content_type: portfolio/product item content  
  evidence: each card represents a distinct item  
  confidence: observed

### 3. Repeated Component Candidates

- component_candidate: item card  
  repeated_parts: image, title, category/meta, optional CTA or hover cue  
  evidence: same card pattern repeats across the grid  
  confidence: observed

- component_candidate: filter tab  
  repeated_parts: label and active/inactive state  
  evidence: similar controls repeat in a row  
  confidence: likely

### 4. Visual Core

- item: product/portfolio grid  
  evidence: the repeated image cards dominate the section body  
  confidence: observed

### 5. Decoration Layers

- item: hover overlays, shadows, or image masks  
  decorative_function: improve visual hierarchy and interaction affordance  
  evidence: visual card styling or overlay-like cues may be visible  
  confidence: likely

### 6. Overlay / Connector Candidates

- item: card hover overlay or label overlay  
  relationship: text/action may appear layered over card image  
  evidence: some item cards may show labels or controls on top of images  
  implementation_status: unknown  
  confidence: likely

### 7. Responsive Risks

- risk: grid column count must adapt  
  reason: item cards need fewer columns on tablet/mobile  
  confidence: likely

- risk: image aspect ratios may vary  
  reason: inconsistent images can break grid rhythm  
  confidence: likely

### 8. Unknowns

- unknown: whether filter tabs are functional or decorative labels  
  why_it_matters: affects interaction and widget/architecture choice  
  blocking: no

- unknown: whether overlays appear only on hover  
  why_it_matters: screenshot may show one interaction state only  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use Portfolio widget  
  reason: widget choice belongs to `/architectures`

- assumption: use CSS Grid or Loop Grid  
  reason: architecture choice belongs to `/architectures`

Allowed next step:
- `/architectures`
