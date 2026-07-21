#!/usr/bin/env python3
"""Validate intermediate Architect pipeline Stage Artifacts and receipts."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "ev4-architect-pipeline-stage-artifact@1.0.0"
RECEIPT_SCHEMA = "ev4-architect-stage-validation-receipt@1.0.0"
VALIDATOR_ID = "architect-pipeline-stage-boundary-validator"
VALIDATOR_VERSION = "1.0.0"
FAMILIES = [f"A{i:02d}" for i in range(1,9)]
ORDER = ["/decompose","/architectures","/score-evidence","/score-audit"]

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def diag(code, rule, stage, path, expected, observed, repair=None):
    d={"code":code,"rule_id":rule,"stage_id":stage,"path":path,"expected":expected,"observed":observed}
    if repair is not None: d["repair_target_stage"] = repair
    return d

def sort_diags(ds): return sorted(ds, key=lambda d:(d["stage_id"], d["path"], d["code"], d["rule_id"]))

class Validator:
    def __init__(self, root=ROOT):
        self.root=Path(root); self.schema=load_json(self.root/"schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json"); self.js=Draft202012Validator(self.schema)
    def validate_path(self, path):
        p=Path(path); data=load_json(p); h=sha(p); return self.validate(data, p, h, {"self_sha": h})
    def validate(self, a, path=None, digest=None, ctx=None):
        ds=[]; stage=a.get("stage_id") if isinstance(a,dict) else "unknown"
        if not isinstance(a,dict):
            return self.receipt({}, digest or "0"*64, "unknown", [diag("INPUT_NOT_OBJECT","ASB-R01","unknown","$","object",type(a).__name__)])
        for e in self.js.iter_errors(a):
            ds.append(diag("SCHEMA_VALIDATION_FAILED", self.rule_for(stage, list(e.path)), stage, "$"+"".join(f"/{x}" for x in e.path), e.message, "schema_violation", stage))
        if not ds:
            ds += self.semantic(a, ctx or {})
        return self.receipt(a, digest or hashlib.sha256(json.dumps(a,sort_keys=True,separators=(",",":")).encode()).hexdigest(), stage, ds)
    def rule_for(self, stage, path):
        if stage=="/decompose": return "ASB-R01"
        if stage=="/architectures" and "architecture_coverage_matrix" in path: return "ASB-R03"
        if stage=="/architectures": return "ASB-R04"
        if stage=="/score-evidence": return "ASB-R05"
        if stage=="/score-audit": return "ASB-R08"
        return "ASB-R07"
    def receipt(self,a,digest,stage,ds):
        status="valid" if not ds else "invalid"
        return {"receipt_schema":RECEIPT_SCHEMA,"receipt_id":f"asb-receipt-{a.get('artifact_id','unknown')}-{digest[:12]}","validator_id":VALIDATOR_ID,"validator_version":VALIDATOR_VERSION,"artifact_id":a.get("artifact_id","unknown"),"artifact_schema":a.get("artifact_schema",SCHEMA_ID),"artifact_sha256":digest,"stage_id":stage,"status":status,"diagnostics":sort_diags(ds)}
    def semantic(self,a,ctx):
        stage=a["stage_id"]; p=a["payload"]; ds=[]
        if stage=="/decompose":
            ids=[u["unknown_id"] for u in p["unknowns"]]
            for uid in sorted(set(x for x in ids if ids.count(x)>1)):
                ds.append(diag("ASB-DUPLICATE-UNKNOWN-ID","ASB-R02",stage,"$/payload/unknowns", "unique unknown_id", uid, stage))
            if p.get("allowed_next_stage") and p.get("gate_results") in {"pass","valid"} and ds:
                ds.append(diag("ASB-NEXT-STAGE-INVALID","ASB-R06",stage,"$/payload/allowed_next_stage","null until valid receipt","self-declared pass",stage))
        if stage=="/architectures":
            got={r["family_id"] for r in p["architecture_coverage_matrix"]}
            miss=[f for f in FAMILIES if f not in got]
            if miss: ds.append(diag("ASB-COVERAGE-MATRIX-INCOMPLETE","ASB-R03",stage,"$/payload/architecture_coverage_matrix","A01-A08", ",".join(miss), stage))
            s2=ctx.get("/decompose")
            ledger={r["unknown_id"]:r for r in p["unknown_propagation_ledger"]}
            if s2:
                for uid in [u["unknown_id"] for u in s2["payload"]["unknowns"]]:
                    if uid not in ledger: ds.append(diag("ASB-UNKNOWN-LEDGER-MISSING-UPSTREAM-ID","ASB-R04",stage,"$/payload/unknown_propagation_ledger",uid,"missing","/decompose"))
            for i,r in enumerate(p["unknown_propagation_ledger"]):
                if r["state"]=="resolved_with_evidence" and not r.get("resolving_evidence_refs"):
                    ds.append(diag("ASB-UNKNOWN-RESOLVED-WITHOUT-EVIDENCE","ASB-R04",stage,f"$/payload/unknown_propagation_ledger/{i}/resolving_evidence_refs","non-empty resolving evidence","missing",stage))
            known=set(ledger)
            for i,c in enumerate(p["active_candidates"]):
                for uid in c["depends_on_unknown_ids"]:
                    if uid not in known: ds.append(diag("ASB-CANDIDATE-UNTRACKED-UNKNOWN","ASB-R04",stage,f"$/payload/active_candidates/{i}/depends_on_unknown_ids",uid,"absent from ledger",stage))
        if stage=="/score-evidence":
            refs=[r for r in p["validated_upstream_artifact_refs"] if r["source_stage"]=="/architectures" and r["validation_status"]=="valid"]
            s3=ctx.get("/architectures")
            if not refs or not s3: ds.append(diag("ASB-UPSTREAM-VALIDATION-REQUIRED","ASB-R05",stage,"$/payload/validated_upstream_artifact_refs","valid /architectures artifact and receipt","missing", "/architectures"))
            if p.get("normalization_claim"): ds.append(diag("ASB-DOWNSTREAM-RECONSTRUCTION-FORBIDDEN","ASB-R05",stage,"$/payload/normalization_claim","no reconstruction/normalization of absent artifacts",p["normalization_claim"],"/architectures"))
            if s3:
                validc={c["candidate_id"] for c in s3["payload"]["active_candidates"]}
                stage3unknown={r["unknown_id"] for r in s3["payload"]["unknown_propagation_ledger"]}
                uncertain={u.get("unknown_id") for u in p["uncertainty_register"] if isinstance(u,dict)}
                for i,s in enumerate(p["candidate_scores"]):
                    if s["candidate_id"] not in validc: ds.append(diag("ASB-CANDIDATE-NOT-IN-VALIDATED-STAGE3","ASB-R07",stage,f"$/payload/candidate_scores/{i}/candidate_id","candidate from validated Stage 3",s["candidate_id"],"/architectures"))
                    if s["scores_audited"]: ds.append(diag("ASB-SCORE-EVIDENCE-CLAIMS-AUDITED","ASB-R08",stage,f"$/payload/candidate_scores/{i}/scores_audited","false before /score-audit","true",stage))
                    if s["final_total"] is not None and any(c["contract_critical"] and c["value"]=="?" for c in s["criteria"]): ds.append(diag("ASB-FINAL-TOTAL-WITH-UNKNOWN","ASB-R05",stage,f"$/payload/candidate_scores/{i}/final_total","null while contract-critical criteria are ?",str(s["final_total"]),stage))
                for uid in stage3unknown-uncertain: ds.append(diag("ASB-STAGE3-UNKNOWN-DISCARDED","ASB-R05",stage,"$/payload/uncertainty_register",uid,"missing",stage))
        if stage=="/score-audit":
            ref=p["validated_stage_4_artifact_ref"]
            if ref["source_stage"]!="/score-evidence" or ref["validation_status"]!="valid" or "/score-evidence" not in ctx:
                ds.append(diag("ASB-STAGE5-MISSING-VALID-STAGE4","ASB-R08",stage,"$/payload/validated_stage_4_artifact_ref","valid Stage 4 receipt lineage","missing or invalid","/score-evidence"))
            if p["overall_audit_status"]=="pass" and p["allowed_next_stage"]!="/recommend": ds.append(diag("ASB-STAGE5-PASS-NEXT-STAGE","ASB-R08",stage,"$/payload/allowed_next_stage","/recommend",str(p["allowed_next_stage"]),stage))
        # anchor binding
        anc=a.get("stage_anchor")
        if anc:
            if anc["source_artifact"]["artifact_id"]!=a["artifact_id"] or (path:=anc["source_artifact"].get("artifact_sha256")) != ctx.get("self_sha", path): ds.append(diag("ASB-ANCHOR-DIGEST-MISMATCH","ASB-R07",stage,"$/stage_anchor/source_artifact/artifact_sha256","exact artifact sha256","mismatch",stage))
            if anc["anchor_type"]=="NEXT STAGE ANCHOR" and anc["source_validation"]["status"]!="valid": ds.append(diag("ASB-ANCHOR-VALID-RECEIPT-REQUIRED","ASB-R06",stage,"$/stage_anchor/source_validation/status","valid","invalid",stage))
        return ds
    def validate_sequence(self, d):
        ctx={}; receipts=[]; all_ds=[]
        for st in ORDER:
            files=sorted(Path(d).glob(st.strip('/').replace('/','_')+"*.json"))
            if not files: continue
            p=files[0]; h=sha(p); a=load_json(p); r=self.validate(a,p,h,{**ctx,"self_sha":h})
            receipts.append(r); all_ds += r["diagnostics"]
            if r["status"]=="valid": ctx[st]=a
            else: break
        return {"status":"valid" if not all_ds else "invalid","diagnostics":sort_diags(all_ds),"receipts":receipts}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--artifact"); ap.add_argument("--write-receipt"); ap.add_argument("--sequence"); ap.add_argument("--fixtures",action="store_true"); ap.add_argument("--format",choices=["text","json"],default="text")
    ns=ap.parse_args(); v=Validator(ROOT); out=None
    if ns.artifact:
        out=v.validate_path(ns.artifact)
        if ns.write_receipt: Path(ns.write_receipt).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    elif ns.sequence: out=v.validate_sequence(ns.sequence)
    elif ns.fixtures:
        base=ROOT/"fixtures/architect-pipeline-stage-boundary"
        valid=v.validate_sequence(base/"valid/complete-sequence")
        checks=[valid]; bad=[]
        for d in sorted((base/"invalid").iterdir()):
            if d.is_dir():
                
                if (d/"stale.receipt.json").exists():
                    af=next(x for x in d.glob("*.json") if x.name != "stale.receipt.json")
                    actual=sha(af); recorded=load_json(d/"stale.receipt.json").get("artifact_sha256")
                    r={"status":"invalid" if actual != recorded else "valid", "diagnostics": [] if actual != recorded else [diag("ASB-RECEIPT-DIGEST-UNEXPECTED-MATCH","ASB-R07","fixture","$/stale.receipt.json/artifact_sha256","digest mismatch fixture",actual)]}
                else:
                    r=v.validate_sequence(d) if any((d/n).exists() for n in ["decompose.json","architectures.json","score-evidence.json","score-audit.json"]) else v.validate_path(next(d.glob("*.json")))
                checks.append(r)
                if r["status"]=="valid": bad.append(str(d.relative_to(ROOT)))
        out={"status":"valid" if valid["status"]=="valid" and not bad else "invalid","diagnostics":[] if not bad else [diag("ASB-FIXTURE-EXPECTED-INVALID-PASSED","ASB-R07","fixture","$/fixtures","invalid fixture failure", ",".join(bad))],"checked":len(checks)}
    else: ap.error("choose --artifact, --sequence, or --fixtures")
    print(json.dumps(out,indent=2,sort_keys=True) if ns.format=="json" else out["status"])
    return 0 if out["status"]=="valid" else 1
if __name__=="__main__": sys.exit(main())
