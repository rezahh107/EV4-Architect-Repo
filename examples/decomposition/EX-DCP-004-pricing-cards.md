# EX-DCP-004 — Pricing Cards

Status: active  
Stage: `/decompose`  
Pattern type: repeated pricing plan cards  

---

## Synthetic input

A pricing section shows a section heading and three pricing cards. Each card includes plan name, price, billing period, feature list, and CTA button. One plan may be visually emphasized as popular.

---

## Expected decomposition

### 1. Visible Groups

- item: section header  
  role: framing content group  
  evidence: heading and intro text appear above pricing cards  
  confidence: observed

- item: pricing card row  
  role: repeated plan comparison group  
  evidence: three plan cards appear side by side  
  confidence: observed

- item: emphasized plan card  
  role: highlighted content variant  
  evidence: one card may use stronger background, badge, border, or scale  
  confidence: likely

### 2. Meaningful Content

- item: plan names, prices, features, and CTA buttons  
  content_type: pricing and conversion content  
  evidence: each card communicates offer details and an action  
  confidence: observed

### 3. Repeated Component Candidates

- component_candidate: pricing card  
  repeated_parts: plan name, price, period, feature list, CTA, card surface  
  evidence: same plan structure repeats across multiple cards  
  confidence: observed

- component_candidate: feature row  
  repeated_parts: feature text, optional check icon  
  evidence: multiple feature lines repeat inside each card  
  confidence: likely

### 4. Visual Core

- item: pricing card group  
  evidence: the card comparison row is the main visual and functional body  
  confidence: observed

### 5. Decoration Layers

- item: popular badge or emphasized border  
  decorative_function: guide attention to one plan  
  evidence: one plan may be visually highlighted  
  confidence: likely

### 6. Overlay / Connector Candidates

- item: popular badge  
  relationship: label attached to a pricing card  
  evidence: badge may sit on or near one card surface  
  implementation_status: unknown  
  confidence: likely

### 7. Responsive Risks

- risk: side-by-side comparison may become too narrow  
  reason: pricing cards contain dense text and CTA buttons  
  confidence: likely

- risk: emphasized plan may disrupt mobile stacking order  
  reason: visual priority on desktop may need a deliberate mobile order  
  confidence: likely

### 8. Unknowns

- unknown: whether the popular badge is real text or decorative label  
  why_it_matters: affects accessibility and content modeling  
  blocking: no

- unknown: whether all cards have equal feature counts  
  why_it_matters: affects height alignment and later architecture  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use Price Table widget  
  reason: widget choice belongs to `/architectures`

- assumption: duplicate one card component three times  
  reason: implementation choice belongs to later stages

Allowed next step:
- `/architectures`
