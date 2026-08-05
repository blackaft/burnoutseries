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
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
IMAGE_CONTENT_TYPES = {
    "image/avif": ".avif",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

def _load_main() -> ModuleType:
    # Legacy note:
    # This old variant was wired to the pre-rename orchestrator at `main.py`.
    # The current script loads `process.py` after the scripts/ refactor.
    path = ROOT / "scripts" / "main.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MAIN = _load_main()

def fetch_rss() -> bytes:
    # Legacy note:
    # The old implementation kept curl in verbose mode (`-v`) for easier shell debugging.
    # The current script dropped that noise and returns `result.stdout` directly.
    print(f"Fetching RSS from {MAIN.RSS_URL}")
    result = subprocess.run(
        ["curl", "-v", "-fsSL", MAIN.RSS_URL],
        check=True,
        stdout=subprocess.PIPE,
    )
    MAIN.FEED_RSS.parent.mkdir(parents=True, exist_ok=True)
    MAIN.FEED_RSS.write_bytes(result.stdout)
    return MAIN.FEED_RSS.read_bytes()

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
    # Removed in the current script.
    # Excerpt cleanup is now delegated to `MAIN.build_excerpt(content)`, so the
    # excerpt rules live in one shared place instead of being duplicated here.
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
    # Removed in the current script.
    # This helper was not part of the active publication contract anymore, so the
    # newer file dropped it to keep the remote processor focused on RSS -> markdown
    # and image syncing only.
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

class FeedImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img":
            return
        attributes = dict(attrs)
        data_attrs = (attributes.get("data-attrs") or "").strip()
        if data_attrs:
            try:
                parsed_data_attrs = json.loads(html.unescape(data_attrs))
            except json.JSONDecodeError:
                parsed_data_attrs = {}
            src = str(parsed_data_attrs.get("src") or "").strip()
            if src:
                self.image_urls.append(html.unescape(src))
                return
        src = (attributes.get("src") or "").strip()
        if src:
            self.image_urls.append(html.unescape(src))

def unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique

def canonical_feed_image_url(url: str) -> str:
    parsed = urlparse(url)
    decoded_url = unquote(url)
    if parsed.netloc.lower().endswith("substackcdn.com"):
        nested_index = decoded_url.rfind("https://")
        if nested_index > 0:
            return decoded_url[nested_index:]
        nested_index = decoded_url.rfind("http://")
        if nested_index > 0:
            return decoded_url[nested_index:]
    return decoded_url

def extract_feed_image_urls(content_html: str) -> list[str]:
    parser = FeedImageParser()
    parser.feed(content_html)
    return unique_preserving_order(parser.image_urls)

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
        enclosure = item.find("enclosure")
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
        # Legacy shape:
        # this processor kept a richer in-memory post object (`slug`, `description`,
        # `creator`, `published`, `url`) and translated it later.
        # The current script normalizes to the final API field names here
        # (`id`, `created_by`, `published_at`, `substack_url`, `file`) so there is
        # less reshaping later in the pipeline.
        image_urls: list[str] = []
        if enclosure is not None and enclosure.attrib.get("url") and str(enclosure.attrib.get("type", "")).startswith("image/"):
            image_urls.append(enclosure.attrib["url"].strip())
        image_urls.extend(extract_feed_image_urls(content_html))
        canonical_image_urls = unique_preserving_order(
            [canonical_feed_image_url(image_url) for image_url in image_urls]
        )
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
                "image_urls": canonical_image_urls,
            }
        )
    posts.sort(key=lambda post: post["published"], reverse=True)
    return posts

def empty_posts_index() -> dict[str, Any]:
    # Removed in the current script.
    # The old flow merged fresh feed items with an existing posts index so older
    # metadata could survive incremental runs. The current script instead treats
    # the article markdown files under the vault as the reusable source of truth
    # when `VAULT_USE_EXISTING_SUBSTACK=1`.
    return {"updated_at": None, "latest": None, "count": 0, "items": []}

def load_existing_posts_json() -> dict[str, Any]:
    # Removed in the current script.
    # This was tied to the legacy `.agents/vaults/posts.json` contract. The newer
    # processor no longer reads an old posts index as input; it either parses RSS
    # or rehydrates from existing markdown files already stored in the vault.
    if not MAIN.POSTS_JSON.exists():
        return empty_posts_index()
    try:
        raw = MAIN.POSTS_JSON.read_text(encoding="utf-8").strip()
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
    # Removed in the current script.
    # This merge step existed because the old processor preserved and updated a
    # standalone posts index across runs. The newer script builds the API payload
    # directly from the current post set or from the already-written markdown
    # articles, so there is no separate metadata merge layer.
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
    # Legacy output contract:
    # this wrote the older posts index with `base_url` under `.agents/vaults/posts/`.
    # The current script writes `api/.../articles.json` and stores repo-relative
    # content paths there instead of section-local base URLs.
    return {
        "updated_at": MAIN.utc_now(),
        "base_url": MAIN.vault_base_url("posts"),
        "latest": metadata[0]["id"] if metadata else None,
        "count": len(metadata),
        "items": metadata,
    }

def write_json(path: Path, payload: dict[str, Any]) -> None:
    # Kept in spirit, but not as a standalone helper in the current file.
    # JSON writes now go through `MAIN.write_json(...)` so the write behavior is
    # shared across processors.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def load_existing_imgs_json() -> dict[str, Any]:
    # Removed in the current script.
    # The legacy image sync relied on an existing imgs index to know which files
    # it managed. The current script just inspects the target images directory
    # itself and removes stale files from there.
    if not MAIN.IMGS_JSON.exists():
        return {"items": []}
    try:
        raw = MAIN.IMGS_JSON.read_text(encoding="utf-8").strip()
        if not raw:
            return {"items": []}
        payload = json.loads(raw)
    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not read existing imgs.json: {error}", file=sys.stderr)
        return {"items": []}
    return payload if isinstance(payload, dict) else {"items": []}

