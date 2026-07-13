#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "planning/ai-governance-coverage.schema.json"
COVERAGE = ROOT / "planning/AI_GOVERNANCE_COVERAGE.yml"
VALID = ROOT / "fixtures/ai-governance/valid/cases.json"
INVALID = ROOT / "fixtures/ai-governance/invalid/cases.json"
WORKFLOWS = ROOT / ".github/workflows"

EXPECTED = {
    "AIGOV-START-001": ("Critical", "per_session", "validator_backed"),
    "AIGOV-EVIDENCE-001": ("Critical", "per_artifact", "ci_enforced"),
    "AIGOV-SECURITY-PROFILE-001": ("High", "cross_turn", "validator_backed"),
    "AIGOV-HUMAN-001": ("High", "per_artifact", "validator_backed"),
    "AIGOV-COACH-001": ("High", "per_artifact", "validator_backed"),
}
LADDER = ["prose_only", "schema_backed", "validator_backed", "fixture_tested", "advisory_ci_observed", "ci_enforced", "sequence_ci_enforced", "runtime_monitor_enforced", "os_harness_enforced", "downstream_contract_enforced"]
FACTUAL = {"REPOSITORY_CONFIRMED", "TOOL_CONFIRMED", "SOURCE_CONFIRMED", "TEST_CONFIRMED", "CI_CONFIRMED", "RUNTIME_CONFIRMED", "PUBLICATION_RECEIPT_CONFIRMED", "PERFORMANCE_RECEIPT_CONFIRMED"}
STATE_FOR_SOURCE = {"repository":"REPOSITORY_CONFIRMED", "tool":"TOOL_CONFIRMED", "source":"SOURCE_CONFIRMED", "test":"TEST_CONFIRMED", "ci":"CI_CONFIRMED", "runtime":"RUNTIME_CONFIRMED", "publication_receipt":"PUBLICATION_RECEIPT_CONFIRMED", "performance_receipt":"PERFORMANCE_RECEIPT_CONFIRMED", "ai_review_signal":"AI_REVIEW_SIGNAL", "coach_critique":"AI_REVIEW_SIGNAL", "ai_technical_decision":"AI_TECHNICAL_DECISION", "user_stated_input":"USER_STATED_INPUT", "assumption":"ASSUMED", "unknown":"UNKNOWN"}
MIN_CONTROLS = {"immutable_action_pins", "minimum_explicit_permissions", "exact_head_checkout_when_repository_is_checked_out", "persist_credentials_false", "fail_closed_head_identity", "no_pull_request_secret_exposure"}
HUMAN_INVARIANT = "Human technical approval and owner acknowledgement must not be treated, accepted, or used as substitutes for repository evidence."
MERGE_INVARIANT = "The user may perform the administrative Merge action after a valid technical recommendation; that action is not technical approval and does not prove correctness."

@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str
    message: str

def j(path: Path) -> Any:
    with path.open(encoding="utf-8") as f: return json.load(f)

def y(path: Path) -> Any:
    with path.open(encoding="utf-8") as f: return yaml.safe_load(f)

read_json = j
read_yaml = y

def ep(error: Any) -> str:
    out = "$"
    for part in error.absolute_path: out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out

def artifact_schema(schema: dict[str, Any], kind: str) -> dict[str, Any]:
    names = {"startup_session":"startup_session", "evidence_claim":"evidence_claim", "security_profile_fixture":"security_profile_fixture", "approval_contract":"approval_contract", "coach_critique":"coach_critique"}
    if kind not in names: raise KeyError(f"unknown fixture_type: {kind}")
    return {"$schema": schema["$schema"], "$ref": f"#/$defs/{names[kind]}", "$defs": schema["$defs"]}

def validate_startup_session(p: dict[str, Any], path: str = "$") -> list[Diagnostic]:
    required = {"README.md", "STATUS.md", "docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md", "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md"}
    out = []
    if not required.issubset(set(p.get("authority_files_inspected") or [])): out.append(Diagnostic("AIGOV-START-001_MISSING_AUTHORITY_EVIDENCE", path, "startup evidence must include the required repository authorities"))
    if not p.get("authorized_work") or p.get("dependencies_checked") is not True: out.append(Diagnostic("AIGOV-START-001_INCOMPLETE_STARTUP_GATE", path, "authorized work and dependency verification are required"))
    return out

