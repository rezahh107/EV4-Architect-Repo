#!/usr/bin/env python3
"""Architect Stage Boundary Validation Transaction CLI."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from architect_validation_cli import *  # noqa: F401,F403,E402

if __name__ == "__main__":
    sys.exit(main())
