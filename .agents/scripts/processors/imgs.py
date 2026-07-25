from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
HUMANS_DIR = ROOT.parent / ".humans"
VAULT_DIR = ROOT / "vaults" / "imgs"
OUTPUT_FILE = ROOT / "vaults" / "imgs.json"
RAW_BASE_URL = "https://raw.githubusercontent.com/blackaft/burnoutseries/dev/.agents/vaults/imgs/"
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


def repo_identity() -> tuple[str, str, str]:
    remote_url = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT.parent,
    ).stdout.strip()
    parsed = urlparse(remote_url)
    if parsed.scheme in {"http", "https", "ssh", "git"}:
        owner_repo = parsed.path.lstrip("/")
    else:
        owner_repo = remote_url.rsplit(":", 1)[-1]
    owner_repo = owner_repo.removesuffix(".git")
    owner, repo = owner_repo.split("/", 1)
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT.parent,
    ).stdout.strip() or "dev"
    return owner, repo, branch


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
        "updated_at": utc_now(),
        "base_url": RAW_BASE_URL,
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
