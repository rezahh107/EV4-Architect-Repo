#!/usr/bin/env python3
"""Validate intermediate Architect pipeline Stage Artifacts and receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "ev4-architect-pipeline-stage-artifact@1.1.0"
RECEIPT_SCHEMA = "ev4-architect-stage-validation-receipt@1.1.0"
VALIDATOR_ID = "architect-pipeline-stage-boundary-validator"
VALIDATOR_VERSION = "1.1.0"
FAMILIES = [f"A{i:02d}" for i in range(1, 9)]
ORDER = ["/decompose", "/architectures", "/score-evidence", "/score-audit"]
STAGE_FILE_PREFIX = {
    "/decompose": "decompose",
    "/architectures": "architectures",
    "/score-evidence": "score-evidence",
    "/score-audit": "score-audit",
}
PREDECESSOR = {
    "/architectures": "/decompose",
    "/score-evidence": "/architectures",
    "/score-audit": "/score-evidence",
}
ACTIVE_UNKNOWN_STATES = {"carried", "score_capped", "blocking", "downstream_only"}
NEXT_STAGE = {
    "/decompose": "/architectures",
    "/architectures": "/score-evidence",
    "/score-evidence": "/score-audit",
    "/score-audit": "/recommend",
}
ANCHOR_SCHEMA = "ev4-stage-anchor@1.2.0"
BOUNDARY_SCHEMA = "ev4-stage-boundary-record@1.0.0"
BUNDLE_SCHEMA = "ev4-architect-validation-bundle@1.0.0"
CARRIER_SCHEMAS = {
    "artifact": "schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json",
    "receipt": "schemas/ev4-architect-stage-validation-receipt.v1.schema.json",
    "boundary": "schemas/ev4-stage-boundary-record.v1.schema.json",
    "anchor": "schemas/ev4-stage-anchor.v1.schema.json",
    "bundle": "schemas/ev4-architect-validation-bundle.v1.schema.json",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diag(code, rule, stage, path, expected, observed, repair=None):
    item = {
        "code": code,
        "rule_id": rule,
        "stage_id": stage,
        "path": path,
        "expected": expected,
        "observed": observed,
    }
    if repair is not None:
        item["repair_target_stage"] = repair
    return item


def sort_diags(items):
    return sorted(items, key=lambda item: (item["stage_id"], item["path"], item["code"], item["rule_id"]))


class Validator:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.schema = load_json(self.root / "schemas/ev4-architect-pipeline-stage-artifact.v1.schema.json")
        self.js = Draft202012Validator(self.schema)

    def validate_path(self, path):
        artifact_path = Path(path)
        artifact = load_json(artifact_path)
        digest = sha(artifact_path)
        return self.validate(artifact, artifact_path, digest, {"self_sha": digest})

    def validate(self, artifact, path=None, digest=None, ctx=None):
        diagnostics = []
        stage = artifact.get("stage_id") if isinstance(artifact, dict) else "unknown"
        if not isinstance(artifact, dict):
            return self.receipt(
                {},
                digest or "0" * 64,
                "unknown",
                [diag("INPUT_NOT_OBJECT", "ASB-R01", "unknown", "$", "object", type(artifact).__name__)],
            )
        for error in self.js.iter_errors(artifact):
            diagnostics.append(
                diag(
                    "SCHEMA_VALIDATION_FAILED",
                    self.rule_for(stage, list(error.path)),
                    stage,
                    "$" + "".join(f"/{part}" for part in error.path),
                    error.message,
                    "schema_violation",
                    stage,
                )
            )
        if not diagnostics:
            diagnostics += self.semantic(artifact, ctx or {})
        return self.receipt(
            artifact,
            digest or hashlib.sha256(json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            stage,
            diagnostics,
        )

    def rule_for(self, stage, path):
        if stage == "/decompose":
            return "ASB-R01"
        if stage == "/architectures" and "architecture_coverage_matrix" in path:
            return "ASB-R03"
        if stage == "/architectures":
            return "ASB-R04"
        if stage == "/score-evidence":
            return "ASB-R05"
        if stage == "/score-audit":
            return "ASB-R08"
        return "ASB-R07"

    def receipt(self, artifact, digest, stage, diagnostics):
        status = "valid" if not diagnostics else "invalid"
        return {
            "receipt_schema": RECEIPT_SCHEMA,
            "receipt_id": f"asb-receipt-{artifact.get('run_id', 'unknown')}-{artifact.get('artifact_id', 'unknown')}-{digest[:12]}",
            "run_id": artifact.get("run_id", "unknown"),
            "validator_id": VALIDATOR_ID,
            "validator_version": VALIDATOR_VERSION,
            "artifact_id": artifact.get("artifact_id", "unknown"),
            "artifact_schema": artifact.get("artifact_schema", SCHEMA_ID),
            "artifact_sha256": digest,
            "stage_id": stage,
            "status": status,
            "diagnostics": sort_diags(diagnostics),
        }

    def expected_receipt(self, artifact, digest, stage):
        return self.receipt(artifact, digest, stage, [])

    def semantic(self, artifact, ctx):
        stage = artifact["stage_id"]
        payload = artifact["payload"]
        diagnostics = []
        predecessor = PREDECESSOR.get(stage)
        if predecessor:
            diagnostics += self._check_source_artifact_refs(artifact, ctx, predecessor)
        if stage == "/decompose":
            diagnostics += self._semantic_decompose(artifact, payload)
        if stage == "/architectures":
            diagnostics += self._semantic_architectures(artifact, payload, ctx)
        if stage == "/score-evidence":
            diagnostics += self._semantic_score_evidence(payload, ctx)
        if stage == "/score-audit":
            diagnostics += self._semantic_score_audit(payload, ctx)
        return diagnostics

    def _semantic_decompose(self, artifact, payload):
        diagnostics = []
        unknown_ids = [unknown["unknown_id"] for unknown in payload["unknowns"]]
        for unknown_id in sorted(set(item for item in unknown_ids if unknown_ids.count(item) > 1)):
            diagnostics.append(
                diag("ASB-DUPLICATE-UNKNOWN-ID", "ASB-R02", artifact["stage_id"], "$/payload/unknowns", "unique unknown_id", unknown_id, artifact["stage_id"])
            )
        if payload.get("allowed_next_stage") and payload.get("gate_results") in {"pass", "valid"} and diagnostics:
            diagnostics.append(
                diag(
                    "ASB-NEXT-STAGE-INVALID",
                    "ASB-R06",
                    artifact["stage_id"],
                    "$/payload/allowed_next_stage",
                    "null until valid receipt",
                    "self-declared pass",
                    artifact["stage_id"],
                )
            )
        return diagnostics

    def _semantic_architectures(self, artifact, payload, ctx):
        diagnostics = []
        stage = artifact["stage_id"]
        got = {row["family_id"] for row in payload["architecture_coverage_matrix"]}
        missing = [family for family in FAMILIES if family not in got]
        if missing:
            diagnostics.append(
                diag("ASB-COVERAGE-MATRIX-INCOMPLETE", "ASB-R03", stage, "$/payload/architecture_coverage_matrix", "A01-A08", ",".join(missing), stage)
            )
        stage_2 = ctx.get("artifacts", {}).get("/decompose")
        ledger = {row["unknown_id"]: row for row in payload["unknown_propagation_ledger"]}
        if stage_2:
            for unknown_id in [unknown["unknown_id"] for unknown in stage_2["payload"]["unknowns"]]:
                if unknown_id not in ledger:
                    diagnostics.append(
                        diag(
                            "ASB-UNKNOWN-LEDGER-MISSING-UPSTREAM-ID",
                            "ASB-R04",
                            stage,
                            "$/payload/unknown_propagation_ledger",
                            unknown_id,
                            "missing",
                            "/decompose",
                        )
                    )
        for index, row in enumerate(payload["unknown_propagation_ledger"]):
            if row["state"] == "resolved_with_evidence" and not row.get("resolving_evidence_refs"):
                diagnostics.append(
                    diag(
                        "ASB-UNKNOWN-RESOLVED-WITHOUT-EVIDENCE",
                        "ASB-R04",
                        stage,
                        f"$/payload/unknown_propagation_ledger/{index}/resolving_evidence_refs",
                        "non-empty resolving evidence",
                        "missing",
                        stage,
                    )
                )
        known = set(ledger)
        for index, candidate in enumerate(payload["active_candidates"]):
            for unknown_id in candidate["depends_on_unknown_ids"]:
                if unknown_id not in known:
                    diagnostics.append(
                        diag(
                            "ASB-CANDIDATE-UNTRACKED-UNKNOWN",
                            "ASB-R04",
                            stage,
                            f"$/payload/active_candidates/{index}/depends_on_unknown_ids",
                            unknown_id,
                            "absent from ledger",
                            stage,
                        )
                    )
        return diagnostics

    def _semantic_score_evidence(self, payload, ctx):
        diagnostics = []
        stage = "/score-evidence"
        stage_3 = ctx.get("artifacts", {}).get("/architectures")
        if not stage_3:
            diagnostics.append(
                diag(
                    "ASB-UPSTREAM-VALIDATION-REQUIRED",
                    "ASB-R05",
                    stage,
                    "$/payload/validated_upstream_artifact_refs",
                    "valid /architectures artifact and receipt",
                    "missing",
                    "/architectures",
                )
            )
        else:
            diagnostics += self._check_ref_array(payload["validated_upstream_artifact_refs"], ctx, "/architectures", stage, "$/payload/validated_upstream_artifact_refs")
        if payload.get("normalization_claim"):
            diagnostics.append(
                diag(
                    "ASB-DOWNSTREAM-RECONSTRUCTION-FORBIDDEN",
                    "ASB-R05",
                    stage,
                    "$/payload/normalization_claim",
                    "no reconstruction/normalization of absent artifacts",
                    payload["normalization_claim"],
                    "/architectures",
                )
            )
        if stage_3:
            valid_candidates = {candidate["candidate_id"] for candidate in stage_3["payload"]["active_candidates"]}
            active_unknowns = {
                row["unknown_id"]
                for row in stage_3["payload"]["unknown_propagation_ledger"]
                if row["state"] in ACTIVE_UNKNOWN_STATES or row["handling"] in ACTIVE_UNKNOWN_STATES
            }
            uncertain = {item.get("unknown_id") for item in payload["uncertainty_register"] if isinstance(item, dict)}
            for index, score in enumerate(payload["candidate_scores"]):
                if score["candidate_id"] not in valid_candidates:
                    diagnostics.append(
                        diag(
                            "ASB-CANDIDATE-NOT-IN-VALIDATED-STAGE3",
                            "ASB-R07",
                            stage,
                            f"$/payload/candidate_scores/{index}/candidate_id",
                            "candidate from validated Stage 3",
                            score["candidate_id"],
                            "/architectures",
                        )
                    )
                if score["scores_audited"]:
                    diagnostics.append(
                        diag(
                            "ASB-SCORE-EVIDENCE-CLAIMS-AUDITED",
                            "ASB-R08",
                            stage,
                            f"$/payload/candidate_scores/{index}/scores_audited",
                            "false before /score-audit",
                            "true",
                            stage,
                        )
                    )
                if score["final_total"] is not None and any(criteria["contract_critical"] and criteria["value"] == "?" for criteria in score["criteria"]):
                    diagnostics.append(
                        diag(
                            "ASB-FINAL-TOTAL-WITH-UNKNOWN",
                            "ASB-R05",
                            stage,
                            f"$/payload/candidate_scores/{index}/final_total",
                            "null while contract-critical criteria are ?",
                            str(score["final_total"]),
                            stage,
                        )
                    )
            for unknown_id in sorted(active_unknowns - uncertain):
                diagnostics.append(diag("ASB-STAGE3-UNKNOWN-DISCARDED", "ASB-R05", stage, "$/payload/uncertainty_register", unknown_id, "missing", stage))
        return diagnostics

    def _semantic_score_audit(self, payload, ctx):
        diagnostics = []
        stage = "/score-audit"
        if "/score-evidence" not in ctx.get("artifacts", {}):
            diagnostics.append(
                diag(
                    "ASB-STAGE5-MISSING-VALID-STAGE4",
                    "ASB-R08",
                    stage,
                    "$/payload/validated_stage_4_artifact_ref",
                    "valid Stage 4 receipt lineage",
                    "missing or invalid",
                    "/score-evidence",
                )
            )
        else:
            diagnostics += self._check_ref(payload["validated_stage_4_artifact_ref"], ctx, "/score-evidence", stage, "$/payload/validated_stage_4_artifact_ref")
        if payload["overall_audit_status"] == "pass" and payload["allowed_next_stage"] != "/recommend":
            diagnostics.append(diag("ASB-STAGE5-PASS-NEXT-STAGE", "ASB-R08", stage, "$/payload/allowed_next_stage", "/recommend", str(payload["allowed_next_stage"]), stage))
        return diagnostics

    def _check_source_artifact_refs(self, artifact, ctx, source_stage):
        return self._check_ref_array(artifact["source_artifacts"], ctx, source_stage, artifact["stage_id"], "$/source_artifacts")

    def _check_ref_array(self, refs, ctx, source_stage, current_stage, base_path):
        diagnostics = []
        matching = [(index, ref) for index, ref in enumerate(refs) if ref.get("source_stage") == source_stage]
        if not matching:
            if refs:
                diagnostics.append(
                    diag(
                        "ASB-LINEAGE-SOURCE-STAGE-MISMATCH",
                        "ASB-R07",
                        current_stage,
                        f"{base_path}/0/source_stage",
                        source_stage,
                        str(refs[0].get("source_stage")),
                        source_stage,
                    )
                )
            else:
                diagnostics.append(
                    diag("ASB-UPSTREAM-VALIDATION-REQUIRED", "ASB-R05", current_stage, base_path, f"validated {source_stage} source artifact", "missing", source_stage)
                )
            return diagnostics
        for index, ref in matching:
            diagnostics += self._check_ref(ref, ctx, source_stage, current_stage, f"{base_path}/{index}")
        return diagnostics

    def _check_ref(self, ref, ctx, source_stage, current_stage, base_path):
        upstream = ctx.get("lineage", {}).get(source_stage)
        if not upstream:
            return [diag("ASB-UPSTREAM-VALIDATION-REQUIRED", "ASB-R05", current_stage, base_path, f"validated {source_stage} source artifact", "missing", source_stage)]
        expected = {
            "run_id": upstream["artifact"]["run_id"],
            "artifact_id": upstream["artifact"]["artifact_id"],
            "artifact_schema": upstream["artifact"].get("artifact_schema"),
            "artifact_sha256": upstream["sha"],
            "source_stage": source_stage,
        }
        diagnostics = []
        for field, expected_value in expected.items():
            observed = ref.get(field)
            if observed != expected_value:
                diagnostics.append(
                    diag(
                        f"ASB-LINEAGE-{field.upper()}-MISMATCH".replace("_", "-"),
                        "ASB-R07",
                        current_stage,
                        f"{base_path}/{field}",
                        str(expected_value),
                        str(observed),
                        source_stage,
                    )
                )
        if upstream["receipt"].get("receipt_schema") != RECEIPT_SCHEMA:
            diagnostics.append(diag("ASB-LINEAGE-RECEIPT-SCHEMA-MISMATCH", "ASB-R07", current_stage, base_path, RECEIPT_SCHEMA, str(upstream["receipt"].get("receipt_schema")), source_stage))
        if upstream["receipt"].get("validator_id") != VALIDATOR_ID:
            diagnostics.append(diag("ASB-LINEAGE-VALIDATOR-ID-MISMATCH", "ASB-R07", current_stage, base_path, VALIDATOR_ID, str(upstream["receipt"].get("validator_id")), source_stage))
        if upstream["receipt"].get("validator_version") != VALIDATOR_VERSION:
            diagnostics.append(diag("ASB-LINEAGE-VALIDATOR-VERSION-MISMATCH", "ASB-R07", current_stage, base_path, VALIDATOR_VERSION, str(upstream["receipt"].get("validator_version")), source_stage))
        return diagnostics

    def validate_anchor(self, anchor, artifact, receipt, artifact_sha, boundary=None, boundary_sha=None, path_base="$"):
        stage = artifact.get("stage_id", "unknown")
        diagnostics = []
        if not isinstance(anchor, dict):
            return {"status": "invalid", "diagnostics": [diag("ASB-ANCHOR-NOT-OBJECT", "ASB-R06", stage, path_base, "object", type(anchor).__name__, stage)]}
        diagnostics += schema_diagnostics("anchor", anchor, stage, path_base)
        if boundary is None:
            diagnostics.append(diag("ASB-ANCHOR-BOUNDARY-REQUIRED", "ASB-R07", stage, path_base, "generated boundary from validated bundle", "missing external boundary", stage))
            return {"status": "invalid", "diagnostics": sort_diags(diagnostics)}
        if boundary_sha is None:
            boundary_sha = hashlib.sha256(canonical_json_bytes(boundary)).hexdigest()
        checks = {
            "anchor_schema": ANCHOR_SCHEMA,
            "run_id": artifact.get("run_id"),
            "source_stage": stage,
            "anchor_type": "NEXT_STAGE_ANCHOR" if boundary["transition"] == "next_stage" else "REPAIR_ANCHOR",
            "target_stage": boundary["target_stage"],
            "repair_target_stage": boundary["repair_target_stage"],
        }
        for field, expected in checks.items():
            if anchor.get(field) != expected:
                diagnostics.append(diag(f"ASB-ANCHOR-{field.upper()}-MISMATCH".replace("_", "-"), "ASB-R06", stage, f"{path_base}/{field}", str(expected), str(anchor.get(field)), stage))
        if anchor.get("run_id") != boundary.get("run_id"):
            diagnostics.append(diag("ASB-ANCHOR-BOUNDARY-RUN-ID-MISMATCH", "ASB-R07", stage, f"{path_base}/run_id", str(boundary.get("run_id")), str(anchor.get("run_id")), stage))
        bref = anchor.get("boundary_ref", {})
        for field, expected in {"boundary_id": boundary["boundary_id"], "boundary_schema": boundary["boundary_schema"], "boundary_sha256": boundary_sha}.items():
            if bref.get(field) != expected:
                diagnostics.append(diag(f"ASB-ANCHOR-BOUNDARY-REF-{field.upper()}-MISMATCH".replace("_", "-"), "ASB-R07", stage, f"{path_base}/boundary_ref/{field}", str(expected), str(bref.get(field)), stage))
        expected_unknowns, expected_blockers = semantic_handoff_items(artifact)
        observed_unknown_ids = {item.get("unknown_id") for item in anchor.get("handoff_state", {}).get("critical_unknowns", []) if isinstance(item, dict)}
        observed_blocker_ids = {item.get("unknown_id") for item in anchor.get("handoff_state", {}).get("blocking_items", []) if isinstance(item, dict)}
        for item in expected_unknowns:
            unknown_id = item.get("unknown_id")
            if unknown_id and unknown_id not in observed_unknown_ids:
                diagnostics.append(diag("ASB-ANCHOR-CRITICAL-UNKNOWN-MISSING", "ASB-R06", stage, f"{path_base}/handoff_state/critical_unknowns", str(unknown_id), "missing", stage))
        for item in expected_blockers:
            unknown_id = item.get("unknown_id")
            if unknown_id and unknown_id not in observed_blocker_ids:
                diagnostics.append(diag("ASB-ANCHOR-BLOCKING-ITEM-MISSING", "ASB-R06", stage, f"{path_base}/handoff_state/blocking_items", str(unknown_id), "missing", stage))
        return {"status": "valid" if not diagnostics else "invalid", "diagnostics": sort_diags(diagnostics)}

    def make_anchor(self, artifact, receipt, artifact_sha, boundary=None, boundary_sha=None):
        if boundary is None:
            boundary = boundary_for(self, artifact, artifact_sha, receipt)
        if boundary_sha is None:
            boundary_sha = hashlib.sha256(canonical_json_bytes(boundary)).hexdigest()
        success = boundary["transition"] == "next_stage"
        return anchor_for(artifact, boundary, boundary_sha)

    def context_from_upstreams(self, artifact_paths, receipt_paths):
        diagnostics = []
        for receipt_path in receipt_paths:
            diagnostics.append(
                diag(
                    "ASB-EXTERNAL-RECEIPT-NOT-AUTHORITY",
                    "ASB-R07",
                    "diagnostic",
                    f"$/{Path(receipt_path).name}",
                    "validate-run generated receipt context",
                    "caller-supplied receipt",
                    None,
                )
            )
        for artifact_path in artifact_paths:
            diagnostics.append(
                diag(
                    "ASB-EXTERNAL-UPSTREAM-DIAGNOSTIC-ONLY",
                    "ASB-R07",
                    "diagnostic",
                    f"$/{Path(artifact_path).name}",
                    "full validate-run transaction",
                    "standalone upstream assertion",
                    None,
                )
            )
        return {"artifacts": {}, "lineage": {}}, diagnostics

    def validate_sequence(self, directory):
        sequence_dir = Path(directory)
        present = {}
        diagnostics = []
        for stage in ORDER:
            files = sorted(
                path
                for path in sequence_dir.glob(f"{STAGE_FILE_PREFIX[stage]}*.json")
                if not path.name.endswith(".receipt.json") and not path.name.endswith(".anchor.json")
            )
            if len(files) > 1:
                diagnostics.append(
                    diag(
                        "ASB-DUPLICATE-STAGE-ARTIFACT",
                        "ASB-R07",
                        stage,
                        f"$/{STAGE_FILE_PREFIX[stage]}",
                        "exactly one artifact file per stage",
                        ",".join(path.name for path in files),
                        stage,
                    )
                )
            if files:
                present[stage] = files[0]
        if diagnostics:
            return {"status": "invalid", "diagnostics": sort_diags(diagnostics), "receipts": []}
        existing = [stage for stage in ORDER if stage in present]
        if not existing:
            diagnostics.append(
                diag(
                    "ASB-EMPTY-SEQUENCE",
                    "ASB-R05",
                    "sequence",
                    "$",
                    "at least /decompose artifact",
                    "empty sequence directory",
                    "/decompose",
                )
            )
            return {"status": "invalid", "diagnostics": sort_diags(diagnostics), "receipts": []}
        if existing:
            last_index = ORDER.index(existing[-1])
            for stage in ORDER[: last_index + 1]:
                if stage not in present:
                    diagnostics.append(
                        diag(
                            "ASB-MISSING-PREDECESSOR-STAGE",
                            "ASB-R05",
                            stage,
                            f"$/{STAGE_FILE_PREFIX[stage]}.json",
                            "contiguous validated stage prefix",
                            "missing predecessor artifact",
                            stage,
                        )
                    )
                    return {"status": "invalid", "diagnostics": sort_diags(diagnostics), "receipts": []}
        run_ids = set()
        for stage in existing:
            try:
                run_ids.add(load_json(present[stage]).get("run_id"))
            except Exception:
                run_ids.add(None)
        if len(run_ids) != 1 or None in run_ids:
            diagnostics.append(diag("ASB-RUN-ID-MISMATCH", "ASB-R07", "sequence", "$/run_id", "one stable run_id", ",".join(str(item) for item in sorted(run_ids, key=str)), "/decompose"))
            return {"status": "invalid", "diagnostics": sort_diags(diagnostics), "receipts": []}
        ctx = {"artifacts": {}, "lineage": {}}
        receipts = []
        all_diagnostics = []
        for stage in ORDER:
            artifact_path = present.get(stage)
            if not artifact_path:
                break
            digest = sha(artifact_path)
            artifact = load_json(artifact_path)
            if artifact.get("stage_id") != stage:
                all_diagnostics.append(
                    diag("ASB-STAGE-FILE-MISMATCH", "ASB-R07", stage, f"$/{artifact_path.name}/stage_id", stage, str(artifact.get("stage_id")), stage)
                )
                break
            receipt = self.validate(artifact, artifact_path, digest, {**ctx, "self_sha": digest})
            receipts.append(receipt)
            all_diagnostics += receipt["diagnostics"]
            if receipt["status"] == "valid":
                ctx["artifacts"][stage] = artifact
                ctx["lineage"][stage] = {"artifact": artifact, "sha": digest, "receipt": receipt}
            else:
                break
        return {"status": "valid" if not all_diagnostics else "invalid", "diagnostics": sort_diags(all_diagnostics), "receipts": receipts}


def validate_fixture_suite(validator):
    base = ROOT / "fixtures/architect-pipeline-stage-boundary"
    valid = validator.validate_sequence(base / "valid/complete-sequence")
    checked = [valid]
    bundle_dir = base / "valid/complete-sequence-receipts-anchors"
    bundle_check = validate_bundle_directory(bundle_dir)
    checked.append(bundle_check)
    anchor_checks = []
    bad = []
    for directory in sorted((base / "invalid").iterdir()):
        if not directory.is_dir():
            continue
        if (directory / "stale.receipt.json").exists():
            artifact_path = next(path for path in directory.glob("*.json") if path.name != "stale.receipt.json")
            actual = sha(artifact_path)
            recorded = load_json(directory / "stale.receipt.json").get("artifact_sha256")
            result = {
                "status": "invalid" if actual != recorded else "valid",
                "diagnostics": []
                if actual != recorded
                else [diag("ASB-RECEIPT-DIGEST-UNEXPECTED-MATCH", "ASB-R07", "fixture", "$/stale.receipt.json/artifact_sha256", "digest mismatch fixture", actual)],
            }
        else:
            result = validator.validate_sequence(directory)
        checked.append(result)
        if result["status"] == "valid":
            bad.append(str(directory.relative_to(ROOT)))
    return {
        "status": "valid" if valid["status"] == "valid" and bundle_check["status"] == "valid" and not bad else "invalid",
        "diagnostics": []
        if not bad and bundle_check["status"] == "valid"
        else sort_diags(
            ([] if not bad else [diag("ASB-FIXTURE-EXPECTED-INVALID-PASSED", "ASB-R07", "fixture", "$/fixtures", "invalid fixture failure", ",".join(bad))])
            + bundle_check.get("diagnostics", [])
        ),
        "checked": len(checked),
    }




def schema_validator(kind):
    schema = load_json(ROOT / CARRIER_SCHEMAS[kind])
    return Draft202012Validator(schema)


def schema_diagnostics(kind, value, stage="carrier", path="$"):
    diagnostics = []
    for error in schema_validator(kind).iter_errors(value):
        diagnostics.append(
            diag(
                f"ASB-{kind.upper()}-SCHEMA-VALIDATION-FAILED",
                "ASB-R07",
                stage,
                path + "".join(f"/{part}" for part in error.path),
                error.message,
                "schema_violation",
                None,
            )
        )
    return diagnostics


def path_within(root, rel):
    root_resolved = Path(root).resolve()
    target = (root_resolved / rel).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError:
        return None
    return target

def canonical_json_bytes(value):
    return json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(canonical_json_bytes(value))


def receipt_sha_for(receipt):
    return hashlib.sha256(canonical_json_bytes(receipt)).hexdigest()


def boundary_for(validator, artifact, artifact_sha, receipt):
    valid = receipt["status"] == "valid"
    stage = artifact["stage_id"]
    return {
        "boundary_schema": "ev4-stage-boundary-record@1.0.0",
        "boundary_id": f"asb-boundary-{artifact['run_id']}-{stage.strip('/').replace('/', '-')}-{artifact_sha[:12]}",
        "run_id": artifact["run_id"],
        "source_stage": stage,
        "target_stage": NEXT_STAGE.get(stage) if valid else None,
        "repair_target_stage": None if valid else stage,
        "transition": "next_stage" if valid else "repair",
        "artifact": {"artifact_id": artifact["artifact_id"], "artifact_schema": artifact["artifact_schema"], "artifact_sha256": artifact_sha},
        "receipt": {"receipt_id": receipt["receipt_id"], "receipt_schema": receipt["receipt_schema"], "receipt_sha256": receipt_sha_for(receipt), "validator_id": VALIDATOR_ID, "validator_version": VALIDATOR_VERSION, "status": receipt["status"]},
        "authorization": {"next_stage_authorized": valid, "authorization_reason": "generated_valid_receipt" if valid else "generated_invalid_receipt"},
    }


def semantic_handoff_items(artifact):
    payload = artifact.get("payload", {})
    stage = artifact.get("stage_id")
    critical = []
    blockers = []
    if stage == "/decompose":
        for unknown in payload.get("unknowns", []):
            item = {
                "unknown_id": unknown.get("unknown_id"),
                "description": unknown.get("description", ""),
                "state": unknown.get("evidence_state", "unknown"),
                "source_stage": stage,
            }
            if unknown.get("evidence_state") not in {"resolved_with_evidence", "stale", "not_applicable"}:
                critical.append(item)
            if unknown.get("blocking") is True:
                blockers.append(item)
    elif stage == "/architectures":
        for row in payload.get("unknown_propagation_ledger", []):
            state = row.get("state")
            handling = row.get("handling")
            item = {
                "unknown_id": row.get("unknown_id"),
                "state": state,
                "handling": handling,
                "source_stage": stage,
                "affected_candidates": row.get("affected_candidates", []),
            }
            if state in ACTIVE_UNKNOWN_STATES or handling in ACTIVE_UNKNOWN_STATES:
                critical.append(item)
            if state == "blocking" or handling == "blocking":
                blockers.append(item)
    elif stage == "/score-evidence":
        for row in payload.get("uncertainty_register", []):
            item = {"unknown_id": row.get("unknown_id"), "state": row.get("state", "active"), "source_stage": stage}
            critical.append(item)
            if row.get("blocking") is True or row.get("state") == "blocking":
                blockers.append(item)
    elif stage == "/score-audit":
        for repair in payload.get("required_repairs", []):
            blockers.append({"repair": repair, "source_stage": stage})
    return critical, blockers


def anchor_for(artifact, boundary, boundary_sha, active_unknowns=None, blockers=None):
    success = boundary["transition"] == "next_stage"
    derived_unknowns, derived_blockers = semantic_handoff_items(artifact)
    critical_unknowns = derived_unknowns if active_unknowns is None else active_unknowns
    blocking_items = derived_blockers if blockers is None else blockers
    return {
        "anchor_schema": ANCHOR_SCHEMA,
        "anchor_id": f"asb-anchor-{artifact['run_id']}-{artifact['stage_id'].strip('/').replace('/', '-')}-{boundary_sha[:12]}",
        "run_id": artifact["run_id"],
        "anchor_type": "NEXT_STAGE_ANCHOR" if success else "REPAIR_ANCHOR",
        "source_stage": artifact["stage_id"],
        "target_stage": boundary["target_stage"] if success else None,
        "repair_target_stage": None if success else boundary["repair_target_stage"],
        "boundary_ref": {"boundary_id": boundary["boundary_id"], "boundary_schema": boundary["boundary_schema"], "boundary_sha256": boundary_sha},
        "handoff_state": {
            "critical_unknowns": critical_unknowns,
            "blocking_items": blocking_items,
            "confidence_delta": ["receipt_status:" + boundary["receipt"]["status"]],
            "gate_results": "machine_boundary_valid" if success else "machine_boundary_repair",
            "audit_flags": [] if success else ["repair_required"],
            "required_user_confirmations": [] if success else ["repair_target_stage:" + str(boundary["repair_target_stage"])],
            "partial_rerun_state": {
                "reusable_until": None,
                "invalidation_triggers": ["artifact_bytes_change", "schema_version_change", "validator_version_change"],
                "earliest_safe_rerun_stage": artifact["stage_id"],
                "downstream_payloads_dependent_on_this_stage": [stage for stage in ORDER[ORDER.index(artifact["stage_id"])+1:]],
            },
            "stage_boundary": {
                "allowed_work": [] if not success else [f"continue_to:{boundary['target_stage']}"],
                "forbidden_work": ["do_not_treat_anchor_as_machine_authorization", "do_not_reconstruct_missing_upstream_artifacts"],
                "stop_conditions": [] if success else ["repair_required"],
            },
        },
    }


def bundle_manifest(run_id, stages, overall_status, authorized_next_stage, repair_target_stage):
    manifest = {
        "bundle_schema": "ev4-architect-validation-bundle@1.0.0",
        "bundle_id": f"asb-bundle-{run_id}",
        "run_id": run_id,
        "validator_id": VALIDATOR_ID,
        "validator_version": VALIDATOR_VERSION,
        "determinism_profile": "deterministic_no_timestamps_v1",
        "stage_sequence": [stage["stage_id"] for stage in stages],
        "overall_status": overall_status,
        "authorized_next_stage": authorized_next_stage,
        "repair_target_stage": repair_target_stage,
        "stages": stages,
        "bundle_content_digest": "",
    }
    digest_input = json.dumps({k: v for k, v in manifest.items() if k != "bundle_content_digest"}, sort_keys=True, separators=(",", ":")).encode()
    manifest["bundle_content_digest"] = hashlib.sha256(digest_input).hexdigest()
    return manifest



def manifest_stage_entry(output_path, stage, artifact, artifact_sha, receipt, receipt_dst, boundary, boundary_dst, anchor, anchor_dst, artifact_dst):
    return {
        "stage_id": stage,
        "artifact_path": str(artifact_dst.relative_to(output_path)),
        "artifact_id": artifact["artifact_id"],
        "artifact_schema": artifact["artifact_schema"],
        "artifact_sha256": artifact_sha,
        "receipt_path": str(receipt_dst.relative_to(output_path)),
        "receipt_id": receipt["receipt_id"],
        "receipt_schema": receipt["receipt_schema"],
        "receipt_sha256": file_sha(receipt_dst),
        "boundary_path": str(boundary_dst.relative_to(output_path)),
        "boundary_id": boundary["boundary_id"],
        "boundary_schema": boundary["boundary_schema"],
        "boundary_sha256": file_sha(boundary_dst),
        "anchor_path": str(anchor_dst.relative_to(output_path)),
        "anchor_id": anchor["anchor_id"],
        "anchor_schema": anchor["anchor_schema"],
        "anchor_sha256": file_sha(anchor_dst),
    }


def validate_bundle_directory(bundle_dir):
    bundle_path = Path(bundle_dir)
    diagnostics = []
    try:
        manifest = load_json(bundle_path / "manifest.json")
    except Exception as exc:
        return {"status": "invalid", "diagnostics": [diag("ASB-BUNDLE-MANIFEST-MISSING", "ASB-R07", "bundle", "$/manifest.json", "readable manifest", type(exc).__name__, None)]}
    diagnostics += schema_diagnostics("bundle", manifest, "bundle", "$")
    expected_files = {Path("manifest.json")}
    for index, stage_entry in enumerate(manifest.get("stages", [])):
        for kind in ["artifact", "receipt", "boundary", "anchor"]:
            path_key = f"{kind}_path"
            rel = stage_entry.get(path_key)
            if rel is None:
                continue
            safe = path_within(bundle_path, rel)
            if safe is None:
                diagnostics.append(diag("ASB-BUNDLE-PATH-TRAVERSAL", "ASB-R07", stage_entry.get("stage_id", "bundle"), f"$/stages/{index}/{path_key}", "path within bundle", str(rel), None))
                continue
            expected_files.add(Path(rel))
            if not safe.exists():
                diagnostics.append(diag(f"ASB-BUNDLE-{kind.upper()}-MISSING", "ASB-R07", stage_entry.get("stage_id", "bundle"), f"$/stages/{index}/{path_key}", "existing file", str(rel), None))
                continue
            try:
                value = load_json(safe)
            except Exception as exc:
                diagnostics.append(diag(f"ASB-BUNDLE-{kind.upper()}-UNREADABLE", "ASB-R07", stage_entry.get("stage_id", "bundle"), f"$/stages/{index}/{path_key}", "readable JSON", type(exc).__name__, None))
                continue
            diagnostics += schema_diagnostics(kind, value, stage_entry.get("stage_id", "bundle"), f"$/stages/{index}/{kind}")
            sha_key = f"{kind}_sha256"
            if sha_key in stage_entry and file_sha(safe) != stage_entry[sha_key]:
                diagnostics.append(diag(f"ASB-BUNDLE-{kind.upper()}-SHA256-MISMATCH", "ASB-R07", stage_entry.get("stage_id", "bundle"), f"$/stages/{index}/{sha_key}", file_sha(safe), str(stage_entry[sha_key]), None))
    actual_files = {path.relative_to(bundle_path) for path in bundle_path.rglob("*.json")}
    extras = sorted(str(path) for path in actual_files - expected_files)
    missing = sorted(str(path) for path in expected_files - actual_files)
    if extras:
        diagnostics.append(diag("ASB-BUNDLE-EXTRA-FILE", "ASB-R07", "bundle", "$", "only manifest-listed carriers", ",".join(extras), None))
    if missing:
        diagnostics.append(diag("ASB-BUNDLE-LISTED-FILE-MISSING", "ASB-R07", "bundle", "$", "all manifest-listed carriers", ",".join(missing), None))
    if diagnostics:
        return {"status": "invalid", "diagnostics": sort_diags(diagnostics), "manifest": manifest}
    with tempfile.TemporaryDirectory(prefix="ev4-bundle-verify-") as tmp:
        regenerated = Path(tmp) / "bundle"
        regen_result = validate_run_transaction(Validator(ROOT), bundle_path / "artifacts", regenerated)
        if regen_result["status"] != manifest.get("overall_status"):
            diagnostics.append(diag("ASB-BUNDLE-STATUS-CONTRADICTS-REGENERATED", "ASB-R07", "bundle", "$/overall_status", regen_result["status"], str(manifest.get("overall_status")), None))
        regen_files = {path.relative_to(regenerated) for path in regenerated.rglob("*.json")}
        if regen_files != actual_files:
            diagnostics.append(diag("ASB-BUNDLE-FILE-SET-MISMATCH", "ASB-R07", "bundle", "$", ",".join(sorted(map(str, regen_files))), ",".join(sorted(map(str, actual_files))), None))
        for rel in sorted(regen_files & actual_files):
            observed = (bundle_path / rel).read_bytes()
            expected = (regenerated / rel).read_bytes()
            if observed != expected:
                diagnostics.append(diag("ASB-BUNDLE-CARRIER-BYTE-MISMATCH", "ASB-R07", "bundle", f"$/{rel}", hashlib.sha256(expected).hexdigest(), hashlib.sha256(observed).hexdigest(), None))
        try:
            regen_manifest = load_json(regenerated / "manifest.json")
            if regen_manifest.get("authorized_next_stage") != manifest.get("authorized_next_stage"):
                diagnostics.append(diag("ASB-BUNDLE-AUTHORIZATION-CONTRADICTS-REGENERATED", "ASB-R07", "bundle", "$/authorized_next_stage", str(regen_manifest.get("authorized_next_stage")), str(manifest.get("authorized_next_stage")), None))
            if regen_manifest.get("repair_target_stage") != manifest.get("repair_target_stage"):
                diagnostics.append(diag("ASB-BUNDLE-REPAIR-TARGET-CONTRADICTS-REGENERATED", "ASB-R07", "bundle", "$/repair_target_stage", str(regen_manifest.get("repair_target_stage")), str(manifest.get("repair_target_stage")), None))
        except Exception as exc:
            diagnostics.append(diag("ASB-BUNDLE-REGENERATION-FAILED", "ASB-R07", "bundle", "$", "regenerated manifest", type(exc).__name__, None))
    return {"status": "valid" if not diagnostics else "invalid", "diagnostics": sort_diags(diagnostics), "manifest": manifest}


def validate_run_transaction(validator, sequence, output):
    sequence_path = Path(sequence)
    result = validator.validate_sequence(sequence_path)
    output_path = Path(output)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)
    for sub in ["artifacts", "receipts", "boundaries", "anchors"]:
        (output_path / sub).mkdir()
    stages = []
    run_id = None
    receipts_to_write = result.get("receipts", [])
    if result["status"] != "valid":
        repair_stage = result["diagnostics"][0].get("repair_target_stage") if result.get("diagnostics") else "/decompose"
        receipts_to_write = [receipt for receipt in receipts_to_write if receipt.get("stage_id") == repair_stage and receipt.get("status") != "valid"]
    for receipt in receipts_to_write:
        stage = receipt["stage_id"]
        prefix = STAGE_FILE_PREFIX[stage]
        artifact_src = sequence_path / f"{prefix}.json"
        if not artifact_src.exists():
            continue
        artifact = load_json(artifact_src)
        run_id = artifact["run_id"] if run_id is None else run_id
        artifact_sha = sha(artifact_src)
        artifact_dst = output_path / "artifacts" / f"{prefix}.json"
        artifact_dst.write_bytes(artifact_src.read_bytes())
        receipt_dst = output_path / "receipts" / f"{prefix}.receipt.json"
        write_json(receipt_dst, receipt)
        boundary = boundary_for(validator, artifact, artifact_sha, receipt)
        boundary_dst = output_path / "boundaries" / f"{prefix}.boundary.json"
        write_json(boundary_dst, boundary)
        boundary_sha = file_sha(boundary_dst)
        anchor = anchor_for(artifact, boundary, boundary_sha)
        anchor_dst = output_path / "anchors" / f"{prefix}.anchor.json"
        write_json(anchor_dst, anchor)
        stages.append(manifest_stage_entry(output_path, stage, artifact, artifact_sha, receipt, receipt_dst, boundary, boundary_dst, anchor, anchor_dst, artifact_dst))
    if run_id is None:
        # Keep failure manifest deterministic even when no artifact could be trusted enough to copy.
        run_id = "unknown"
        for receipt in result.get("receipts", []):
            if receipt.get("run_id"):
                run_id = receipt["run_id"]
                break
    overall = result["status"]
    authorized = NEXT_STAGE.get(stages[-1]["stage_id"]) if overall == "valid" and stages else None
    repair = None if overall == "valid" else (result["diagnostics"][0].get("repair_target_stage") if result.get("diagnostics") else "/decompose")
    manifest = bundle_manifest(run_id, stages, overall, authorized, repair)
    write_json(output_path / "manifest.json", manifest)
    carrier_diagnostics = schema_diagnostics("bundle", manifest, "bundle", "$")
    for stage_entry in stages:
        carrier_diagnostics += schema_diagnostics("receipt", load_json(output_path / stage_entry["receipt_path"]), stage_entry["stage_id"], f"$/{stage_entry['receipt_path']}")
        carrier_diagnostics += schema_diagnostics("boundary", load_json(output_path / stage_entry["boundary_path"]), stage_entry["stage_id"], f"$/{stage_entry['boundary_path']}")
        carrier_diagnostics += schema_diagnostics("anchor", load_json(output_path / stage_entry["anchor_path"]), stage_entry["stage_id"], f"$/{stage_entry['anchor_path']}")
    if carrier_diagnostics:
        result_diagnostics = sort_diags(result["diagnostics"] + carrier_diagnostics)
        return {"status": "invalid", "diagnostics": result_diagnostics, "manifest": manifest}
    return {"status": overall, "diagnostics": result["diagnostics"], "manifest": manifest}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "validate-bundle":
        parser = argparse.ArgumentParser()
        parser.add_argument("validate_bundle")
        parser.add_argument("--bundle", required=True)
        parser.add_argument("--format", choices=["text", "json"], default="text")
        args = parser.parse_args()
        output = validate_bundle_directory(args.bundle)
        print(json.dumps(output, indent=2, sort_keys=True) if args.format == "json" else output["status"])
        return 0 if output["status"] == "valid" else 1
    if len(sys.argv) > 1 and sys.argv[1] == "validate-run":
        parser = argparse.ArgumentParser()
        parser.add_argument("validate_run")
        parser.add_argument("--sequence", required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--format", choices=["text", "json"], default="text")
        args = parser.parse_args()
        output = validate_run_transaction(Validator(ROOT), args.sequence, args.output)
        print(json.dumps(output, indent=2, sort_keys=True) if args.format == "json" else output["status"])
        return 0 if output["status"] == "valid" else 1
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact")
    parser.add_argument("--write-receipt")
    parser.add_argument("--upstream-artifact", action="append", default=[])
    parser.add_argument("--upstream-receipt", action="append", default=[])
    parser.add_argument("--anchor")
    parser.add_argument("--anchor-source-artifact")
    parser.add_argument("--anchor-source-receipt")
    parser.add_argument("--anchor-source-boundary")
    parser.add_argument("--sequence")
    parser.add_argument("--write-receipts")
    parser.add_argument("--write-anchors")
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    validator = Validator(ROOT)
    if args.anchor:
        if not args.anchor_source_artifact or not args.anchor_source_receipt:
            parser.error("--anchor requires --anchor-source-artifact and --anchor-source-receipt")
        artifact_path = Path(args.anchor_source_artifact)
        artifact = load_json(artifact_path)
        receipt = load_json(Path(args.anchor_source_receipt))
        boundary = load_json(Path(args.anchor_source_boundary)) if args.anchor_source_boundary else None
        boundary_sha = file_sha(Path(args.anchor_source_boundary)) if args.anchor_source_boundary else None
        output = validator.validate_anchor(load_json(Path(args.anchor)), artifact, receipt, sha(artifact_path), boundary, boundary_sha)
        output["diagnostic_only"] = True
        output["authorization_valid"] = False
        output["diagnostics"] = sort_diags(output.get("diagnostics", []) + [diag("ASB-STANDALONE-ANCHOR-NOT-AUTHORITY", "ASB-R07", artifact.get("stage_id", "unknown"), "$", "validate-bundle authorization", "standalone anchor diagnostic", None)])
        output["status"] = "invalid"
    elif args.artifact:
        if len(args.upstream_artifact) != len(args.upstream_receipt):
            parser.error("--upstream-artifact and --upstream-receipt counts must match")
        ctx, upstream_diagnostics = validator.context_from_upstreams(args.upstream_artifact, args.upstream_receipt)
        artifact_path = Path(args.artifact)
        artifact = load_json(artifact_path)
        digest = sha(artifact_path)
        output = validator.validate(artifact, artifact_path, digest, {**ctx, "self_sha": digest})
        output["diagnostic_only"] = True
        output["authorization_valid"] = False
        if args.upstream_artifact or args.upstream_receipt:
            output["diagnostics"] = sort_diags(upstream_diagnostics + output["diagnostics"] + [diag("ASB-STANDALONE-ARTIFACT-NOT-AUTHORITY", "ASB-R07", artifact.get("stage_id", "unknown"), "$", "validate-run transaction", "standalone artifact diagnostic", None)])
            output["status"] = "invalid"
        if args.write_receipt:
            # Diagnostic receipts are comparison artifacts only and cannot authorize continuation.
            Path(args.write_receipt).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif args.sequence:
        output = validator.validate_sequence(args.sequence)
        if args.write_receipts or args.write_anchors:
            receipt_dir = Path(args.write_receipts) if args.write_receipts else None
            anchor_dir = Path(args.write_anchors) if args.write_anchors else None
            if receipt_dir:
                receipt_dir.mkdir(parents=True, exist_ok=True)
            if anchor_dir:
                anchor_dir.mkdir(parents=True, exist_ok=True)
            for receipt in output.get("receipts", []):
                stage = receipt["stage_id"]
                if receipt_dir:
                    (receipt_dir / f"{STAGE_FILE_PREFIX[stage]}.receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                if anchor_dir and receipt["status"] == "valid":
                    artifact_path = Path(args.sequence) / f"{STAGE_FILE_PREFIX[stage]}.json"
                    artifact = load_json(artifact_path)
                    anchor = validator.make_anchor(artifact, receipt, sha(artifact_path))
                    (anchor_dir / f"{STAGE_FILE_PREFIX[stage]}.anchor.json").write_text(json.dumps(anchor, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif args.fixtures:
        output = validate_fixture_suite(validator)
    else:
        parser.error("choose validate-run, validate-bundle, --artifact, --sequence, or --fixtures")
    print(json.dumps(output, indent=2, sort_keys=True) if args.format == "json" else output["status"])
    return 0 if output["status"] == "valid" else 1


if __name__ == "__main__":
    sys.exit(main())