def validate_evidence_claim(p: dict[str, Any], path: str = "$") -> list[Diagnostic]:
    out, state, source = [], p.get("evidence_state"), p.get("source_type")
    if p.get("unknown_input") is True and state not in {"UNKNOWN", "BLOCKED_INSUFFICIENT_EVIDENCE"}: out.append(Diagnostic("AIGOV-EVIDENCE-001_UNKNOWN_AS_FACT", path, "unknown input must remain unknown"))
    if source in {"ai_review_signal", "coach_critique"} and state in FACTUAL: out.append(Diagnostic("AIGOV-EVIDENCE-001_AI_SIGNAL_AS_FACT", path, "AI critique cannot be factual proof"))
    if p.get("self_asserted_outcome") is True and source in {"ai_review_signal", "coach_critique", "ai_technical_decision", "user_stated_input", "assumption", "unknown"}: out.append(Diagnostic("AIGOV-EVIDENCE-001_SELF_ASSERTED_OUTCOME", path, "outcomes require external evidence"))
    expected = STATE_FOR_SOURCE.get(source)
    if expected and state not in {expected, "BLOCKED_INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE"}: out.append(Diagnostic("AIGOV-EVIDENCE-001_SOURCE_STATE_MISMATCH", path, f"{source!r} is incompatible with {state!r}"))
    if state in FACTUAL and not p.get("source_reference"): out.append(Diagnostic("AIGOV-EVIDENCE-001_MISSING_SOURCE_REFERENCE", path, "factual states require a source reference"))
    return out

def validate_security_profile(p: dict[str, Any], path: str = "$") -> list[Diagnostic]:
    if p.get("repository_visibility") == "public" and not p.get("active_profile"): return [Diagnostic("AIGOV-SECURITY-PROFILE-001_MISSING_PROFILE", path, "public repository requires an active profile")]
    out = []
    if p.get("active_profile") == "personal_public_repository_minimum":
        if not MIN_CONTROLS.issubset(set(p.get("minimum_controls") or [])): out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_MINIMUM_CONTROL_MISSING", path, "minimum control missing"))
        if p.get("enterprise_controls_status") != "intentionally_out_of_scope": out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_ENTERPRISE_SCOPE_AMBIGUOUS", path, "enterprise scope must be explicit"))
    return out

def validate_approval_contract(p: dict[str, Any], path: str = "$") -> list[Diagnostic]:
    bad = p.get("human_technical_approval_required") is True or p.get("owner_acknowledgement_used_as_evidence") is True or p.get("user_merge_action_role") != "administrative_action"
    return [Diagnostic("AIGOV-HUMAN-001_APPROVAL_AS_EVIDENCE", path, "human approval cannot substitute for evidence")] if bad else []

def validate_coach_critique(p: dict[str, Any], path: str = "$") -> list[Diagnostic]:
    bad = p.get("evidence_state") != "AI_REVIEW_SIGNAL" or p.get("claims_technical_truth") is True or p.get("claims_real_world_outcome") is True
    return [Diagnostic("AIGOV-COACH-001_CRITIQUE_AS_FACT", path, "coach critique must remain an AI_REVIEW_SIGNAL")] if bad else []

FIXTURE_VALIDATORS = {"startup_session":validate_startup_session, "evidence_claim":validate_evidence_claim, "security_profile_fixture":validate_security_profile, "approval_contract":validate_approval_contract, "coach_critique":validate_coach_critique}

def carrier_path(value: str | None) -> str | None:
    if value is None: return None
    return value.split(" / ",1)[0].split("::",1)[0].split("#",1)[0]

def max_status(c: dict[str, Any]) -> str:
    if c.get("downstream_contract"): return "downstream_contract_enforced"
    if c.get("sequence_test"): return "sequence_ci_enforced"
    if c.get("CI_step"): return "ci_enforced"
    if c.get("valid_fixture") and c.get("invalid_fixture"): return "fixture_tested"
    if c.get("validator_rule"): return "validator_backed"
    if c.get("schema_carrier"): return "schema_backed"
    return "prose_only"

