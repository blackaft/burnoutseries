from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _load_main():
    path = ROOT / "scripts" / "main.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MAIN = _load_main()

def build_excerpt(source: Path, limit: int = 250) -> str:
    text = source.read_text(encoding="utf-8").strip()
    text = text.replace("\n\n", " ")
    text = " ".join(text.split())
    if len(text) <= limit:
        return text if text.endswith("...") else text[: max(0, limit - 3)] + "..."
    return text[: max(0, limit - 3)].rstrip() + "..."

def write_index(path: Path, items: list[dict[str, str]]) -> None:
    payload = {
        "updated_at": MAIN.utc_now(),
        "base_url": MAIN.vault_base_url("about" if path == MAIN.ABOUT_JSON else "excerpts"),
        "count": len(items),
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def scan_vault_items(directory: Path, prefix: str) -> list[dict[str, str]]:
    if not directory.exists():
        return []

    items: list[dict[str, str]] = []
    for source in sorted(directory.glob("*.md")):
        item_id = source.stem.replace(f"{prefix}-", "", 1) if source.stem.startswith(f"{prefix}-") else source.stem
        items.append(
            {
                "id": item_id,
                "excerpt": build_excerpt(source),
                "published_at": "2026-07-24T18:26:08Z",
                "file": source.name,
            }
        )
    return items

def main() -> None:
    MAIN.validate_sources()

    about_items = scan_vault_items(MAIN.ABOUT_DIR, "about")
    excerpt_items = scan_vault_items(MAIN.EXCERPTS_DIR, "excerpts")

    write_index(MAIN.ABOUT_JSON, about_items)
    write_index(MAIN.EXCERPTS_JSON, excerpt_items)

    print(f"Processed {len(about_items)} about txt file(s)")
    print(f"Processed {len(excerpt_items)} excerpt txt file(s)")

if __name__ == "__main__":
    main()
