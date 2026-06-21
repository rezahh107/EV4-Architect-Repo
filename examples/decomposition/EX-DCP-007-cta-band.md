# EX-DCP-007 — CTA Band

Status: active  
Stage: `/decompose`  
Pattern type: call-to-action band with background visual or decoration  

---

## Synthetic input

A full-width call-to-action band contains a short headline, supporting sentence, one or two CTA buttons, and a decorative background image, gradient, shape, or abstract pattern.

---

## Expected decomposition

### 1. Visible Groups

- item: CTA content group  
  role: primary conversion message  
  evidence: headline, supporting text, and buttons appear together  
  confidence: observed

- item: background visual area  
  role: decorative or atmospheric layer  
  evidence: image, gradient, or abstract pattern appears behind the CTA content  
  confidence: observed

### 2. Meaningful Content

- item: headline and supporting text  
  content_type: conversion copy  
  evidence: text explains the desired next action  
  confidence: observed

- item: CTA button group  
  content_type: interactive action controls  
  evidence: button-like elements are visible  
  confidence: observed

### 3. Repeated Component Candidates

- component_candidate: CTA button  
  repeated_parts: button surface, label, optional icon  
  evidence: one or more buttons share a similar visual treatment  
  confidence: likely

### 4. Visual Core

- item: CTA message group  
  evidence: the section is centered around a conversion message and action  
  confidence: observed

### 5. Decoration Layers

- item: background image or abstract pattern  
  decorative_function: reinforce mood and visual contrast  
  evidence: background visual does not appear to carry independent text content  
  confidence: likely

### 6. Overlay / Connector Candidates

- item: background decoration behind content  
  relationship: layered behind CTA content  
  evidence: visual layer sits under or around the text/button group  
  implementation_status: unknown  
  confidence: likely

### 7. Responsive Risks

- risk: background image may reduce text contrast on mobile  
  reason: cropped background can sit behind text differently at narrow widths  
  confidence: likely

- risk: CTA buttons may wrap awkwardly  
  reason: two buttons may not fit side by side on mobile  
  confidence: likely

### 8. Unknowns

- unknown: whether background image carries meaningful information  
  why_it_matters: affects accessibility and content modeling  
  blocking: no

- unknown: required CTA priority  
  why_it_matters: affects later responsive button order and styling  
  blocking: no

### 9. Implementation Assumptions Not Allowed Yet

- assumption: use a background image on the container  
  reason: implementation choice belongs to `/architectures`

- assumption: use absolute decorative shapes  
  reason: architecture choice belongs to `/architectures`

Allowed next step:
- `/architectures`
