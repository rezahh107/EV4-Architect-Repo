# EX-DCP-009 — Stats / Metrics Section

Status: active  
Stage: `/decompose`  
Pattern type: repeated metric blocks  

---

## Synthetic input

A metrics section shows four large numbers with short labels, optional icons, and a short heading. The metric blocks are aligned in one row on desktop.

---

## Expected decomposition

### 1. Visible Groups

- item: section intro  
  role: framing content group  
  evidence: heading or short intro appears above or beside metric blocks  
  confidence: likely

- item: metric block row  
  role: repeated data-summary group  
  evidence: multiple large numbers and labels repeat horizontally  
  confidence: observed

### 2. Meaningful Content

- item: metric numbers and labels  
  content_type: quantitative proof or summary data  
  evidence: numbers and labels communicate outcomes or scale  
  confidence: observed

- item: optional icons  
  content_type: supporting semantic or decorative iconography  
  evidence: icons may appear above or beside metrics  
  confidence: likely

### 3. Repeated Component Candidates

- component_candidate: metric item  
  repeated_parts: number, label, optional icon, consistent spacing  
  evidence: metric blocks repeat with a consistent internal pattern  
  confidence: observed

### 4. Visual Core

- item: metric row/grid  
  evidence: repeated numbers dominate the section and act as the core message  
  confidence: observed

### 5. Decoration Layers

- item: separators, background surface, or subtle dividers  
  decorative_function: segment metrics and guide scanning  
  evidence: metrics may be separated by lines or card surfaces  
  confidence: likely

### 6. Overlay / Connector Candidates

- item: none clearly visible  
  relationship: no connector relationship is required by the pattern  
  evidence: metrics are independent repeated content blocks  
  implementation_status: unknown  
  confidence: likely

### 7. Responsive Risks

- risk: large numbers may overflow on narrow screens  
  reason: numeric values can be wide, especially with suffixes like +, %, K, or M  
  confidence: likely

- risk: metric row must stack or wrap  
  reason: four columns may be too narrow on mobile  
  confidence: likely

### 8. Unknowns

- unknown: whether numbers animate/count up  
  why_it_matters: affects later widget/interaction decisions  
  blocking: no

- unknown: whether icons are meaningful or decorative  
  why_it_matters: affects accessibility and content modeling  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use Counter widget  
  reason: widget choice belongs to `/architectures`

- assumption: use four-column Flex or Grid  
  reason: architecture choice belongs to `/architectures`

Allowed next step:
- `/architectures`
