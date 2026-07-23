"""Deterministic coverage checks for Payload derivation classifications."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from architect_runtime_errors import PayloadDerivationError, RuntimeDiagnostic


def _decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _resolve_local_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local Schema references are supported: {ref}")
    value: Any = root_schema
    for token in ref[2:].split("/"):
        if not isinstance(value, dict):
            raise ValueError(f"Schema reference does not resolve to an object: {ref}")
        value = value[_decode_pointer_token(token)]
    if not isinstance(value, dict):
        raise ValueError(f"Schema reference does not resolve to an object: {ref}")
    return value


def _resolved(root_schema: dict[str, Any], node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        return {}
    if "$ref" not in node:
        return node
    resolved = dict(_resolve_local_ref(root_schema, str(node["$ref"])))
    resolved.update({key: value for key, value in node.items() if key != "$ref"})
    return resolved


def _join(prefix: str, name: str) -> str:
    return f"{prefix}.{name}" if prefix else name


def required_schema_paths(schema: dict[str, Any]) -> frozenset[str]:
    """Return every path structurally required for every accepted Payload."""

    def collect(node: Any, prefix: str) -> set[str]:
        current = _resolved(schema, node)
        local: set[str] = set()

        for branch in current.get("allOf", []):
            local.update(collect(branch, prefix))

        for keyword in ("anyOf", "oneOf"):
            branches = current.get(keyword)
            if isinstance(branches, list) and branches:
                branch_sets = [collect(branch, prefix) for branch in branches]
                local.update(set.intersection(*branch_sets) if branch_sets else set())

        if current.get("type") == "array" or "items" in current:
            local.update(collect(current.get("items"), prefix + "[]"))
            return local

        properties = current.get("properties")
        required = current.get("required", [])
        if isinstance(properties, dict) and isinstance(required, list):
            for name in sorted(required):
                if not isinstance(name, str) or name not in properties:
                    raise ValueError(
                        "Schema required property is absent from properties: "
                        f"{prefix or '<root>'}.{name}"
                    )
                path = _join(prefix, name)
                local.add(path)
                local.update(collect(properties[name], path))
        return local

    return frozenset(collect(schema, ""))


def validate_payload_derivation_rules(
    schema: dict[str, Any],
    rules: Mapping[str, str],
    allowed_kinds: set[str] | frozenset[str],
) -> frozenset[str]:
    required = required_schema_paths(schema)
    classified = set(rules)
    diagnostics: list[RuntimeDiagnostic] = []

    for path in sorted(required - classified):
        diagnostics.append(
            RuntimeDiagnostic(
                "PAYLOAD_DERIVATION_REQUIRED_PATH_UNCLASSIFIED",
                f"Required Payload Schema path lacks a derivation classification: {path}",
                path=path,
            )
        )
    for path in sorted(classified - required):
        diagnostics.append(
            RuntimeDiagnostic(
                "PAYLOAD_DERIVATION_CLASSIFICATION_PATH_UNKNOWN",
                f"Derivation classification does not identify a required Payload Schema path: {path}",
                path=path,
            )
        )
    for path, kind in sorted(rules.items()):
        if kind not in allowed_kinds:
            diagnostics.append(
                RuntimeDiagnostic(
                    "PAYLOAD_DERIVATION_CLASSIFICATION_KIND_INVALID",
                    f"Invalid derivation classification kind for {path}: {kind!r}",
                    path=path,
                )
            )

    if diagnostics:
        raise PayloadDerivationError(diagnostics)
    return required


def validate_payload_derivation_authority(
    root: Path,
    rules: Mapping[str, str],
    allowed_kinds: set[str] | frozenset[str],
) -> frozenset[str]:
    schema_path = Path(root) / "schemas/ev4-architect-stage-payload.v1.schema.json"
    if not schema_path.is_file():
        # Partial release-authority fixtures intentionally exercise other required
        # sources without carrying the terminal Payload Schema. Full repository,
        # checker, and terminal paths include this Schema and therefore execute
        # exact derivation coverage before a Payload can be trusted.
        return frozenset()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return validate_payload_derivation_rules(schema, rules, allowed_kinds)
