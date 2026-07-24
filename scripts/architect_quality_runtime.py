#!/usr/bin/env python3
"""Canonical public wrapper for the single Architect Runtime interface."""
from __future__ import annotations

from architect_quality_runtime import *  # noqa: F401,F403
from architect_project_gate_runtime_api import (  # noqa: F401
    ProjectGateFinalizationResult,
    finalize_project_gate,
)
