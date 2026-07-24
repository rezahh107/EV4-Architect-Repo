"""Compatibility-free workflow alias for the canonical Stage claim guard.

The active implementation remains ``architect_stage_claim_guard``. This file
exists only because historical workflow paths used the longer Runtime-prefixed
name; it contains no evaluator or authority logic.
"""
from architect_stage_claim_guard import *  # noqa: F401,F403
