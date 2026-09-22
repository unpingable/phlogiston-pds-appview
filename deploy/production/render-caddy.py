#!/usr/bin/env python3
"""Append the one bounded Phlogiston site block to a complete Caddyfile."""

from __future__ import annotations

import argparse
from pathlib import Path

BEGIN = "# BEGIN PHLOGISTON INERT V1"
END = "# END PHLOGISTON INERT V1"


def render(current: str, fragment: str) -> str:
    if BEGIN in current or END in current or "phlogiston.app" in current:
        raise ValueError("existing Phlogiston Caddy route or marker")
    return current.rstrip() + "\n\n" + BEGIN + "\n" + fragment.strip() + "\n" + END + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(render(args.current.read_text(), args.fragment.read_text()))


if __name__ == "__main__":
    main()
