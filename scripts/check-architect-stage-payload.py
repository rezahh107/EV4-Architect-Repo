#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from jsonschema import Draft202012Validator

Severity = Literal["error","warning","info","insufficient_evidence"]
ORDER = {"error":0,"insufficient_evidence":1,"warning":2,"info":3}
FORBIDDEN = {
  "constructability_proven":"A-R11","ce_approved":"A-R11","builder_ready":"A-R02",
  "builder_executable":"A-R02","builder_executable_allowed":"A-R02","builder_runtime_intake_authorized":"A-R02",
  "responsive_complete":"A-R10","production_ready":"A-R03","production_ready_allowed":"A-R03",
  "live_elementor_validated":"A-R11","real_export_json_validated":"A-R11","exact_pixel_match_validated":"A-R11"
}
REQUIRED_FORBIDDEN_WORK = {"no_invent_geometry","no_invent_assets","no_invent_breakpoints","no_infer_dynamic_data","no_claim_builder_ready","no_claim_production_ready"}

@dataclass(frozen=True)
class Diagnostic:
    code: str; severity: Severity; message: str; path: str = "$"; rule_id: str|None = None; details: dict[str,Any] = field(default_factory=dict)
    def key(self): return (self.path, ORDER[self.severity], self.rule_id or "", self.code, self.message)
    def to_dict(self):
        d={"code":self.code,"severity":self.severity,"message":self.message,"path":self.path}
        if self.rule_id: d["rule_id"]=self.rule_id
        if self.details: d["details"]=self.details
        return d

def D(code,severity,msg,path="$",rule_id=None,**details): return Diagnostic(code,severity,msg,path,rule_id,details)
def jp(parts):
    out="$"
    for p in parts: out += f"[{p}]" if isinstance(p,int) else f".{p}"
    return out

