#!/usr/bin/env python3
"""
Sync dependencies and remove enum34.

This script runs `uv sync` and then removes enum34 (which is incorrectly
pulled in by pvporcupine via realtimestt but breaks pyinstaller on Python 3.10+).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run uv sync and remove enum34."""
    project_root = Path(__file__).resolve().parents[1]
    
    # Run uv sync
    print("Running uv sync...")
    sync_result = subprocess.run(
        ["uv", "sync"],
        cwd=project_root,
    )
    if sync_result.returncode != 0:
        print("ERROR: uv sync failed", file=sys.stderr)
        return sync_result.returncode
    
    # Remove enum34
    print("\nRemoving enum34...")
    remove_result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "remove_enum34.py")],
        cwd=project_root,
    )
    
    return remove_result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