def validate_coverage_semantics(cov: dict[str, Any]) -> list[Diagnostic]:
    out, rules = [], cov.get("rules") or []
    by_id = {r.get("rule_id"):r for r in rules if isinstance(r, dict)}
    if set(by_id) != set(EXPECTED): out.append(Diagnostic("AIGOV-COVERAGE-001_RULE_SET_MISMATCH", "$.rules", "required rule set mismatch"))
    for rid, (risk, scope, minimum) in EXPECTED.items():
        r = by_id.get(rid)
        if not r: continue
        path = f"$.rules[{rid}]"
        for field, expected in (("risk",risk), ("session_scope",scope), ("minimum_required_status",minimum)):
            if r.get(field) != expected: out.append(Diagnostic("AIGOV-COVERAGE-001_RULE_IDENTITY_MISMATCH", path, f"{field} must be {expected!r}"))
        status = (r.get("status") or {}).get("enforcement_status")
        if status in LADDER and LADDER.index(status) < LADDER.index(minimum): out.append(Diagnostic("AIGOV-COVERAGE-001_BELOW_MINIMUM", path, f"{status} below {minimum}"))
        carriers = r.get("carriers") or {}
        proven = max_status(carriers)
        if status in LADDER and LADDER.index(status) > LADDER.index(proven): out.append(Diagnostic("AIGOV-COVERAGE-001_OVERCLAIMED_STATUS", path, f"{status} exceeds {proven}"))
        for name, value in carriers.items():
            cp = carrier_path(value)
            if cp and not (ROOT/cp).exists(): out.append(Diagnostic("AIGOV-COVERAGE-001_MISSING_CARRIER", f"{path}.carriers.{name}", f"missing {cp}"))
    profile = cov.get("security_profile") or {}
    out += validate_security_profile({"repository_visibility":profile.get("repository_visibility"), "active_profile":profile.get("profile_id"), "minimum_controls":profile.get("minimum_controls") or [], "enterprise_controls_status":(profile.get("enterprise_controls") or {}).get("status")}, "$.security_profile")
    return out

def validate_authority_sources() -> list[Diagnostic]:
    agents_path, policy_path = ROOT/"AGENTS.md", ROOT/"docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md"
    agents, policy = agents_path.read_text(encoding="utf-8"), policy_path.read_text(encoding="utf-8")
    order = ["`README.md`", "`STATUS.md`", "`docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md`", "`02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md`"]
    pos, out = [agents.find(x) for x in order], []
    if any(x < 0 for x in pos) or pos != sorted(pos): out.append(Diagnostic("AIGOV-START-001_AUTHORITY_ORDER_INVALID", "AGENTS.md#Read First", "authority startup order invalid"))
    for path, text in ((agents_path,agents),(policy_path,policy)):
        if HUMAN_INVARIANT not in text: out.append(Diagnostic("AIGOV-HUMAN-001_INVARIANT_MISSING", str(path.relative_to(ROOT)), "human evidence invariant missing"))
    if MERGE_INVARIANT not in policy: out.append(Diagnostic("AIGOV-HUMAN-001_MERGE_BOUNDARY_MISSING", str(policy_path.relative_to(ROOT)), "administrative Merge boundary missing"))
    return out

def is_pr_workflow(text: str) -> bool: return bool(re.search(r"(?m)^\s{0,2}pull_request(?:_target)?\s*:", text))

def validate_workflow_text(path: str, text: str) -> list[Diagnostic]:
    if not is_pr_workflow(text): return []
    out = []
    if not re.search(r"(?ms)^permissions:\s*\n(?:^[ \t].*\n)*?^\s{2}contents:\s*read\s*$", text): out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_PERMISSIONS_NOT_MINIMAL", path, "contents: read required"))
    for m in re.finditer(r"(?m)^\s*-?\s*uses:\s*([^\s#]+)", text):
        target = m.group(1)
        if not target.startswith(("./","docker://")) and not re.search(r"@[0-9a-f]{40}$", target): out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_MUTABLE_ACTION_REF", path, f"mutable ref: {target}"))
    if "actions/checkout@" in text:
        if "ref: ${{ github.event.pull_request.head.sha }}" not in text: out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_NOT_EXACT_HEAD", path, "exact PR head required"))
        if not re.search(r"(?m)^\s+persist-credentials:\s*false\s*$", text): out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_CREDENTIAL_PERSISTENCE", path, "persist-credentials: false required"))
        if 'test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"' not in text: out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_HEAD_ASSERTION_MISSING", path, "exact-head assertion required"))
    if re.search(r"\$\{\{\s*secrets\.", text) or re.search(r"(?m)^\s*secrets:\s*inherit\s*$", text): out.append(Diagnostic("AIGOV-SECURITY-PROFILE-001_PR_SECRET_EXPOSURE", path, "PR secret exposure forbidden"))
    return out

