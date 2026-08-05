from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO_ROOT / ".agents"
HUMANS_DIR = REPO_ROOT / ".humans"
CONFIG_JSON = REPO_ROOT / "config.json"

VAULT_ID = "burnoutseries"
VAULTS_DIR = REPO_ROOT / "vaults"
VAULT_ROOT = VAULTS_DIR / VAULT_ID
API_ROOT = REPO_ROOT / "api"
API_DIR = API_ROOT / VAULT_ID
ABOUT_DIR = VAULT_ROOT / "about"
SUBSTACK_DIR = VAULT_ROOT / "substack"
SUBSTACK_ARTICLES_DIR = SUBSTACK_DIR / "articles"
SUBSTACK_IMGS_DIR = SUBSTACK_DIR / "imgs"

ABOUT_API_DIR = API_DIR / "about"
SUBSTACK_API_DIR = API_DIR / "substack"

PROJECT_JSON = ABOUT_API_DIR / "project.json"
STORY_JSON = ABOUT_API_DIR / "story.json"
CREATOR_JSON = ABOUT_API_DIR / "creator.json"
ARTICLES_JSON = SUBSTACK_API_DIR / "articles.json"
IMGS_JSON = SUBSTACK_API_DIR / "imgs.json"
API_ROOT_INDEX_JSON = API_ROOT / "index.json"
INDEX_JSON = API_DIR / "index.json"
FEED_RSS = SUBSTACK_DIR / "feed.rss"

RSS_URL = "https://burnoutseries.substack.com/feed.rss"
LOCAL_PROCESSORS_DIR = AGENTS_DIR / "scripts" / "local"
REMOTE_PROCESSORS_DIR = AGENTS_DIR / "scripts" / "remote"
IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
CATEGORY_NAMES = ("project", "story", "creator")


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
        check=False,
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


def vault_base_url() -> str:
    return f"{raw_base_url()}vaults/{VAULT_ID}/"


def api_base_url() -> str:
    return f"{raw_base_url()}api/{VAULT_ID}/"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ensure_directories() -> None:
    for path in (
        VAULT_ROOT,
        API_DIR,
        ABOUT_DIR,
        SUBSTACK_DIR,
        SUBSTACK_ARTICLES_DIR,
        SUBSTACK_IMGS_DIR,
        ABOUT_API_DIR,
        SUBSTACK_API_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def build_excerpt(text: str, limit: int = 240) -> str:
    normalized = text.replace("\r", "")
    normalized = re.sub(r"^#{1,6}\s*", "", normalized, flags=re.MULTILINE)
    normalized = normalized.replace("`", "")
    normalized = " ".join(normalized.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)].rstrip() + "..."


def humans_txt_files() -> list[Path]:
    if not HUMANS_DIR.exists():
        return []
    return sorted(path for path in HUMANS_DIR.glob("*.txt") if path.is_file())


def humans_image_files() -> list[Path]:
    if not HUMANS_DIR.exists():
        return []
    return sorted(
        path
        for path in HUMANS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def validate_sources() -> None:
    if not CONFIG_JSON.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_JSON}")


def validate_outputs(paths: Iterable[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing generated file: {path}")
        if path.suffix == ".json":
            load_json(path)


def load_processor(name: str) -> ModuleType:
    path = LOCAL_PROCESSORS_DIR / f"{name}.py"
    if not path.exists():
        path = REMOTE_PROCESSORS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"burnout_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load processor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_processors(names: Iterable[str]) -> None:
    for name in names:
        load_processor(name).main()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Burnout vault publisher")
    parser.add_argument(
        "processors",
        nargs="*",
        default=["vault", "about", "substack", "index"],
        help="Processor names to run in order",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate_sources()
    ensure_directories()
    run_processors(args.processors)
    validate_outputs(
        [
            API_ROOT_INDEX_JSON,
            PROJECT_JSON,
            STORY_JSON,
            CREATOR_JSON,
            ARTICLES_JSON,
            IMGS_JSON,
            INDEX_JSON,
        ]
    )


if __name__ == "__main__":
    main()
