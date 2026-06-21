# EX-DCP-008 — FAQ Accordion

Status: active  
Stage: `/decompose`  
Pattern type: interactive FAQ / accordion content group  

---

## Synthetic input

An FAQ section shows a heading and a vertical list of questions. Some questions have visible answer text while others appear collapsed. Each row may include a plus/minus icon or chevron.

---

## Expected decomposition

### 1. Visible Groups

- item: section header  
  role: framing content group  
  evidence: heading introduces the FAQ area  
  confidence: observed

- item: FAQ item list  
  role: repeated interactive content group  
  evidence: multiple question rows repeat vertically  
  confidence: observed

### 2. Meaningful Content

- item: questions and visible answers  
  content_type: support/help content  
  evidence: FAQ rows contain question text and possibly answer text  
  confidence: observed

- item: expand/collapse indicators  
  content_type: interaction state indicators  
  evidence: chevrons, plus, or minus icons appear on rows  
  confidence: likely

### 3. Repeated Component Candidates

- component_candidate: FAQ item  
  repeated_parts: question text, optional answer, state icon, row boundary  
  evidence: same question-row pattern repeats  
  confidence: observed

### 4. Visual Core

- item: FAQ list  
  evidence: the repeated interactive list is the main body of the section  
  confidence: observed

### 5. Decoration Layers

- item: row dividers or subtle card surfaces  
  decorative_function: separate questions and improve scanability  
  evidence: FAQ rows usually have borders, spacing, or surfaces  
  confidence: likely

### 6. Overlay / Connector Candidates

- item: none clearly visible  
  relationship: no connector relationship is required by the pattern  
  evidence: the main structure is a vertical interactive list  
  implementation_status: unknown  
  confidence: likely

### 7. Responsive Risks

- risk: open answer text can create large vertical expansion  
  reason: expanded FAQ rows may become long on mobile  
  confidence: likely

- risk: screenshot shows only one state  
  reason: collapsed/open states cannot be fully inferred from a static image  
  confidence: observed

### 8. Unknowns

- unknown: which items are open by default  
  why_it_matters: affects interaction and initial layout height  
  blocking: no

- unknown: whether multiple items can remain open simultaneously  
  why_it_matters: affects later widget/interaction decision  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use Accordion widget  
  reason: widget choice belongs to `/architectures`

- assumption: use Toggle widget or custom interaction  
  reason: architecture choice belongs to `/architectures`

Allowed next step:
- `/architectures`
