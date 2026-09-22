"""Admission check: the synthetic compose job accepts only an immutable image digest."""

from __future__ import annotations

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from phlogiston_appview.deploy_validate import validate_image


if __name__ == "__main__":
    try:
        print(validate_image(sys.argv[1]))
    except (IndexError, ValueError) as error:
        raise SystemExit(str(error)) from error
