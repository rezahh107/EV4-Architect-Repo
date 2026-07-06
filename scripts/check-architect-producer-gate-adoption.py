#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_CONTRACT_SHA = "c556bb9deeccdcafeb885a1c8b3dbd660e4e06f452b8ac3c7040d21377465fcc"
EXPECTED_STAGE_BUNDLE_SHA = "fc1ec6d3f7aecbabaeb0a3455d9eb42788779d2fa1531e8c7b2cb3bde706a886"
PROJECT_GATE_COMMIT = "ea19c22c32458068e167b267da8b819e9263cdf7"
ARCHITECT_REPOSITORY = "rezahh107/EV4-Architect-Repo"
CLASS_RE = re.compile(r"^[a-z][a-z0-9-]*(?:__[a-z0-9-]+)?(?:--[a-z0-9-]+)?$")
VAGUE_LABELS = {"box", "box-1", "left", "right", "wrapper", "container", "visual"}
ORDER = {"error": 0, "warning": 1, "info": 2}

@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    path: str = "$"
    def key(self) -> tuple[str, int, str, str]:
        return (self.path, ORDER.get(self.severity, 99), self.code, self.message)
    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "severity": self.severity, "message": self.message, "path": self.path}

def D(code: str, severity: str, message: str, path: str = "$") -> Diagnostic:
    return Diagnostic(code, severity, message, path)

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {path}")
    if isinstance(value, dict):
        for key in sorted(value):
            reject_non_finite(value[key], f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_non_finite(item, f"{path}[{index}]")

def canonical_json_hash(value: Any) -> str:
    reject_non_finite(value)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def tokens(path: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in path.split(".") if part]

def set_path(value: dict[str, Any], path: str, new_value: Any) -> None:
    cur: Any = value
    parts = tokens(path)
    for part in parts[:-1]: cur = cur[part]
    cur[parts[-1]] = new_value

def delete_path(value: dict[str, Any], path: str) -> None:
    cur: Any = value
    parts = tokens(path)
    for part in parts[:-1]: cur = cur[part]
    del cur[parts[-1]]

def apply_mutations(base: dict[str, Any], mutations: list[dict[str, Any]]) -> dict[str, Any]:
    value = copy.deepcopy(base)
    for mutation in mutations:
        op = mutation["op"]
        if op == "set": set_path(value, mutation["path"], mutation["value"])
        elif op == "delete": delete_path(value, mutation["path"])
        elif op == "delete_index":
            cur: Any = value
            for part in tokens(mutation["path"]): cur = cur[part]
            del cur[mutation["index"]]
        else: raise ValueError(f"Unsupported mutation op: {op}")
    return value

class AdoptionValidator:
    def __init__(self, repo_root: str | Path = ".") -> None:
        self.root = Path(repo_root)
    def validate_all(self) -> dict[str, Any]:
        diagnostics: list[Diagnostic] = []
        diagnostics += self.validate_common_contracts()
        diagnostics += self.validate_manifest(read_json(self.root / "manifests/architect-pipeline-manifest.v1.json"))
        diagnostics += self.validate_build_tree(read_json(self.root / "fixtures/build-tree/valid/voice-assistant-reference.v1.json"))
        diagnostics += self.validate_build_tree_cases()
        diagnostics += self.validate_export(read_json(self.root / "fixtures/project-gate-export/valid/blocked-run.v1.json"))
        diagnostics += self.validate_export_cases()
        diagnostics += self.validate_capability_registry()
        diagnostics += self.validate_behavioral_coverage()
        ordered = sorted(diagnostics, key=lambda d: d.key())
        return {"schema_version":"architect-producer-gate-adoption-validation-result.v1","status":"failed" if any(d.severity == "error" for d in ordered) else "passed","diagnostics":[d.to_dict() for d in ordered]}
    def validate_common_contracts(self) -> list[Diagnostic]:
        d: list[Diagnostic] = []
        if sha256_file(self.root / "contracts/project-gate/producer-gate-export.v1.schema.json") != EXPECTED_CONTRACT_SHA:
            d.append(D("A_PG_CONTRACT_BYTE_MISMATCH", "error", "Vendored Producer Gate Export bytes differ from Prompt 0."))
        if sha256_file(self.root / "contracts/project-gate/stage-bundle.v1.schema.json") != EXPECTED_STAGE_BUNDLE_SHA:
            d.append(D("A_STAGE_BUNDLE_BYTE_MISMATCH", "error", "Stage Bundle supplementary copy differs from Prompt 0."))
        lock = read_json(self.root / "contracts/project-gate/producer-gate-export.v1.lock.json")
        if lock.get("lock_schema") != "project-gate-common-contract-lock.v1": d.append(D("A_PG_LOCK_SCHEMA_MISMATCH", "error", "Wrong lock schema.", "$.lock_schema"))
        if lock.get("contract_id") != "producer-gate-export.v1": d.append(D("A_PG_LOCK_CONTRACT_ID_MISMATCH", "error", "Lock must apply to producer-gate-export.v1.", "$.contract_id"))
        if lock.get("canonical", {}).get("commit_sha") != PROJECT_GATE_COMMIT: d.append(D("A_PG_LOCK_MOVING_REF", "error", "Project Gate pin must be immutable Prompt 0 merge commit.", "$.canonical.commit_sha"))
        if lock.get("verification", {}).get("compare_against_moving_default_branch") is not False: d.append(D("A_PG_LOCK_MOVING_DEFAULT_FORBIDDEN", "error", "Moving default branch comparison is forbidden."))
        return d
    def validate_manifest(self, manifest: dict[str, Any]) -> list[Diagnostic]:
        d: list[Diagnostic] = []
        stages = manifest.get("project_execution_stages", [])
        ids = [s.get("stage_id") for s in stages]
        ords = [s.get("ordinal") for s in stages]
        if len(ids) != len(set(ids)): d.append(D("A_MANIFEST_DUPLICATE_STAGE_ID", "error", "Stage IDs must be unique."))
        if len(ords) != len(set(ords)): d.append(D("A_MANIFEST_DUPLICATE_ORDINAL", "error", "Stage ordinals must be unique."))
        if ords != sorted(ords): d.append(D("A_MANIFEST_OUT_OF_ORDER", "error", "Stage ordinals must be sorted."))
        if not stages or stages[-1].get("stage_id") != "/project-gate-export": d.append(D("A_MANIFEST_FINAL_EXPORT_MISSING", "error", "Final stage must be /project-gate-export."))
        declared = set(ids)
        for stage in stages:
            if stage.get("mandatory") and not stage.get("required_outputs"): d.append(D("A_MANIFEST_MANDATORY_OUTPUT_MISSING", "error", "Mandatory stages require outputs."))
            if stage.get("next_stage") is not None and stage.get("next_stage") not in declared: d.append(D("A_MANIFEST_NEXT_STAGE_UNDECLARED", "error", "next_stage is undeclared."))
        legacy = {item.get("output_id") for item in manifest.get("legacy_compatibility_outputs", [])}
        if not {"/handoff-export", "/builder-feed-export"}.issubset(legacy): d.append(D("A_MANIFEST_LEGACY_OUTPUT_NOT_PRESERVED", "error", "Legacy outputs must remain declared."))
        return d
    def validate_build_tree(self, tree: dict[str, Any]) -> list[Diagnostic]:
        d: list[Diagnostic] = []
        if tree.get("fixture_type") == "approved_reference_example" and tree.get("real_elementor_export") is not False: d.append(D("A_TREE_SYNTHETIC_LABELED_REAL", "error", "Synthetic fixture cannot be labeled real."))
        payload = tree.get("Build_Tree_Payload") if isinstance(tree.get("Build_Tree_Payload"), dict) else {}
        if payload.get("user_summary_only") is True or payload.get("machine_artifact_complete") is not True: d.append(D("A_TREE_SUMMARY_REPLACED_MACHINE_ARTIFACT", "error", "Summary cannot replace machine artifact."))
        nodes = payload.get("nodes", [])
        by_id: dict[str, dict[str, Any]] = {}
        for i, node in enumerate(nodes):
            node_id = node.get("node_id")
            if node_id in by_id: d.append(D("A_TREE_DUPLICATE_NODE_ID", "error", "Duplicate node_id.", f"$.nodes[{i}].node_id"))
            if isinstance(node_id, str): by_id[node_id] = node
        root = payload.get("root_node_id")
        if root not in by_id: d.append(D("A_TREE_MISSING_ROOT", "error", "root_node_id must exist."))
        for i, node in enumerate(nodes):
            nid = node.get("node_id"); parent = node.get("parent_node_id")
            if parent is not None and parent not in by_id: d.append(D("A_TREE_ORPHAN_NODE", "error", "parent_node_id must exist.", f"$.nodes[{i}].parent_node_id"))
            if str(node.get("structure_label", "")).lower() in VAGUE_LABELS: d.append(D("A_TREE_VAGUE_STRUCTURE_LABEL", "error", "Structure label is vague."))
            if node.get("class_name") and not CLASS_RE.fullmatch(node["class_name"]): d.append(D("A_TREE_INVALID_CLASS_NAME", "error", "Invalid class name."))
            if node.get("meaningful") is True and node.get("content_carrier") in {"static_svg", "static_html"}: d.append(D("A_TREE_MEANINGFUL_CONTENT_STATIC_CARRIER", "error", "Meaningful content trapped in static carrier."))
            if i == 0 and "unknowns" in node and not node.get("unknowns"): d.append(D("A_TREE_UNKNOWN_DROPPED", "error", "Root unknowns were dropped."))
            if "responsive_structural_intent" not in node: d.append(D("A_TREE_RESPONSIVE_CONTRACT_MISSING", "error", "Responsive structural intent missing."))
        for start in sorted(by_id):
            seen: set[str] = set(); cur = start
            while cur in by_id:
                if cur in seen: d.append(D("A_TREE_CYCLE", "error", "Tree contains cycle.")); break
                seen.add(cur); cur = by_id[cur].get("parent_node_id")
        source_roles = set(payload.get("required_source_roles", []))
        coverage = payload.get("semantic_role_coverage", [])
        covered = {item.get("source_role_id") for item in coverage}
        if source_roles - covered: d.append(D("A_TREE_MISSING_SOURCE_ROLE", "error", "Source role coverage missing."))
        for item in coverage:
            if item.get("disposition") == "authorized_composite" and not item.get("authorization_ref"): d.append(D("A_TREE_UNAUTHORIZED_ROLE_COLLAPSE", "error", "Composite role needs authorization."))
        return d
    def validate_build_tree_cases(self) -> list[Diagnostic]:
        suite: list[Diagnostic] = []
        cases = read_json(self.root / "fixtures/build-tree/invalid/cases.v1.json")
        base = read_json((self.root / "fixtures/build-tree/invalid" / cases["base_fixture"]).resolve())
        for case in cases["cases"]:
            codes = {diag.code for diag in self.validate_build_tree(apply_mutations(base, case.get("mutations", [])))}
            if case["expected_diagnostic"] not in codes: suite.append(D("A_TREE_INVALID_FIXTURE_NOT_REJECTED", "error", case["case_id"]))
        return suite
    def validate_export(self, export: dict[str, Any]) -> list[Diagnostic]:
        d: list[Diagnostic] = []
        if export.get("export_id") == "builder-feed-export": d.append(D("A_EXPORT_LEGACY_FEED_MISLABELED", "error", "Legacy builder feed mislabeled."))
        if export.get("schema_version") != "producer-gate-export.v1": d.append(D("A_EXPORT_WRONG_SCHEMA_VERSION", "error", "Wrong export schema."))
        if export.get("producer", {}).get("stage") != "architect" or export.get("final_stage_bundle", {}).get("stage") != "architect": d.append(D("A_EXPORT_FINAL_BUNDLE_STAGE_MISMATCH", "error", "Final bundle stage mismatch."))
        if export.get("final_stage_bundle", {}).get("payload_schema", {}).get("owner_repository") != ARCHITECT_REPOSITORY: d.append(D("A_EXPORT_PAYLOAD_OWNER_MISMATCH", "error", "Payload owner mismatch."))
        if export.get("acquisition_mode", {}).get("silent_fallback_allowed") is not False: d.append(D("A_EXPORT_SILENT_FALLBACK_FORBIDDEN", "error", "Silent fallback forbidden."))
        if export.get("handoff", {}).get("allowed") is True and export.get("handoff", {}).get("blocking_diagnostics"): d.append(D("A_EXPORT_HANDOFF_ALLOWED_WITH_BLOCKER", "error", "Allowed handoff has blockers."))
        return d
    def validate_export_cases(self) -> list[Diagnostic]:
        suite: list[Diagnostic] = []
        cases = read_json(self.root / "fixtures/project-gate-export/invalid/cases.v1.json")
        base = read_json((self.root / "fixtures/project-gate-export/invalid" / cases["base_fixture"]).resolve())
        for case in cases["cases"]:
            codes = {diag.code for diag in self.validate_export(apply_mutations(base, case.get("mutations", [])))}
            if case["expected_diagnostic"] not in codes: suite.append(D("A_EXPORT_INVALID_FIXTURE_NOT_REJECTED", "error", case["case_id"]))
        return suite
    def validate_capability_registry(self) -> list[Diagnostic]:
        d: list[Diagnostic] = []
        registry = read_json(self.root / "references/ELEMENTOR_V4_OFFICIAL_CAPABILITY_REGISTRY.v1.json")
        for i, feature in enumerate(registry.get("capabilities", [])):
            if not str(feature.get("official_source", "")).startswith("https://elementor.com/"): d.append(D("A_CAPABILITY_SOURCE_NOT_OFFICIAL", "error", "Official Elementor source required.", f"$.capabilities[{i}].official_source"))
            if not feature.get("architect_must_not_assume"): d.append(D("A_CAPABILITY_PROJECT_USE_NOT_SEPARATED", "error", "Must separate platform support from project use."))
        return d
    def validate_behavioral_coverage(self) -> list[Diagnostic]:
        text = (self.root / "docs/BEHAVIORAL_RULE_COVERAGE_PROMPT_01.md").read_text(encoding="utf-8")
        return [] if all(f"A-R{n:02d}" in text for n in range(13, 31)) else [D("A_COVERAGE_RULE_MISSING", "error", "Missing Prompt 01 coverage rule.")]

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", default=Path.cwd()); parser.add_argument("--format", choices=["text", "json"], default="text"); args = parser.parse_args(argv)
    result = AdoptionValidator(args.repo_root).validate_all()
    if args.format == "json": print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        for diag in result["diagnostics"]: print(f"{diag['severity']}: {diag['code']} {diag['path']} {diag['message']}")
        print(f"status: {result['status']}")
    return 0 if result["status"] == "passed" else 1
if __name__ == "__main__": raise SystemExit(main())
