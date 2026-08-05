from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_main():
    path = ROOT / "scripts" / "process.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MAIN = _load_main()


def build_api_registry_payload() -> dict:
    return {
        "updated_at": MAIN.utc_now(),
        "count": 1,
        "items": [
            {
                "id": MAIN.VAULT_ID,
                "path": f"api/{MAIN.VAULT_ID}/",
                "api": f"api/{MAIN.VAULT_ID}/index.json",
            }
        ],
    }


def main() -> None:
    MAIN.write_json(MAIN.API_ROOT_INDEX_JSON, build_api_registry_payload())


if __name__ == "__main__":
    main()
