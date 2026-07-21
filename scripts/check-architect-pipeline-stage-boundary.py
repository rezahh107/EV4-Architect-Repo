#!/usr/bin/env python3
"""Validate intermediate Architect pipeline Stage Artifacts and receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "ev4-architect-pipeline-stage-artifact@1.0.0"
RECEIPT_SCHEMA = "ev4-architect-stage-validation-receipt@1.0.0"
VALIDATOR_ID = "architect-pipeline-stage-boundary-validator"
VALIDATOR_VERSION = "1.0.0"
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
            "receipt_id": f"asb-receipt-{artifact.get('artifact_id', 'unknown')}-{digest[:12]}",
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
            "artifact_id": upstream["artifact"]["artifact_id"],
            "artifact_schema": upstream["artifact"].get("artifact_schema"),
            "artifact_sha256": upstream["sha"],
            "validation_receipt_id": upstream["receipt"]["receipt_id"],
            "validation_status": upstream["receipt"]["status"],
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

    def validate_anchor(self, anchor, artifact, receipt, artifact_sha, path_base="$"):
        stage = artifact.get("stage_id", "unknown")
        diagnostics = []
        if not isinstance(anchor, dict):
            return {"status": "invalid", "diagnostics": [diag("ASB-ANCHOR-NOT-OBJECT", "ASB-R06", stage, path_base, "object", type(anchor).__name__, stage)]}
        required = ["anchor_schema", "anchor_type", "allowed_next_stage", "source_artifact", "source_validation"]
        for field in required:
            if field not in anchor:
                diagnostics.append(diag("ASB-ANCHOR-MISSING-FIELD", "ASB-R06", stage, f"{path_base}/{field}", "present", "missing", stage))
        if diagnostics:
            return {"status": "invalid", "diagnostics": sort_diags(diagnostics)}
        expected_artifact = {
            "artifact_id": artifact.get("artifact_id"),
            "artifact_schema": artifact.get("artifact_schema"),
            "artifact_sha256": artifact_sha,
            "stage_id": stage,
        }
        for field, expected in expected_artifact.items():
            observed = anchor.get("source_artifact", {}).get(field)
            if observed != expected:
                diagnostics.append(
                    diag(
                        f"ASB-ANCHOR-SOURCE-ARTIFACT-{field.upper()}-MISMATCH".replace("_", "-"),
                        "ASB-R07",
                        stage,
                        f"{path_base}/source_artifact/{field}",
                        str(expected),
                        str(observed),
                        stage,
                    )
                )
        expected_validation = {
            "receipt_id": receipt.get("receipt_id"),
            "receipt_schema": RECEIPT_SCHEMA,
            "validator_id": VALIDATOR_ID,
            "validator_version": VALIDATOR_VERSION,
            "status": "valid",
        }
        for field, expected in expected_validation.items():
            observed = anchor.get("source_validation", {}).get(field)
            if observed != expected:
                diagnostics.append(
                    diag(
                        f"ASB-ANCHOR-SOURCE-VALIDATION-{field.upper()}-MISMATCH".replace("_", "-"),
                        "ASB-R06" if field == "status" else "ASB-R07",
                        stage,
                        f"{path_base}/source_validation/{field}",
                        str(expected),
                        str(observed),
                        stage,
                    )
                )
        if anchor.get("anchor_schema") != ANCHOR_SCHEMA:
            diagnostics.append(diag("ASB-ANCHOR-SCHEMA-MISMATCH", "ASB-R06", stage, f"{path_base}/anchor_schema", ANCHOR_SCHEMA, str(anchor.get("anchor_schema")), stage))
        expected_type = "NEXT STAGE ANCHOR" if receipt.get("status") == "valid" else "REPAIR ANCHOR"
        if anchor.get("anchor_type") != expected_type:
            diagnostics.append(diag("ASB-ANCHOR-TYPE-MISMATCH", "ASB-R06", stage, f"{path_base}/anchor_type", expected_type, str(anchor.get("anchor_type")), stage))
        if anchor.get("anchor_type") == "NEXT STAGE ANCHOR" and anchor.get("allowed_next_stage") != NEXT_STAGE.get(stage):
            diagnostics.append(diag("ASB-ANCHOR-NEXT-STAGE-MISMATCH", "ASB-R06", stage, f"{path_base}/allowed_next_stage", str(NEXT_STAGE.get(stage)), str(anchor.get("allowed_next_stage")), stage))
        return {"status": "valid" if not diagnostics else "invalid", "diagnostics": sort_diags(diagnostics)}

    def make_anchor(self, artifact, receipt, artifact_sha):
        stage = artifact["stage_id"]
        return {
            "anchor_schema": ANCHOR_SCHEMA,
            "anchor_type": "NEXT STAGE ANCHOR" if receipt["status"] == "valid" else "REPAIR ANCHOR",
            "allowed_next_stage": NEXT_STAGE.get(stage) if receipt["status"] == "valid" else None,
            "repair_target_stage": None if receipt["status"] == "valid" else stage,
            "source_artifact": {
                "artifact_id": artifact["artifact_id"],
                "artifact_schema": artifact["artifact_schema"],
                "artifact_sha256": artifact_sha,
                "stage_id": stage,
            },
            "source_validation": {
                "receipt_id": receipt["receipt_id"],
                "receipt_schema": RECEIPT_SCHEMA,
                "validator_id": VALIDATOR_ID,
                "validator_version": VALIDATOR_VERSION,
                "status": receipt["status"],
            },
        }

    def context_from_upstreams(self, artifact_paths, receipt_paths):
        ctx = {"artifacts": {}, "lineage": {}}
        diagnostics = []
        for artifact_path, receipt_path in zip(artifact_paths, receipt_paths):
            artifact_file = Path(artifact_path)
            receipt_file = Path(receipt_path)
            artifact = load_json(artifact_file)
            receipt = load_json(receipt_file)
            digest = sha(artifact_file)
            stage = artifact.get("stage_id")
            expected = self.expected_receipt(artifact, digest, stage)
            for field in ["receipt_id", "receipt_schema", "validator_id", "validator_version", "artifact_id", "artifact_schema", "artifact_sha256", "stage_id", "status"]:
                if receipt.get(field) != expected.get(field):
                    diagnostics.append(diag(f"ASB-UPSTREAM-RECEIPT-{field.upper()}-MISMATCH".replace("_", "-"), "ASB-R07", stage, f"$/{receipt_file.name}/{field}", str(expected.get(field)), str(receipt.get(field)), stage))
            if receipt.get("status") != "valid":
                diagnostics.append(diag("ASB-UPSTREAM-RECEIPT-STATUS-NOT-VALID", "ASB-R06", stage, f"$/{receipt_file.name}/status", "valid", str(receipt.get("status")), stage))
            if not diagnostics:
                ctx["artifacts"][stage] = artifact
                ctx["lineage"][stage] = {"artifact": artifact, "sha": digest, "receipt": receipt}
        return ctx, diagnostics

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
    anchor_sequence_dir = base / "valid/complete-sequence-receipts-anchors"
    anchor_sequence = validator.validate_sequence(anchor_sequence_dir)
    checked.append(anchor_sequence)
    anchor_checks = []
    if anchor_sequence["status"] == "valid":
        for stage in ORDER:
            prefix = STAGE_FILE_PREFIX[stage]
            anchor_checks.append(
                validator.validate_anchor(
                    load_json(anchor_sequence_dir / f"{prefix}.anchor.json"),
                    load_json(anchor_sequence_dir / f"{prefix}.json"),
                    load_json(anchor_sequence_dir / f"{prefix}.receipt.json"),
                    sha(anchor_sequence_dir / f"{prefix}.json"),
                )
            )
        checked.extend(anchor_checks)
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
        "status": "valid" if valid["status"] == "valid" and anchor_sequence["status"] == "valid" and all(item["status"] == "valid" for item in anchor_checks) and not bad else "invalid",
        "diagnostics": []
        if not bad and anchor_sequence["status"] == "valid" and all(item["status"] == "valid" for item in anchor_checks)
        else sort_diags(
            ([] if not bad else [diag("ASB-FIXTURE-EXPECTED-INVALID-PASSED", "ASB-R07", "fixture", "$/fixtures", "invalid fixture failure", ",".join(bad))])
            + anchor_sequence.get("diagnostics", [])
            + [diagnostic for item in anchor_checks for diagnostic in item.get("diagnostics", [])]
        ),
        "checked": len(checked),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact")
    parser.add_argument("--write-receipt")
    parser.add_argument("--upstream-artifact", action="append", default=[])
    parser.add_argument("--upstream-receipt", action="append", default=[])
    parser.add_argument("--anchor")
    parser.add_argument("--anchor-source-artifact")
    parser.add_argument("--anchor-source-receipt")
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
        output = validator.validate_anchor(load_json(Path(args.anchor)), artifact, receipt, sha(artifact_path))
    elif args.artifact:
        if len(args.upstream_artifact) != len(args.upstream_receipt):
            parser.error("--upstream-artifact and --upstream-receipt counts must match")
        ctx, upstream_diagnostics = validator.context_from_upstreams(args.upstream_artifact, args.upstream_receipt)
        artifact_path = Path(args.artifact)
        artifact = load_json(artifact_path)
        digest = sha(artifact_path)
        output = validator.validate(artifact, artifact_path, digest, {**ctx, "self_sha": digest})
        if upstream_diagnostics:
            output["diagnostics"] = sort_diags(upstream_diagnostics + output["diagnostics"])
            output["status"] = "invalid"
        if args.write_receipt:
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
        parser.error("choose --artifact, --sequence, or --fixtures")
    print(json.dumps(output, indent=2, sort_keys=True) if args.format == "json" else output["status"])
    return 0 if output["status"] == "valid" else 1


if __name__ == "__main__":
    sys.exit(main())
