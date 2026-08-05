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


def build_vault_payload() -> dict:
    payload = MAIN.load_json(MAIN.CONFIG_JSON)
    payload.update(
        {
            "id": MAIN.VAULT_ID,
            "updated_at": MAIN.utc_now(),
            "base_url": MAIN.vault_base_url(),
        }
    )
    return payload


def main() -> None:
    MAIN.write_json(MAIN.VAULT_JSON, build_vault_payload())


if __name__ == "__main__":
    main()
