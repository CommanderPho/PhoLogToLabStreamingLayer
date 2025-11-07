#!/usr/bin/env python3
"""
Remove enum34 package if installed.

enum34 is only needed for Python < 3.4, but pvporcupine (via realtimestt) declares it.
This breaks pyinstaller and isn't needed for Python 3.10+.
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Uninstall enum34 if present."""
    try:
        # Try uv pip first, fall back to pip
        try:
            result = subprocess.run(
                ["uv", "pip", "uninstall", "enum34"],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            # Fall back to pip if uv is not available
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "enum34"],
                capture_output=True,
                text=True,
            )
        if result.returncode == 0:
            if "WARNING: Skipping enum34" in result.stdout or "not installed" in result.stdout.lower():
                print("enum34 is not installed (or already removed)")
            else:
                print("Successfully removed enum34")
        else:
            # enum34 might not be installed, which is fine
            if "not installed" in result.stderr.lower() or "not installed" in result.stdout.lower():
                print("enum34 is not installed")
                return 0
            print(f"Warning: Failed to remove enum34: {result.stderr}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error removing enum34: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

