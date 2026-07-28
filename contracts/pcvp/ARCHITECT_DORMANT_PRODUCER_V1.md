# EV4-PCVP v1 Architect producer activation contract

Historical filename note: this path was introduced for the dormant preparation
phase in PR #43. Its current contents supersede the dormant-only behavior after
the bounded activation authorized by Decision Kernel activation merge
`ad0e7235929d7f6d847724f6b4d1a6a3c57453db`. The filename is retained to avoid
breaking repository references; the dormant semantics below are no longer
current authority.

## Current bounded behavior

- Decision Kernel remains the canonical Policy, profile, schema, and staged
  activation authority owner.
- The compact Model Policy, Architect profile, and four carrier schemas remain
  non-authoritative byte copies pinned to immutable Decision Kernel bundle
  snapshot `069a50fa243b01fa578a7c1bcb8864d9e796d34b`.
- Official activation authority is separately pinned to exact Decision Kernel
  merge `ad0e7235929d7f6d847724f6b4d1a6a3c57453db`, activation ID
  `EV4-PCVP-ACT-ARCH-PG-CE-20260728-R1`.
- The only enabled activation edge is
  `ARCHITECT_TO_PROJECT_GATE_TO_CE`.
- `CE_TO_BUILDER`, `BUILDER_TO_RESPONSIVE`, and `RESPONSIVE_TO_FINAL` remain
  disabled, and `full_rollout_authorized` remains `false`.
- The Architect Runtime may attach exactly one optional
  `continuation_assurance` carrier to the canonical Producer Gate export only
  after consuming the existing Runtime-issued one-shot Payload capability and
  revalidating that exact Runtime-issued Payload.
- Carrier construction remains private to the Runtime-owned terminal export
  transaction. Caller-supplied `continuation_assurance`, environment-variable
  activation, public enablement parameters, and test-only activation switches
  remain forbidden.
- A continued effect uses `NOT_REQUIRED` only when the existing Architect
  Runtime has already authorized that exact handoff. PCVP creates no new
  continuation authority and cannot upgrade a blocked handoff.
- Project Gate remains the lossless boundary reader. Constructability Engineer
  remains the next semantic consumer.
- Downstream constructability conclusions, Builder execution, Responsive
  completion, production readiness, deployment status, and full-rollout status
  remain explicitly unverified or unauthorized unless their own authorities
  later prove them.
- The active Producer Gate Export schema permits the optional carrier while
  retaining `additionalProperties: false`; legacy exports without the carrier
  remain structurally valid.
- The Runtime Authority Manifest includes the PCVP producer and the exact
  Python/data authority closure actually loaded by the active Runtime.
- Dedicated validation preserves byte parity with the immutable bundle
  snapshot, validates the exact activation authority, exercises fail-closed
  semantic mutations, and validates the actual Runtime-emitted carrier against
  the exact current Project Gate and CE consumers.

## Fail-closed activation boundary

Emission is valid only while all of the following remain true:

1. the local producer lock matches the six pinned bundle resources;
2. the local activation record matches
   `ad0e7235929d7f6d847724f6b4d1a6a3c57453db` and enables only
   `ARCHITECT_TO_PROJECT_GATE_TO_CE`;
3. all three downstream activation edges remain disabled;
4. the Runtime-issued Payload is canonically valid before attachment;
5. the existing Runtime handoff decision is preserved rather than upgraded;
6. the emitted carrier passes structural, cross-record, and semantic PCVP
   validation.

Any mismatch fails closed. Safe disable or rollback requires a dedicated
repository change; it must not rewrite history, weaken validation, or silently
reactivate a downstream edge.

## Adoption and claim boundary

The immutable bundle snapshot itself remains `release_candidate` with
`bundle_adoption_status: not_yet_adopted`. That bundle metadata is not a claim
that this edge is dormant: the separate staged activation authority now permits
only the Architect → Project Gate → Constructability Engineer edge.

This contract does not claim full PCVP rollout, CE → Builder emission, Builder →
Responsive emission, Responsive → Final emission, production readiness,
deployment, or downstream correctness.
