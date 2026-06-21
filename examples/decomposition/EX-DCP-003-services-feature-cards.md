# EX-DCP-003 — Services / Feature Cards Grid

Status: active  
Stage: `/decompose`  
Pattern type: repeated cards grid  

---

## Synthetic input

A services section shows a heading and intro text followed by a grid of six service cards. Each card contains an icon, service title, short description, and sometimes a small link or arrow. Cards share the same visual style.

---

## Expected decomposition

### 1. Visible Groups

- item: section header  
  role: introductory content group  
  evidence: heading and short paragraph appear above the grid  
  confidence: observed

- item: service-card grid  
  role: repeated content group  
  evidence: multiple cards repeat in a regular grid  
  confidence: observed

### 2. Meaningful Content

- item: section heading and intro  
  content_type: section framing copy  
  evidence: text introduces the service list  
  confidence: observed

- item: service cards  
  content_type: repeated service descriptions  
  evidence: each card communicates a distinct service  
  confidence: observed

### 3. Repeated Component Candidates

- component_candidate: service card  
  repeated_parts: icon, title, description, optional link/arrow, card surface  
  evidence: same internal structure repeats across the grid  
  confidence: observed

### 4. Visual Core

- item: service-card grid  
  evidence: the repeated card grid is the main section content and visual body  
  confidence: observed

### 5. Decoration Layers

- item: card shadows or border accents  
  decorative_function: separate cards and create depth  
  evidence: cards have surfaces, borders, or shadows  
  confidence: likely

### 6. Overlay / Connector Candidates

- item: none clearly visible  
  relationship: no connector or overlay relationship is required by the visible pattern  
  evidence: cards appear as standard grid items  
  implementation_status: unknown  
  confidence: likely

### 7. Responsive Risks

- risk: grid column count must adapt across breakpoints  
  reason: six cards may need to shift from 3 columns to 2 or 1  
  confidence: likely

- risk: unequal description length may create uneven card heights  
  reason: repeated cards can diverge if text length varies  
  confidence: likely

### 8. Unknowns

- unknown: whether cards are clickable or only informational  
  why_it_matters: affects later semantic and interaction decisions  
  blocking: no

- unknown: exact number of service cards in final content  
  why_it_matters: affects grid architecture and component reuse  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use CSS Grid or Flex wrap  
  reason: layout implementation belongs to `/architectures`

- assumption: create Elementor Component for card  
  reason: component decision belongs to later stages

Allowed next step:
- `/architectures`
