#!/usr/bin/env python3
"""
Switch the [tool.uv.sources] section in pyproject.toml between dev and release presets.

Usage:
  python scripts/switch_uv_sources.py --mode dev
  python scripts/switch_uv_sources.py --mode release

By default, only updates specific keys inside [tool.uv.sources] (preserving
other entries):
  - whisper-timestamped
  - phopylslhelper
The values for these keys are taken from the corresponding fragment in
templating/pyproject_template_*.toml_fragment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
TEMPLATING_DIR = PROJECT_ROOT / "templating"

DEV_FRAGMENT = TEMPLATING_DIR / "pyproject_template_dev.toml_fragment"
RELEASE_FRAGMENT = TEMPLATING_DIR / "pyproject_template_release.toml_fragment"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def find_section_bounds(lines: list[str], header: str) -> tuple[int, int] | None:
    """Return (start_idx, end_idx) lines to replace for the given header.

    The end index is exclusive and is computed as the next '['-header line
    after the header, or len(lines) if none exists.
    """
    header_line = header.strip()
    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == header_line:
            start_idx = i
            break
    if start_idx == -1:
        return None

    # Find the next section header (a line whose first non-space char is '[')
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        stripped = lines[j].lstrip()
        if stripped.startswith("[") and stripped.rstrip().endswith("]"):
            end_idx = j
            break
    return (start_idx, end_idx)


def parse_fragment_kv_lines(fragment_text: str) -> dict[str, str]:
    """Extract key = { ... } assignment lines from a fragment, skipping the header.

    Returns a mapping from key -> full line (without trailing newline).
    """
    result: dict[str, str] = {}
    for raw in fragment_text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "[tool.uv.sources]":
            continue
        # Expect lines like: key = { ... }
        if "=" in stripped:
            key_part = stripped.split("=", 1)[0].strip()
            result[key_part] = line
    return result


def detect_section_indent(lines: list[str], start_idx: int, end_idx: int) -> str:
    """Infer indentation used for entries inside the section.

    Finds the first non-empty, non-comment line after header and returns its
    leading whitespace. Defaults to empty string if none found.
    """
    for i in range(start_idx + 1, end_idx):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        leading_ws = line[: len(line) - len(line.lstrip())]
        return leading_ws
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Switch [tool.uv.sources] in pyproject.toml")
    parser.add_argument(
        "--mode",
        choices=["dev", "release"],
        required=True,
        help="Which sources fragment to apply",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=PYPROJECT_PATH,
        help="Path to pyproject.toml (default: project root pyproject.toml)",
    )
    args = parser.parse_args(argv)

    fragment_path = DEV_FRAGMENT if args.mode == "dev" else RELEASE_FRAGMENT

    if not args.pyproject.exists():
        print(f"ERROR: {args.pyproject} does not exist", file=sys.stderr)
        return 1
    if not fragment_path.exists():
        print(f"ERROR: fragment not found: {fragment_path}", file=sys.stderr)
        return 1

    py_text = read_text(args.pyproject)
    frag_text = read_text(fragment_path).rstrip("\n") + "\n"
    frag_kv = parse_fragment_kv_lines(frag_text)
    target_keys = ["whisper-timestamped", "phopylslhelper"]

    lines = py_text.splitlines(keepends=True)
    bounds = find_section_bounds(lines, "[tool.uv.sources]")

    if bounds is None:
        # If section is missing, append header + the specific key lines
        header = "[tool.uv.sources]\n"
        # Build body from available fragment key lines for target_keys
        body_lines = []
        for key in target_keys:
            if key in frag_kv:
                body_lines.append(frag_kv[key] + "\n")
        section_text = header + "".join(body_lines)
        if not py_text.endswith("\n\n"):
            if py_text.endswith("\n"):
                py_text += "\n"
            else:
                py_text += "\n\n"
        new_text = py_text + section_text
    else:
        start_idx, end_idx = bounds
        indent = detect_section_indent(lines, start_idx, end_idx)

        # Build a mapping of current key -> (line_index)
        key_to_idx: dict[str, int] = {}
        for i in range(start_idx + 1, end_idx):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key_part = stripped.split("=", 1)[0].strip()
                key_to_idx[key_part] = i

        # Prepare updates for target keys from fragment
        for key in target_keys:
            if key not in frag_kv:
                continue
            new_line = indent + frag_kv[key] + "\n"
            if key in key_to_idx:
                # Replace existing line at same location
                i = key_to_idx[key]
                lines[i] = new_line
            else:
                # Insert before end_idx (right before the next section header)
                lines.insert(end_idx, new_line)
                end_idx += 1  # section grows by one line

        new_text = "".join(lines)

    # Backup existing file
    backup_path = args.pyproject.with_suffix(args.pyproject.suffix + ".bak")
    write_text(backup_path, py_text)
    write_text(args.pyproject, new_text)

    print(f"Updated [tool.uv.sources] keys ({', '.join(target_keys)}) -> {args.mode}"
          f" (backup saved to {backup_path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