class ArchitectPayloadValidator:
    def __init__(self, repo_root: Path):
        self.repo_root=Path(repo_root)
        with (self.repo_root/"schemas/ev4-architect-stage-payload.v1.schema.json").open(encoding="utf-8") as f: self.schema=json.load(f)
        Draft202012Validator.check_schema(self.schema)
        self.schema_validator=Draft202012Validator(self.schema)
    def validate_file(self,path:Path):
        try:
            with Path(path).open(encoding="utf-8") as f: value=json.load(f)
        except json.JSONDecodeError as e: return self._result(None,[D("MALFORMED_JSON","error","File is not valid JSON.","$",line=e.lineno,column=e.colno)])
        except OSError as e: return self._result(None,[D("FILE_READ_ERROR","error","File could not be read.","$",error_type=type(e).__name__)])
        return self.validate_value(value)
    def validate_value(self,value:Any):
        if not isinstance(value,dict): return self._result(value,[D("INPUT_NOT_OBJECT","error","Architect Stage Payload must be a JSON object.","$",observed_type=type(value).__name__)])
        diags=[D("SCHEMA_VALIDATION_FAILED","error",e.message,jp(list(e.path))) for e in sorted(self.schema_validator.iter_errors(value), key=lambda e:(jp(list(e.path)),e.message))]
        diags += self._semantic(value)
        return self._result(value,diags)
    def _semantic(self,v:dict):
        out=[]; evidence={e.get("evidence_id"):e for e in v.get("evidence_register",[]) if isinstance(e,dict)}
        nodes={n.get("node_id") for n in v.get("approved_structure_model",{}).get("structure_nodes",[]) if isinstance(n,dict)}
        out += self._forbidden(v)
        dec=v.get("architecture_identity",{}).get("decision_source",{}) if isinstance(v.get("architecture_identity"),dict) else {}
        for field,path in [("evidence_refs","$.architecture_identity.decision_source.evidence_refs"),("locked_decision_refs","$.architecture_identity.decision_source.locked_decision_refs"),("source_evidence_refs","$.architecture_identity.decision_source.source_evidence_refs")]:
            refs=dec.get(field,[])
            if not refs: out.append(D("A_R01_MISSING_LOCK_EVIDENCE","error","Locked architecture requires explicit evidence references.",path,"A-R01"))
            for r in refs:
                if r not in evidence: out.append(D("A_R01_UNKNOWN_LOCK_EVIDENCE_REF","error","Locked architecture references unknown evidence.",path,"A-R01",missing_ref=r))
        if dec.get("approved_structure_ref") and dec.get("approved_structure_ref") not in nodes:
            out.append(D("A_R01_APPROVED_STRUCTURE_REF_NOT_FOUND","error","Approved structure reference must point to a structure node.","$.architecture_identity.decision_source.approved_structure_ref","A-R01"))
        structure=v.get("approved_structure_model",{}).get("structure_nodes",[]) if isinstance(v.get("approved_structure_model"),dict) else []
        if not structure: out.append(D("A_R01_STRUCTURE_MODEL_MISSING","error","Locked architecture requires an approved structure model.","$.approved_structure_model.structure_nodes","A-R01"))
        for i,n in enumerate(structure):
            if not isinstance(n,dict): continue
            if not n.get("evidence_refs"): out.append(D("A_R01_STRUCTURE_NODE_EVIDENCE_MISSING","error","Every structure node requires source evidence references.",f"$.approved_structure_model.structure_nodes[{i}].evidence_refs","A-R01"))
            for r in n.get("evidence_refs",[]):
                if r not in evidence: out.append(D("A_R01_UNKNOWN_STRUCTURE_EVIDENCE_REF","error","Structure node references unknown evidence.",f"$.approved_structure_model.structure_nodes[{i}].evidence_refs","A-R01",missing_ref=r))
            if n.get("node_kind")=="wrapper" and "wrapper_justification" not in n: out.append(D("A_R07_WRAPPER_WITHOUT_JUSTIFICATION","error","Wrapper nodes require explicit structural justification.",f"$.approved_structure_model.structure_nodes[{i}]","A-R07"))
        missing=sorted(REQUIRED_FORBIDDEN_WORK-set(v.get("forbidden_work",[])))
        if missing: out.append(D("A_R04_FORBIDDEN_WORK_INCOMPLETE","error","Architect payload must explicitly forbid invented downstream facts.","$.forbidden_work","A-R04",missing=missing))
        if v.get("payload_status")=="insufficient_evidence" and not v.get("unresolved_evidence"):
            out.append(D("A_R05_UNRESOLVED_EVIDENCE_MISSING","error","Insufficient payloads must structurally state missing evidence.","$.unresolved_evidence","A-R05"))
        css=v.get("architect_intent",{}).get("scoped_css_intent",{}) if isinstance(v.get("architect_intent"),dict) else {}
        if css.get("global_css_allowed") is not False: out.append(D("A_R08_GLOBAL_CSS_NOT_ALLOWED","error","Scoped CSS intent must not allow global CSS.","$.architect_intent.scoped_css_intent.global_css_allowed","A-R08"))
        if css.get("meaningful_content_created_by_css_allowed") is not False: out.append(D("A_R08_CSS_CONTENT_CREATION_NOT_ALLOWED","error","CSS must not create meaningful content.","$.architect_intent.scoped_css_intent.meaningful_content_created_by_css_allowed","A-R08"))
        if "global" in css.get("allowed_selector_scopes",[]): out.append(D("A_R08_GLOBAL_SCOPE_NOT_ALLOWED","error","Allowed selector scopes must remain local.","$.architect_intent.scoped_css_intent.allowed_selector_scopes","A-R08"))
        dyn=v.get("architect_intent",{}).get("dynamic_loop_intent",{}) if isinstance(v.get("architect_intent"),dict) else {}
        if dyn.get("status")=="approved":
            ok=any((evidence.get(r) or {}).get("fact_class")=="project_specific_behavior" and (evidence.get(r) or {}).get("state") in {"observed","validated","resolved"} for r in dyn.get("evidence_refs",[]))
            if not ok: out.append(D("A_R09_DYNAMIC_LOOP_UNSUPPORTED","error","Dynamic Loop approval requires project-specific observed or validated data-source evidence.","$.architect_intent.dynamic_loop_intent","A-R09"))
        if not v.get("architect_intent",{}).get("responsive_risk_seeds",[]) if isinstance(v.get("architect_intent"),dict) else True:
            out.append(D("A_R10_RESPONSIVE_UNCERTAINTY_NOT_VISIBLE","error","Responsive uncertainty must remain visible.","$.architect_intent.responsive_risk_seeds","A-R10"))
        return out
    def _forbidden(self,value,path="$"):
        out=[]
        if isinstance(value,dict):
            for k,c in value.items():
                p=f"{path}.{k}"
                if k in FORBIDDEN and c is not False: out.append(D("FORBIDDEN_DOWNSTREAM_CLAIM","error","Architect payload must not assert positive downstream readiness or validation claims.",p,FORBIDDEN[k],claim=k,observed_value=c))
                out+=self._forbidden(c,p)
        elif isinstance(value,list):
            for i,c in enumerate(value): out+=self._forbidden(c,f"{path}[{i}]")
        return out
    def _result(self,value,diags):
        ordered=sorted(diags,key=lambda d:d.key())
        status="invalid" if any(d.severity=="error" for d in ordered) else "insufficient_evidence" if isinstance(value,dict) and value.get("payload_status")=="insufficient_evidence" else "valid"
        return {"status":status,"diagnostics":[d.to_dict() for d in ordered]}


