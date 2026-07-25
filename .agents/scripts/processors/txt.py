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

def source_to_markdown(source: Path) -> str:
    text = source.read_text(encoding="utf-8").strip()
    return text + "\n" if text else "\n"

def target_dir(source: Path) -> Path:
    if source.name.startswith("about-"):
        return MAIN.ABOUT_DIR
    if source.name.startswith("excerpts-"):
        return MAIN.EXCERPTS_DIR
    raise ValueError(f"Unsupported TXT source: {source.name}")

def process_human_sources() -> tuple[int, int]:
    about_count = 0
    excerpts_count = 0

    for source in MAIN.humans_txt_files():
        destination_dir = target_dir(source)
        destination_dir.mkdir(parents=True, exist_ok=True)
        file_id = source.stem.split("-", 1)[1] if "-" in source.stem else source.stem
        destination = destination_dir / f"{file_id}.md"
        destination.write_text(source_to_markdown(source), encoding="utf-8")

        if destination_dir == MAIN.ABOUT_DIR:
            about_count += 1
        if destination_dir == MAIN.EXCERPTS_DIR:
            excerpts_count += 1

    return about_count, excerpts_count

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

    processed_about, processed_excerpts = process_human_sources()
    about_items = scan_vault_items(MAIN.ABOUT_DIR, "about")
    excerpt_items = scan_vault_items(MAIN.EXCERPTS_DIR, "excerpts")

    write_index(MAIN.ABOUT_JSON, about_items)
    write_index(MAIN.EXCERPTS_JSON, excerpt_items)

    print(f"Processed {processed_about} about txt source file(s)")
    print(f"Processed {processed_excerpts} excerpt txt source file(s)")
    print(f"Indexed {len(about_items)} about vault file(s)")
    print(f"Indexed {len(excerpt_items)} excerpt vault file(s)")

if __name__ == "__main__":
    main()