def image_extension(url: str, content_type: str) -> str:
    parsed = urlparse(url)
    suffix = Path(unquote(parsed.path)).suffix.lower()
    if suffix in IMAGE_CONTENT_TYPES.values():
        return suffix
    content_type = content_type.split(";", 1)[0].strip().lower()
    if content_type in IMAGE_CONTENT_TYPES:
        return IMAGE_CONTENT_TYPES[content_type]
    raise ValueError(f"Unsupported image type for {url}: {content_type or 'unknown'}")

def download_image(url: str, filename_stem: str) -> tuple[str, bytes]:
    # Minor implementation change in the current script:
    # the user-agent string was updated from `burnout-rss-processor` to
    # `burnout-vault-processor` to reflect the broader vault-oriented contract.
    request = Request(url, headers={"User-Agent": "burnout-rss-processor/1.0"})
    with urlopen(request) as response:
        content = response.read()
        extension = image_extension(url, response.headers.get_content_type())
    filename = f"{sanitize_filename(filename_stem)}{extension}"
    return filename, content

def image_filename_stem(post_slug: str, image_index: int) -> str:
    if image_index == 1:
        return f"{post_slug}-featured"
    return f"{post_slug}-{image_index - 1}"

def build_imgs_json(items: list[str]) -> dict[str, Any]:
    # Legacy output contract:
    # this produced the old image index with `base_url` under `.agents/vaults/imgs/`.
    # The current script writes `api/.../imgs.json` with repo-relative content
    # paths instead.
    sorted_items = sorted(items, key=str.lower)
    return {
        "updated_at": MAIN.utc_now(),
        "base_url": MAIN.vault_base_url("imgs"),
        "count": len(sorted_items),
        "items": [quote(item, safe="/") for item in sorted_items],
    }

def sync_feed_images(feed_posts: list[dict[str, Any]]) -> tuple[int, dict[str, Any]]:
    # Legacy behavior:
    # this function both synchronized files and returned the next imgs payload.
    # The current script splits those concerns: file sync happens here, while the
    # API payload is built separately from the directory contents.
    MAIN.IMGS_DIR.mkdir(parents=True, exist_ok=True)
    existing_index = load_existing_imgs_json()
    managed_files = {
        str(item)
        for item in existing_index.get("items", [])
        if isinstance(item, str) and item.strip()
    }
    url_to_filename: dict[str, str] = {}
    desired_files: list[str] = []
    reserved_filenames: set[str] = set()
    downloaded_count = 0

    for post in feed_posts:
        for index, image_url in enumerate(post.get("image_urls", []), start=1):
            if image_url in url_to_filename:
                desired_files.append(url_to_filename[image_url])
                continue

            filename_stem = image_filename_stem(post["slug"], index)
            filename, content = download_image(image_url, filename_stem)
            candidate = Path(filename)
            collision_index = 2
            while candidate.name in reserved_filenames:
                candidate = Path(f"{sanitize_filename(filename_stem)}-{collision_index}{candidate.suffix}")
                collision_index += 1

            destination = MAIN.IMGS_DIR / candidate.name
            destination.write_bytes(content)
            url_to_filename[image_url] = candidate.name
            reserved_filenames.add(candidate.name)
            desired_files.append(candidate.name)
            downloaded_count += 1

    desired_set = set(desired_files)
    for stale in managed_files - desired_set:
        stale_path = MAIN.IMGS_DIR / unquote(stale)
        if stale_path.exists():
            stale_path.unlink()

    return downloaded_count, build_imgs_json(unique_preserving_order(desired_files))

def write_posts(feed_posts: list[dict[str, str]]) -> None:
    # Kept conceptually, but renamed in the current script to `write_articles(...)`
    # because the output now belongs to the Substack article surface rather than
    # the older `.agents/vaults/posts/` contract.
    MAIN.POSTS_DIR.mkdir(parents=True, exist_ok=True)
    for post in feed_posts:
        (MAIN.POSTS_DIR / post_filename(post)).write_text(render_post(post), encoding="utf-8")

def main() -> None:
    # Legacy orchestration:
    # this path always fetched RSS, merged against legacy JSON indexes, wrote
    # markdown, and then rewrote both posts/imgs indexes.
    # The current script is narrower:
    # - it can reuse existing vault markdown via `VAULT_USE_EXISTING_SUBSTACK=1`
    # - it writes to the newer API JSON outputs instead of the old vault indexes
    # - it does not preserve a separate merge layer for historical metadata
    existing_index = load_existing_posts_json()
    feed_posts = parse_feed(fetch_rss())
    metadata = merge_metadata(existing_index, feed_posts)
    write_posts(feed_posts)
    downloaded_images, imgs_payload = sync_feed_images(feed_posts)
    write_json(MAIN.POSTS_JSON, build_posts_json(metadata))
    write_json(MAIN.IMGS_JSON, imgs_payload)
    print(f"Processed {len(feed_posts)} RSS item(s); indexed {len(metadata)} total post(s)")
    print(f"Downloaded {downloaded_images} feed image(s); indexed {imgs_payload['count']} total image(s)")

if __name__ == "__main__":
    main()
