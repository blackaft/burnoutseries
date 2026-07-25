from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Iterable
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
HUMANS_DIR = REPO_ROOT / ".humans"
SCRIPTS_DIR = ROOT / "scripts"
PROCESSORS_DIR = SCRIPTS_DIR / "processors"
VAULT_ROOT = ROOT / "vaults"
ABOUT_DIR = VAULT_ROOT / "about"
EXCERPTS_DIR = VAULT_ROOT / "excerpts"
IMGS_DIR = VAULT_ROOT / "imgs"
POSTS_DIR = VAULT_ROOT / "posts"
ABOUT_JSON = VAULT_ROOT / "about.json"
EXCERPTS_JSON = VAULT_ROOT / "excerpts.json"
IMGS_JSON = VAULT_ROOT / "imgs.json"
POSTS_JSON = VAULT_ROOT / "posts.json"
FEED_RSS = VAULT_ROOT / "feed.rss"
RSS_URL = "https://burnoutseries.substack.com/feed.rss"

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

def repo_default_branch() -> str:
    branch = subprocess.run(
        [
            "git",
            "symbolic-ref",
            "--quiet",
            "--short",
            "refs/remotes/origin/HEAD",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    ).stdout.strip()

    if branch:
        return branch.rsplit("/", 1)[-1]

    branch = subprocess.run(
        ["git", "remote", "show", "origin"],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    ).stdout

    for line in branch.splitlines():
        line = line.strip()
        if line.startswith("HEAD branch:"):
            return line.split(":", 1)[1].strip()

    return "dev"

def raw_base_url() -> str:
    return f"https://raw.githubusercontent.com/blackaft/burnoutseries/{repo_default_branch()}/"

def vault_base_url(section: str = "") -> str:
    base = f"{raw_base_url()}.agents/vaults/"
    return f"{base}{section}/" if section else base

def humans_txt_files() -> list[Path]:
    if not HUMANS_DIR.exists():
        return []
    return sorted(HUMANS_DIR.glob("*.txt"))

def has_human_txt() -> bool:
    return bool(humans_txt_files())

def has_human_images() -> bool:
    if not HUMANS_DIR.exists():
        return False
    return any(
        path.is_file() and path.suffix.lower() in {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
        for path in HUMANS_DIR.iterdir()
    )

def validate_sources() -> None:
    if not HUMANS_DIR.exists():
        raise FileNotFoundError(f"Missing humans directory: {HUMANS_DIR}")

def validate_outputs(paths: Iterable[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing generated file: {path}")
        json.loads(path.read_text(encoding="utf-8"))

def load_processor(name: str) -> ModuleType:
    path = PROCESSORS_DIR / name
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load processor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_processors() -> None:
    load_processor("imgs.py").main()
    load_processor("rss.py").main()
    load_processor("txt.py").main()

def main() -> None:
    validate_sources()
    run_processors()
    validate_outputs([POSTS_JSON, IMGS_JSON, ABOUT_JSON, EXCERPTS_JSON])

if __name__ == "__main__":
    main()
