from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_main():
    path = ROOT / "scripts" / "process.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MAIN = _load_main()

CATEGORY_PATHS = {
    "project": MAIN.PROJECT_JSON,
    "story": MAIN.STORY_JSON,
    "creator": MAIN.CREATOR_JSON,
}


def render_project_markdown() -> str:
    config = MAIN.load_json(MAIN.CONFIG_JSON)
    lines = [
        "# Burnout Series",
        "",
        f"Creator: {config.get('creator', '')}",
        "",
        "## Summary",
        "",
        str(config.get("summary", "")).strip(),
        "",
        "## About",
        "",
        str(config.get("about", "")).strip(),
        "",
    ]
    contributors = config.get("contributors", [])
    if isinstance(contributors, list) and contributors:
        lines.extend(["## Contributors", ""])
        lines.extend([f"- {item}" for item in contributors if str(item).strip()])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def sync_human_sources() -> int:
    processed = 0
    for source in MAIN.humans_txt_files():
        stem = source.stem
        if stem.startswith(("creator-", "story-", "project-")):
            stem = stem.split("-", 1)[1]
        destination = MAIN.ABOUT_DIR / f"{stem}.md"
        destination.write_text(source.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")
        source.unlink()
        processed += 1
    return processed


def categorize(path: Path) -> str:
    stem = path.stem.lower()
    if stem in {"georgekary", "creator"} or stem.startswith("creator-"):
        return "creator"
    if stem in {"prologue", "epilogue", "story"} or stem.startswith("story-"):
        return "story"
    return "project"


def build_items(files: list[Path]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for path in sorted(files):
        text = path.read_text(encoding="utf-8").strip()
        items.append(
            {
                "id": path.stem,
                "excerpt": MAIN.build_excerpt(text),
                "file": path.name,
            }
        )
    return items


def build_payload(category: str, files: list[Path]) -> dict:
    return {
        "updated_at": MAIN.utc_now(),
        "category": category,
        "path": f"vaults/{MAIN.VAULT_ID}/about/",
        "count": len(files),
        "items": build_items(files),
    }


def main() -> None:
    MAIN.ensure_directories()
    sync_human_sources()
    project_markdown = MAIN.ABOUT_DIR / "project.md"
    project_markdown.write_text(render_project_markdown(), encoding="utf-8")

    categorized: dict[str, list[Path]] = {name: [] for name in MAIN.CATEGORY_NAMES}
    for path in sorted(MAIN.ABOUT_DIR.glob("*.md")):
        categorized[categorize(path)].append(path)

    for category, destination in CATEGORY_PATHS.items():
        MAIN.write_json(destination, build_payload(category, categorized[category]))


if __name__ == "__main__":
    main()
