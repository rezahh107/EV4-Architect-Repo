"""G1 facade: payload assertions use the internal terminal execution value."""
from __future__ import annotations

import importlib

from _runtime_private_execution_projection import (
    evaluate_run_with_private_payload,
)

_legacy = importlib.import_module(
    "_legacy_architect_css_target_referential_integrity_g1"
)


def payload_with_valid_css() -> dict:
    items = _legacy.outputs()
    _legacy.specified_css(items[8]["canonical_content"], ["node-content"])
    outcome = evaluate_run_with_private_payload(
        _legacy.runtime,
        items,
        root=_legacy.REPO_ROOT,
        run_context=_legacy.context(),
        git_provider=_legacy.FixtureGitProvider(),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    return outcome["results"][-1]["project_gate_export"][
        "runtime_issued_payload"
    ]


_legacy.payload_with_valid_css = payload_with_valid_css
for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)
