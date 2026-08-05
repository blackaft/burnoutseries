from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_processor():
    path = ROOT / "scripts" / "local" / "about.py"
    spec = importlib.util.spec_from_file_location("burnout_about", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load about processor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    _load_processor().main()


if __name__ == "__main__":
    main()