def _path_tokens(path: str):
    return [int(part) if part.isdigit() else part for part in path.split('.') if part]

def _set_path(value: dict[str, Any], path: str, new_value: Any) -> None:
    cur: Any = value
    parts = _path_tokens(path)
    for part in parts[:-1]:
        cur = cur[part]
    cur[parts[-1]] = new_value

def _delete_path(value: dict[str, Any], path: str) -> None:
    cur: Any = value
    parts = _path_tokens(path)
    for part in parts[:-1]:
        cur = cur[part]
    del cur[parts[-1]]

def _load_case_reports(repo_root: Path, cases_file: Path, expect: str):
    import copy
    data = json.loads(cases_file.read_text(encoding='utf-8'))
    base_path = (cases_file.parent / data['base_fixture']).resolve()
    base = json.loads(base_path.read_text(encoding='utf-8'))
    validator = ArchitectPayloadValidator(repo_root)
    reports = []
    failures = 0
    for case in data['cases']:
        payload = copy.deepcopy(base)
        for mutation in case.get('mutations', []):
            if mutation['op'] == 'set':
                _set_path(payload, mutation['path'], mutation['value'])
            elif mutation['op'] == 'delete':
                _delete_path(payload, mutation['path'])
            else:
                raise ValueError(f"Unsupported mutation op: {mutation['op']}")
        result = validator.validate_value(payload)
        ok = result['status'] == expect
        failures += 0 if ok else 1
        reports.append({
            'fixture': f"{cases_file.relative_to(repo_root)}#{case['case_id']}",
            'expected': expect,
            'actual': result['status'],
            'ok': ok,
            'diagnostic_codes': [item['code'] for item in result['diagnostics']],
        })
    return failures, reports

def iter_expected(root:Path):
    for d,expect in [("valid","valid"),("invalid","invalid"),("insufficient-evidence","insufficient_evidence")]:
        for p in sorted((root/"fixtures/architect-stage-payload"/d).glob("*.json")): yield p,expect

def validate_fixture_suite(repo_root:Path):
    v=ArchitectPayloadValidator(repo_root); reports=[]; failures=0
    for path,expect in iter_expected(repo_root):
        if path.name == "cases.v1.json":
            case_failures, case_reports = _load_case_reports(repo_root, path, expect)
            failures += case_failures
            reports.extend(case_reports)
            continue
        r=v.validate_file(path); ok=r["status"]==expect; failures += 0 if ok else 1
        reports.append({"fixture":str(path.relative_to(repo_root)),"expected":expect,"actual":r["status"],"ok":ok,"diagnostic_codes":[d["code"] for d in r["diagnostics"]]})
    return failures,reports

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",default=Path.cwd()); ap.add_argument("--file",type=Path); ap.add_argument("--expect",choices=["valid","invalid","insufficient_evidence"]); ap.add_argument("--format",choices=["text","json"],default="text"); args=ap.parse_args(argv)
    root=Path(args.repo_root).resolve(); v=ArchitectPayloadValidator(root)
    if args.file:
        r=v.validate_file(args.file if args.file.is_absolute() else root/args.file)
        print(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(",",":")) if args.format=="json" else f"status: {r['status']}")
        if args.expect: return 0 if r["status"]==args.expect else 1
        return 0 if r["status"]=="valid" else 2 if r["status"]=="insufficient_evidence" else 1
    failures,reports=validate_fixture_suite(root)
    if args.format=="json": print(json.dumps({"failures":failures,"reports":reports},ensure_ascii=False,sort_keys=True,separators=(",",":")))
    else:
        for r in reports: print(f"{'ok' if r['ok'] else 'FAIL'}: {r['fixture']} expected={r['expected']} actual={r['actual']} codes={','.join(r['diagnostic_codes'])}")
        print(f"fixture_failures: {failures}")
    return 0 if failures==0 else 1
if __name__=="__main__": raise SystemExit(main())
