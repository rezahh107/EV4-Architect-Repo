#!/usr/bin/env python3
"""Evaluate the canonical quality-first Architect runtime fixture."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from architect_quality_runtime import ROOT, evaluate_run

BUILD_TREE = {
    "candidate_id": "ARCH-FAM-C",
    "root": "node-root",
    "nodes": [
        {"id": "node-root", "role": "section_root", "children": ["node-wrapper"]},
        {"id": "node-wrapper", "role": "normal_flow_group", "children": []},
    ],
}


def load_outputs(path: Path, root: Path) -> list[dict]:
    historical_results = json.loads(path.read_text(encoding="utf-8"))
    outputs: list[dict] = []
    for result in historical_results:
        stage_id = result["stage_id"]
        output = {
            "run_id": result["run_id"],
            "stage_id": stage_id,
            "stage_version": result["stage_version"],
            "check_evidence": {
                key: {"result": value, "reason": f"Structured model assessment for {key}."}
                for key, value in result["quality_checks"].items()
            },
            "blockers": result["blocking_issues"],
            "unknown_introductions": [],
            "unknown_resolutions": [],
            "research_disposition": result["research_disposition"],
            "decision_input": {
                "selected_candidate_id": result["decision_state"]["selected_candidate_id"],
                "architecture_drift": result["decision_state"]["architecture_drift"],
                "hidden_recommendation": result["decision_state"]["hidden_recommendation"],
                "unknown_converted_to_exact": result["decision_state"]["unknown_converted_to_exact"],
            },
            "final_audit_findings": result["final_audit_findings"],
        }
        if stage_id == "/intake":
            output["unknown_introductions"] = [{
                "unknown_id": "U-mobile-behavior",
                "statement": "Mobile connector treatment requires evidence.",
                "downstream_critical": False,
            }]
            output["check_evidence"] = {
                "required_input_captured": {"result": "pass", "reason": "Desktop and mobile input are present."},
                "architecture_not_selected": {"result": "pass", "reason": "Intake does not select architecture."},
                "exact_values_not_invented": {"result": "pass", "reason": "Exact values remain unknown."},
            }
        elif stage_id == "/research":
            output["check_evidence"] = {
                "research_scope_resolved": {"result": "pass", "reason": "No platform question requires lookup."},
                "platform_project_boundary_preserved": {"result": "pass", "reason": "Research does not decide visual structure."},
                "unsupported_claims_remain_unknown": {"result": "pass", "reason": "Unsupported claims remain unknown."},
            }
        elif stage_id == "/decompose":
            output["check_evidence"] = {
                "observation_inference_separated": {"result": "pass", "reason": "Observation and inference are separated."},
                "implementation_not_selected": {"result": "pass", "reason": "No implementation is selected."},
                "unknowns_recorded": {"result": "pass", "reason": "Unknowns remain visible."},
            }
        elif stage_id == "/architectures":
            output["check_evidence"] = {
                "architecture_coverage_complete": {"result": "pass", "reason": "Architecture families are covered."},
                "recommendation_not_made": {"result": "pass", "reason": "No early recommendation."},
                "unknowns_propagated": {"result": "pass", "reason": "Unknowns are preserved."},
            }
        elif stage_id == "/score-evidence":
            output["check_evidence"] = {
                "evidence_scoring_valid": {"result": "pass", "reason": "Approved evidence rubric is used."},
                "hidden_recommendation_absent": {"result": "pass", "reason": "No hidden recommendation."},
                "unknowns_not_numeric": {"result": "pass", "reason": "Unknowns are not numeric."},
            }
            output["unknown_resolutions"] = [{
                "unknown_id": "U-mobile-behavior",
                "resolution_type": "user_confirmation",
                "note": "User supplied the mobile reference.",
            }]
        elif stage_id == "/score-audit":
            output["check_evidence"] = {
                "score_audit_acceptance": {"result": "pass", "reason": "Audit accepts the score."},
                "rubric_integrity": {"result": "pass", "reason": "Rubric integrity is preserved."},
                "unknowns_not_numeric": {"result": "pass", "reason": "Unknowns remain non-numeric."},
            }
        elif stage_id == "/recommend":
            output["decision_input"]["selected_candidate_id"] = "ARCH-FAM-C"
            output["check_evidence"] = {
                "audited_candidate_selected": {"result": "pass", "reason": "Candidate is audit-eligible."},
                "candidate_lock_established": {"result": "pass", "reason": "Candidate lock is established."},
            }
        elif stage_id == "/build-tree":
            output["decision_input"]["selected_candidate_id"] = "ARCH-FAM-C"
            output["canonical_content"] = copy.deepcopy(BUILD_TREE)
            output["check_evidence"] = {
                "selected_candidate_preserved": {"result": "pass", "reason": "Candidate is preserved."},
                "canonical_build_tree_present": {"result": "pass", "reason": "Structured Build Tree is present."},
                "architecture_drift_absent": {"result": "pass", "reason": "No architecture drift."},
            }
        elif stage_id == "/implementation":
            output["decision_input"]["selected_candidate_id"] = "ARCH-FAM-C"
            output["canonical_content"] = {
                "approved_build_tree": copy.deepcopy(BUILD_TREE),
                "widgets": [{"node_id": "node-root", "widget": "container"}],
            }
            output["check_evidence"] = {
                "selected_candidate_preserved": {"result": "pass", "reason": "Candidate is preserved."},
                "canonical_implementation_present": {"result": "pass", "reason": "Structured implementation is present."},
                "approved_build_tree_preserved": {"result": "pass", "reason": "Approved tree is embedded."},
            }
        elif stage_id == "/final-audit":
            output["decision_input"]["selected_candidate_id"] = "ARCH-FAM-C"
            output["check_evidence"] = {
                "final_audit_acceptance": {"result": "pass", "reason": "No blocking finding."},
                "candidate_lock_preserved": {"result": "pass", "reason": "Candidate lock remains."},
                "implementation_fidelity_confirmed": {"result": "pass", "reason": "Implementation fidelity is confirmed."},
            }
        elif stage_id == "/handoff-export":
            output["decision_input"]["selected_candidate_id"] = "ARCH-FAM-C"
            output["check_evidence"] = {
                "handoff_eligibility": {"result": "pass", "reason": "Final Audit permits handoff."},
                "blocking_unknowns_absent": {"result": "pass", "reason": "No critical unknown remains."},
                "final_audit_preserved": {"result": "pass", "reason": "Final Audit is preserved."},
            }
        elif stage_id == "/project-gate-export":
            output["decision_input"]["selected_candidate_id"] = "ARCH-FAM-C"
            output["check_evidence"] = {}
            payload = json.loads((root / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json").read_text(encoding="utf-8"))
            payload["synthetic"] = False
            payload["payload_identity"]["synthetic_fixture_notice"] = "Unit-only non-production vector."
            output["project_gate_payload"] = payload
        outputs.append(output)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=ROOT / "fixtures/architect-quality-runtime/valid/full-pipeline.json")
    args = parser.parse_args()
    result = evaluate_run(load_outputs(args.run, ROOT), root=ROOT)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
