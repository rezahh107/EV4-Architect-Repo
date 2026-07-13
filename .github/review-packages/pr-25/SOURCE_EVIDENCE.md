# PR #25 Source Evidence

Status: review-package evidence only

Authority effect: none

This file records immutable source identities for independent review. It does not replace or override `STATUS.md`, `AGENTS.md`, repository contracts, schemas, validators, manifests, active overrides, or the target governance standard.

## Target standard

```yaml
source_title: AI Authority Deterministic Governance — Source of Truth
source_version: 1.0.2
source_type: user_provided_immutable_attachment
source_locator: conversation_attachment/AI_AUTHORITY_DETERMINISTIC_GOVERNANCE_SSOT_v1.0.2.fa(1).md
sha256: ba74929aa39a2b375b058b33783d4f5a0abf70e27ffde4297a58750fff7fd320
repository_copy: intentionally_absent
reason_repository_copy_absent: avoid creating a competing repository authority
independent_review_requirement: the exact attachment matching this SHA-256 must accompany the independent review request
```

The repository adoption policy references this target standard by title and version. Implementation claims remain bounded to repository evidence; the attachment itself is not proof of enforcement.

## Frozen plan

```yaml
plan_id: GOV-ADOPTION-EV4-ARCHITECT-REPO-C9109F9-V1
plan_version: 1
increment_id: ARCH-GOV-CORE-001
source_type: immutable_review_package_attachment
source_commit_sha: b8b32fd3c662280376cf9d784f34aa41ef18bd30
source_path: .github/review-packages/pr-25/GOV-ADOPTION-EV4-ARCHITECT-REPO-C9109F9-V1.plan.md
sha256: 1fd509a4fbba58c2811eba4f777dc578ec7efa701c764f7cd87ae9788aec1e0e
authority_effect: none
```

The plan attachment is an immutable serialization of the previously approved frozen plan. It is evidence for review identity and authorized scope, not a new mutable status authority.

## Verification procedure

Independent review must:

1. obtain the exact target-standard attachment identified above;
2. verify its SHA-256;
3. fetch the plan attachment from the immutable commit and path above;
4. verify its SHA-256;
5. bind review to the final PR head rather than to a synthetic merge commit;
6. treat any later head change as invalidating the review package.
