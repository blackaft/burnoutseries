from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

def _load_main() -> ModuleType:
    path = ROOT / "scripts" / "main.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MAIN = _load_main()

MANIFEST_SECTION_FIELDS_DROP = {"updated_at", "base_url", "latest", "count"}
MANIFEST_ITEM_FIELDS_DROP = {"id", "created_by"}

def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload

def sanitize_manifest_section(payload: dict[str, Any], path: str) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    sanitized["path"] = f"{path}/"
    for key, value in payload.items():
        if key in MANIFEST_SECTION_FIELDS_DROP:
            continue
        if key == "items" and isinstance(value, list):
            sanitized["items"] = [
                {
                    item_key: item_value
                    for item_key, item_value in item.items()
                    if item_key not in MANIFEST_ITEM_FIELDS_DROP
                    and not (path == "about" and item_key == "published_at")
                    and not (path == "posts" and item_key in {"title", "published_at"})
                }
                if isinstance(item, dict)
                else item
                for item in value
            ]
            continue
        sanitized[key] = value
    return sanitized

def build_manifest() -> dict[str, Any]:
    return {
        "config": load_json(MAIN.CONFIG_JSON),
        "updated_at": MAIN.utc_now(),
        "base_url": MAIN.vault_base_url(),
        "posts": sanitize_manifest_section(load_json(MAIN.POSTS_JSON), "posts"),
        "about": sanitize_manifest_section(load_json(MAIN.ABOUT_JSON), "about"),
        "imgs": sanitize_manifest_section(load_json(MAIN.IMGS_JSON), "imgs"),
    }

def main() -> None:
    MAIN.MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    MAIN.MANIFEST_JSON.write_text(
        json.dumps(build_manifest(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
