# EV4-PCVP v1 dormant Architect producer

This work unit prepares the canonical Architect Producer Gate exporter to add an
optional `continuation_assurance` carrier in a later activation change.

## Locked behavior

- Decision Kernel remains the canonical Policy, profile, and schema owner.
- The compact Model Policy, Architect profile, and four carrier schemas are
  non-authoritative byte copies pinned to immutable Decision Kernel commit
  `069a50fa243b01fa578a7c1bcb8864d9e796d34b`.
- The producer derives only from Runtime-owned facts already available to the
  existing Project Gate exporter. Project Gate is the lossless boundary reader;
  Constructability Engineer is the next semantic consumer.
- A continued effect uses `NOT_REQUIRED` only because the existing Runtime has
  already authorized that exact handoff; PCVP creates no additional authority.
- Downstream constructability, Builder execution, Responsive completion, and
  production readiness remain explicitly unverified.
- The active Architect Producer Gate Export schema remains byte-identical to its
  current authority pin. The tolerant Project Gate boundary can accept the
  optional carrier, but adding the field to this producer schema belongs to the
  separate activation change.
- The vendored PCVP policy, profile, lock, and schemas remain dormant resources;
  they are not declared as active Runtime data authority before activation.

`PRODUCER_EMISSION_ENABLED` is hard-coded to `False`, the lock forbids caller
override, and no environment variable or public API can enable emission.
Changing that state belongs to a separate activation PR after all required
consumers, producer checks, boundary checks, and independent review are ready.

Rollout status remains `not_yet_adopted`; activation effect remains `NONE`.
