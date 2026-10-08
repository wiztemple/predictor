"""Load config.yaml and resolve paths relative to the project root."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@lru_cache(maxsize=None)
def load_config(path: str | None = None) -> dict[str, Any]:
    with open(path or CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_env(path: Path | None = None) -> None:
    """Read KEY=value lines from the project's .env into os.environ (real env vars win).
    Kept dependency-free; quotes around values are stripped."""
    import os

    p = Path(path or PROJECT_ROOT / ".env")
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def project_path(relative: str) -> Path:
    return PROJECT_ROOT / relative


def season_codes(first: str, last: str) -> list[str]:
    """'1920', '2324' -> ['1920', '2021', '2122', '2223', '2324']."""
    start, end = int(first[:2]), int(last[:2])
    return [f"{y:02d}{(y + 1) % 100:02d}" for y in range(start, end + 1)]


def season_label(code: str) -> str:
    """'2526' -> '2025-26'."""
    return f"20{code[:2]}-{code[2:]}"


def season_of(date, start_month: int | None = None) -> str:
    """Football season label for a date: 2026-10-05 -> '2026-27' (seasons run Aug-Jul)."""
    if start_month is None:
        start_month = load_config()["football"]["season_start_month"]
    y = date.year if date.month >= start_month else date.year - 1
    return f"{y}-{(y + 1) % 100:02d}"
