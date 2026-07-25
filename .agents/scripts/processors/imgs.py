from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
HUMANS_DIR = ROOT.parent / ".humans"
VAULT_DIR = ROOT / "vaults" / "imgs"
OUTPUT_FILE = ROOT / "vaults" / "imgs.json"
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
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []

    if not HUMANS_DIR.exists():
        return moved

    for path in sorted(HUMANS_DIR.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        relative = path.relative_to(HUMANS_DIR)
        destination = VAULT_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            destination.unlink()

        shutil.move(str(path), str(destination))
        moved.append(relative.as_posix())

    return moved

def build_index() -> dict:
    items: list[str] = []
    if VAULT_DIR.exists():
        for path in VAULT_DIR.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            relative = quote(path.relative_to(VAULT_DIR).as_posix(), safe="/")
            items.append(relative)

    items.sort(key=str.lower)
    return {
        "updated_at": MAIN.utc_now(),
        "base_url": f"{MAIN.raw_base_url()}.agents/vaults/imgs/",
        "count": len(items),
        "items": items,
    }

def main() -> None:
    moved = move_images()
    payload = build_index()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Moved {len(moved)} image(s) into {VAULT_DIR.relative_to(ROOT)}")
    print(f"Indexed {payload['count']} image(s) in {OUTPUT_FILE.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
