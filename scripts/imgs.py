from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
IMGS_DIR = ROOT / "imgs"
OUTPUT_FILE = ROOT / "imgs.json"

SUPPORTED_EXTENSIONS = {
    ".avif",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value

def build_index() -> dict:
    owner = required_env("GITHUB_OWNER")
    repo = required_env("GITHUB_REPO")
    branch = required_env("GITHUB_BRANCH")

    base_url = (
        f"https://raw.githubusercontent.com/"
        f"{owner}/{repo}/{quote(branch, safe='')}/imgs/"
    )

    filenames: list[str] = []

    if IMGS_DIR.exists():
        for path in IMGS_DIR.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            relative_path = path.relative_to(IMGS_DIR).as_posix()
            filenames.append(quote(relative_path, safe="/"))

    filenames.sort(key=str.lower)

    return {
        "updated_at": utc_now(),
        "base_url": base_url,
        "count": len(filenames),
        "imgs": filenames,
    }

def main() -> None:
    payload = build_index()

    OUTPUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        f"Indexed {payload['count']} image(s) "
        f"from {IMGS_DIR.relative_to(ROOT)}"
    )
    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)}")

if __name__ == "__main__":
    main()