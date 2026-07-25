from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HUMANS_DIR = ROOT.parent / ".humans"
VAULT_ROOT = ROOT / "vaults"
ABOUT_DIR = VAULT_ROOT / "about"
EXCERPTS_DIR = VAULT_ROOT / "excerpts"
ABOUT_JSON = VAULT_ROOT / "about.json"
EXCERPTS_JSON = VAULT_ROOT / "excerpts.json"

def _load_main():
    path = ROOT / "scripts" / "main.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MAIN = _load_main()

def source_to_markdown(source: Path) -> str:
    text = source.read_text(encoding="utf-8").strip()
    return text + "\n" if text else "\n"

def build_excerpt(source: Path, limit: int = 250) -> str:
    text = source_to_markdown(source).strip()
    text = text.replace("\n\n", " ")
    text = " ".join(text.split())
    if len(text) <= limit:
        return text if text.endswith("...") else text[: max(0, limit - 3)] + "..."
    return text[: max(0, limit - 3)].rstrip() + "..."

def target_dir(source: Path) -> Path:
    if source.name.startswith("about-"):
        return ABOUT_DIR
    if source.name.startswith("excerpts-"):
        return EXCERPTS_DIR
    raise ValueError(f"Unsupported TXT source: {source.name}")

def build_item(source: Path, md_path: Path) -> dict[str, str]:
    if source.name.startswith("about-"):
        return {
            "id": source.stem.replace("about-", "", 1) or source.stem,
            "excerpt": build_excerpt(source),
            "published_at": "2026-07-24T18:26:08Z",
            "file": md_path.name,
        }
    return {
        "id": source.stem.replace("excerpts-", "", 1) or source.stem,
        "excerpt": build_excerpt(source),
        "published_at": "2026-07-24T18:26:08Z",
        "file": md_path.name,
    }

def write_index(path: Path, items: list[dict[str, str]]) -> None:
    payload = {
        "updated_at": MAIN.utc_now(),
        "base_url": (
            f"{MAIN.raw_base_url()}.agents/vaults/about/"
            if path == ABOUT_JSON
            else f"{MAIN.raw_base_url()}.agents/vaults/excerpts/"
        ),
        "count": len(items),
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def process_file(source: Path) -> dict[str, dict[str, str]]:
    destination_dir = target_dir(source)
    destination_dir.mkdir(parents=True, exist_ok=True)
    file_id = source.stem.split("-", 1)[1] if "-" in source.stem else source.stem
    destination = destination_dir / f"{file_id}.md"
    excerpt = source_to_markdown(source)
    destination.write_text(excerpt, encoding="utf-8")
    item = build_item(source, destination)
    return {
        "about": item if destination_dir == ABOUT_DIR else {},
        "excerpts": item if destination_dir == EXCERPTS_DIR else {},
    }

def main() -> None:
    MAIN.validate_sources()

    about_items: list[dict[str, str]] = []
    excerpt_items: list[dict[str, str]] = []

    for source in MAIN.humans_txt_files():
        item = process_file(source)
        if item["about"]:
            about_items.append(item["about"])
        if item["excerpts"]:
            excerpt_items.append(item["excerpts"])

    write_index(ABOUT_JSON, about_items)
    write_index(EXCERPTS_JSON, excerpt_items)

    print(f"Processed {len(about_items)} about txt file(s)")
    print(f"Processed {len(excerpt_items)} excerpt txt file(s)")

if __name__ == "__main__":
    main()
