# EX-DCP-012 — Overlapping Floating Cards

Status: active  
Stage: `/decompose`  
Pattern type: visual section with overlapping cards/badges around a core visual  

---

## Synthetic input

A section shows a product image, phone mockup, dashboard, or person photo as the central visual. Several floating cards, labels, badges, charts, or avatar clusters overlap around it. The left or top side may include headline text and CTA buttons.

---

## Expected decomposition

### 1. Visible Groups

- item: primary copy group  
  role: meaningful text/action content  
  evidence: headline, paragraph, and CTA may appear near the visual composition  
  confidence: likely

- item: central visual core  
  role: focal image/mockup area  
  evidence: one large visual object anchors the composition  
  confidence: observed

- item: floating card/badge cluster  
  role: layered supporting visual/content group  
  evidence: smaller cards or badges appear around or on top of the core visual  
  confidence: observed

### 2. Meaningful Content

- item: headline, paragraph, and CTA controls  
  content_type: primary section copy and actions  
  evidence: text and button-like controls may be visible  
  confidence: likely

- item: floating card text, labels, or numbers  
  content_type: supporting proof/details or decorative data snippets  
  evidence: small cards may contain text, numbers, icons, or charts  
  confidence: likely

### 3. Repeated Component Candidates

- component_candidate: floating badge/card  
  repeated_parts: small surface, icon/number/label, shadow or border  
  evidence: multiple floating elements share visual treatment  
  confidence: likely

### 4. Visual Core

- item: central product/mockup/person visual  
  evidence: largest image anchors the overlapping composition  
  confidence: observed

### 5. Decoration Layers

- item: shadows, glows, background shapes, floating accents  
  decorative_function: create depth and premium feel  
  evidence: overlapping visuals depend on layered depth cues  
  confidence: observed

### 6. Overlay / Connector Candidates

- item: floating card cluster  
  relationship: visually attached to or orbiting the central visual core  
  evidence: small elements overlap or surround the main visual  
  implementation_status: unknown  
  confidence: observed

### 7. Responsive Risks

- risk: floating cards may collide with copy or core visual  
  reason: overlapping desktop composition can become cramped on tablet/mobile  
  confidence: likely

- risk: visual order may not equal DOM order  
  reason: layered cards can appear visually rearranged by z-index-like composition  
  confidence: likely

### 8. Unknowns

- unknown: whether floating cards contain meaningful real text or decorative placeholder text  
  why_it_matters: affects editability and accessibility decisions  
  blocking: no

- unknown: whether each floating element is a separate asset or part of one image  
  why_it_matters: affects later architecture and asset strategy  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use absolute positioning for floating cards  
  reason: architecture choice belongs to `/architectures`

- assumption: export floating cards as one raster image  
  reason: asset strategy belongs to `/architectures`

Allowed next step:
- `/architectures`
