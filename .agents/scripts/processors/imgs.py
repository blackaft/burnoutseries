from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_EXTENSIONS = {
    ".avif",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}

def _load_main():
    path = ROOT / "scripts" / "main.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MAIN = _load_main()

def move_images() -> list[str]:
    MAIN.IMGS_DIR.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []

    if not MAIN.HUMANS_DIR.exists():
        return moved

    for path in sorted(MAIN.HUMANS_DIR.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        relative = path.relative_to(MAIN.HUMANS_DIR)
        destination = MAIN.IMGS_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            destination.unlink()

        shutil.move(str(path), str(destination))
        moved.append(relative.as_posix())

    return moved

def build_index() -> dict:
    items: list[str] = []
    if MAIN.IMGS_DIR.exists():
        for path in MAIN.IMGS_DIR.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            relative = quote(path.relative_to(MAIN.IMGS_DIR).as_posix(), safe="/")
            items.append(relative)

    items.sort(key=str.lower)
    return {
        "updated_at": MAIN.utc_now(),
        "base_url": MAIN.vault_base_url("imgs"),
        "count": len(items),
        "items": items,
    }

def main() -> None:
    moved = move_images()
    payload = build_index()
    MAIN.IMGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    MAIN.IMGS_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Moved {len(moved)} image(s) into {MAIN.IMGS_DIR.relative_to(ROOT)}")
    print(f"Indexed {payload['count']} image(s) in {MAIN.IMGS_JSON.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