def validate_workflows() -> list[Diagnostic]:
    if not WORKFLOWS.exists(): return [Diagnostic("AIGOV-SECURITY-PROFILE-001_WORKFLOW_DIRECTORY_MISSING", str(WORKFLOWS.relative_to(ROOT)), "workflow directory missing")]
    out = []
    for path in sorted(WORKFLOWS.glob("*.y*ml")): out += validate_workflow_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"))
    return out

def validate_fixture_case(schema: dict[str, Any], case: dict[str, Any], index: int) -> list[Diagnostic]:
    kind, payload, path = case.get("fixture_type"), case.get("payload"), f"$.cases[{index}]"
    try: validator = Draft202012Validator(artifact_schema(schema, kind))
    except KeyError as exc: return [Diagnostic("AIGOV-FIXTURE-001_UNKNOWN_TYPE", path, str(exc))]
    out = [Diagnostic("AIGOV-FIXTURE-001_SCHEMA_INVALID", f"{path}{ep(e)[1:]}", e.message) for e in sorted(validator.iter_errors(payload), key=lambda x:(ep(x),x.message))]
    return out if out else FIXTURE_VALIDATORS[kind](payload, path)

def validate_fixtures(schema: dict[str, Any]) -> list[Diagnostic]:
    out = []
    for i, case in enumerate(j(VALID).get("cases", [])):
        got = validate_fixture_case(schema, case, i)
        if got: out.append(Diagnostic("AIGOV-FIXTURE-001_VALID_CASE_REJECTED", f"{VALID.relative_to(ROOT)}::{case.get('case_id')}", "; ".join(x.code for x in got)))
    for i, case in enumerate(j(INVALID).get("cases", [])):
        codes = {x.code for x in validate_fixture_case(schema, case, i)}
        if case.get("expected_diagnostic") not in codes: out.append(Diagnostic("AIGOV-FIXTURE-001_INVALID_CASE_NOT_REJECTED", f"{INVALID.relative_to(ROOT)}::{case.get('case_id')}", f"got {sorted(codes)}"))
    return out

def validate_repository() -> dict[str, Any]:
    schema, cov = j(SCHEMA), y(COVERAGE)
    Draft202012Validator.check_schema(schema)
    out = [Diagnostic("AIGOV-COVERAGE-001_SCHEMA_INVALID", ep(e), e.message) for e in sorted(Draft202012Validator(schema).iter_errors(cov), key=lambda x:(ep(x),x.message))]
    if not out: out += validate_coverage_semantics(cov)
    out += validate_authority_sources() + validate_workflows() + validate_fixtures(schema)
    return {"status":"passed" if not out else "failed", "diagnostics":[asdict(x) for x in out], "validated_rules":sorted(EXPECTED), "workflow_count":len(list(WORKFLOWS.glob("*.y*ml"))) if WORKFLOWS.exists() else 0}

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("text","json"), default="text")
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = validate_repository()
    if args.format == "json": print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["status"] == "passed":
        print(f"ok: {COVERAGE.relative_to(ROOT)}")
        print(f"validated_rules: {len(result['validated_rules'])}")
        print(f"workflows_inspected: {result['workflow_count']}")
        print("fixture_failures: 0")
    else:
        for x in result["diagnostics"]: print(f"{x['code']}: {x['path']}: {x['message']}", file=sys.stderr)
    return 0 if result["status"] == "passed" else 1

if __name__ == "__main__": raise SystemExit(main())
