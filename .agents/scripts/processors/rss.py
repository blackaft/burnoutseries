from __future__ import annotations

import html
import importlib.util
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

def _load_main() -> ModuleType:
    path = ROOT / "scripts" / "main.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MAIN = _load_main()

def fetch_rss() -> bytes:
    if MAIN.FEED_RSS.exists() and MAIN.FEED_RSS.read_text(encoding="utf-8").strip():
        print(f"Reading RSS from {MAIN.FEED_RSS.relative_to(ROOT)}")
        return MAIN.FEED_RSS.read_bytes()
    print(f"Fetching RSS from {MAIN.RSS_URL}")
    result = subprocess.run(["curl", "-fsSL", MAIN.RSS_URL], check=True, capture_output=True)
    MAIN.FEED_RSS.write_bytes(result.stdout)
    return result.stdout

def element_text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return html.unescape(element.text.strip())

def normalize_date(value: str) -> str:
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def normalize_excerpt(value: str) -> str:
    value = re.sub(r"^\[\s*\n\s*\]\s*\n+", "", value)
    value = re.sub(r"^\[\s*\]\s*", "", value)
    return value.strip()

def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    candidate = path.split("/")[-1].lower()
    slug = re.sub(r"[^a-z0-9-]+", "-", candidate)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise ValueError(f"Could not derive slug from URL: {url}")
    return slug

def youtube_url(source_url: str) -> str | None:
    parsed = urlparse(source_url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host == "youtu.be":
        video_id = parsed.path.strip("/")
        return f"https://www.youtube.com/watch?v={video_id}" if video_id else None
    if host not in {"youtube.com", "youtube-nocookie.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] in {"embed", "shorts", "live"}:
        return f"https://www.youtube.com/watch?v={parts[1]}"
    video_id = parse_qs(parsed.query).get("v", [""])[0]
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else None

class SimpleHTMLToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg", "noscript", "template"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "br":
            self.parts.append("\n")
        elif tag in {"p", "div", "section", "article", "header", "footer", "blockquote", "figure", "li", "h1", "h2", "h3", "h4", "h5", "h6", "hr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg", "noscript", "template"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in {"p", "div", "section", "article", "header", "footer", "blockquote", "figure", "li", "h1", "h2", "h3", "h4", "h5", "h6", "hr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = html.unescape(text)
        text = re.sub(r"\n\s+\n", "\n\n", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

def html_to_clean_markdown(content: str) -> str:
    parser = SimpleHTMLToMarkdown()
    parser.feed(content)
    return parser.get_text()

def parse_feed(xml_data: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_data)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS feed is missing its channel element")
    posts: list[dict[str, str]] = []
    for item in channel.findall("item"):
        title = element_text(item.find("title"))
        description = element_text(item.find("description"))
        url = element_text(item.find("link"))
        creator = element_text(item.find("dc:creator", NAMESPACES))
        published_raw = element_text(item.find("pubDate"))
        content_html = element_text(item.find("content:encoded", NAMESPACES))
        if not title or not url or not published_raw:
            print("Skipping RSS item missing title, URL or publication date", file=sys.stderr)
            continue
        try:
            published = normalize_date(published_raw)
            slug = slug_from_url(url)
        except (TypeError, ValueError) as error:
            print(f"Skipping invalid RSS item: {error}", file=sys.stderr)
            continue
        content = html_to_clean_markdown(content_html)
        excerpt = normalize_excerpt(content[:240])
        posts.append(
            {
                "slug": slug,
                "title": title,
                "description": description,
                "creator": creator,
                "published": published,
                "url": url,
                "excerpt": excerpt,
                "content": content,
            }
        )
    posts.sort(key=lambda post: post["published"], reverse=True)
    return posts

def empty_posts_index() -> dict[str, Any]:
    return {"updated_at": None, "latest": None, "count": 0, "items": []}

def load_existing_posts_json() -> dict[str, Any]:
    if not POSTS_JSON.exists():
        return empty_posts_index()
    try:
        raw = POSTS_JSON.read_text(encoding="utf-8").strip()
        if not raw:
            return empty_posts_index()
        payload = json.loads(raw)
    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not read existing posts.json: {error}", file=sys.stderr)
        return empty_posts_index()
    if not isinstance(payload, dict):
        print("Existing posts.json is not a JSON object; rebuilding", file=sys.stderr)
        return empty_posts_index()
    return payload

def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^a-z0-9-]+", "-", value.lower())
    return re.sub(r"-+", "-", value).strip("-")

def render_post(post: dict[str, str]) -> str:
    lines = [
        "---",
        f'id: {json.dumps(post["slug"], ensure_ascii=False)}',
        f'title: {json.dumps(post["title"], ensure_ascii=False)}',
        f'excerpt: {json.dumps(post["excerpt"], ensure_ascii=False)}',
        f'created_by: {json.dumps(post["creator"], ensure_ascii=False)}',
        f'published_at: {json.dumps(post["published"], ensure_ascii=False)}',
        f'substack_url: {json.dumps(post["url"], ensure_ascii=False)}',
        f'file: {json.dumps(post_filename(post), ensure_ascii=False)}',
        "---",
        "",
        post["content"],
        "",
    ]
    return "\n".join(lines).strip() + "\n"

def post_filename(post: dict[str, str]) -> str:
    published = datetime.fromisoformat(post["published"].replace("Z", "+00:00"))
    return f"{published.strftime('%Y%m%d')}-{sanitize_filename(post['slug'])}.md"

def merge_metadata(existing_index: dict[str, Any], feed_posts: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    existing_posts = existing_index.get("items", [])
    if isinstance(existing_posts, list):
        for post in existing_posts:
            if not isinstance(post, dict):
                continue
            post_id = str(post.get("id", "")).strip()
            if not post_id:
                continue
            merged[post_id] = {
                "id": post_id,
                "title": str(post.get("title", "")),
                "excerpt": str(post.get("excerpt", "")),
                "created_by": str(post.get("created_by", "")),
                "published_at": str(post.get("published_at", "")),
                "substack_url": str(post.get("substack_url", "")),
                "file": str(post.get("file", "")),
            }
    for post in feed_posts:
        post_path = post_filename(post)
        merged[post["slug"]] = {
            "id": post["slug"],
            "title": post["title"],
            "excerpt": post["excerpt"],
            "created_by": post["creator"],
            "published_at": post["published"],
            "substack_url": post["url"],
            "file": post_path,
        }
    return sorted(merged.values(), key=lambda post: post["published_at"], reverse=True)

def build_posts_json(metadata: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "updated_at": MAIN.utc_now(),
        "base_url": MAIN.vault_base_url("posts"),
        "latest": metadata[0]["id"] if metadata else None,
        "count": len(metadata),
        "items": metadata,
    }

def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_posts(feed_posts: list[dict[str, str]]) -> None:
    MAIN.POSTS_DIR.mkdir(parents=True, exist_ok=True)
    for post in feed_posts:
        (MAIN.POSTS_DIR / post_filename(post)).write_text(render_post(post), encoding="utf-8")

def main() -> None:
    existing_index = load_existing_posts_json()
    feed_posts = parse_feed(fetch_rss())
    metadata = merge_metadata(existing_index, feed_posts)
    write_posts(feed_posts)
    write_json(MAIN.POSTS_JSON, build_posts_json(metadata))
    print(f"Processed {len(feed_posts)} RSS item(s); indexed {len(metadata)} total post(s)")

if __name__ == "__main__":
    main()
