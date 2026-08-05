from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
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


def _load_main():
    path = ROOT / "scripts" / "process.py"
    spec = importlib.util.spec_from_file_location("burnout_main", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load main orchestrator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MAIN = _load_main()


def normalize_date(value: str) -> str:
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    candidate = path.split("/")[-1].lower()
    slug = re.sub(r"[^a-z0-9-]+", "-", candidate)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise ValueError(f"Could not derive slug from URL: {url}")
    return slug


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^a-z0-9-]+", "-", value.lower())
    return re.sub(r"-+", "-", value).strip("-")


def post_filename(post: dict[str, str]) -> str:
    published = datetime.fromisoformat(post["published_at"].replace("Z", "+00:00"))
    return f"{published.strftime('%Y%m%d')}-{sanitize_filename(post['id'])}.md"


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
        text = html.unescape("".join(self.parts))
        text = re.sub(r"\n\s+\n", "\n\n", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


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
        if value and value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def canonical_feed_image_url(url: str) -> str:
    parsed = urlparse(url)
    decoded_url = unquote(url)
    if parsed.netloc.lower().endswith("substackcdn.com"):
        for marker in ("https://", "http://"):
            nested_index = decoded_url.rfind(marker)
            if nested_index > 0:
                return decoded_url[nested_index:]
    return decoded_url


def extract_feed_image_urls(content_html: str) -> list[str]:
    parser = FeedImageParser()
    parser.feed(content_html)
    return unique_preserving_order(parser.image_urls)


def html_to_clean_markdown(content: str) -> str:
    parser = SimpleHTMLToMarkdown()
    parser.feed(content)
    return parser.get_text()


def fetch_rss() -> bytes:
    result = subprocess.run(
        ["curl", "-fsSL", MAIN.RSS_URL],
        check=True,
        stdout=subprocess.PIPE,
    )
    MAIN.FEED_RSS.parent.mkdir(parents=True, exist_ok=True)
    MAIN.FEED_RSS.write_bytes(result.stdout)
    return result.stdout


def element_text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return html.unescape(element.text.strip())


def parse_feed(xml_data: bytes) -> list[dict[str, object]]:
    root = ET.fromstring(xml_data)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS feed is missing its channel element")

    posts: list[dict[str, object]] = []
    for item in channel.findall("item"):
        title = element_text(item.find("title"))
        url = element_text(item.find("link"))
        creator = element_text(item.find("dc:creator", NAMESPACES))
        published_raw = element_text(item.find("pubDate"))
        content_html = element_text(item.find("content:encoded", NAMESPACES))
        enclosure = item.find("enclosure")
        if not title or not url or not published_raw:
            continue

        try:
            published_at = normalize_date(published_raw)
            slug = slug_from_url(url)
        except (TypeError, ValueError) as error:
            print(f"Skipping invalid RSS item: {error}", file=sys.stderr)
            continue

        content = html_to_clean_markdown(content_html)
        image_urls: list[str] = []
        if enclosure is not None and enclosure.attrib.get("url") and str(enclosure.attrib.get("type", "")).startswith("image/"):
            image_urls.append(enclosure.attrib["url"].strip())
        image_urls.extend(extract_feed_image_urls(content_html))

        posts.append(
            {
                "id": slug,
                "title": title,
                "excerpt": MAIN.build_excerpt(content),
                "created_by": creator,
                "published_at": published_at,
                "substack_url": url,
                "file": post_filename({"id": slug, "published_at": published_at}),
                "content": content,
                "image_urls": unique_preserving_order(
                    [canonical_feed_image_url(value) for value in image_urls]
                ),
            }
        )

    posts.sort(key=lambda post: str(post["published_at"]), reverse=True)
    return posts


def render_post(post: dict[str, object]) -> str:
    lines = [
        "---",
        f'id: {json.dumps(post["id"], ensure_ascii=False)}',
        f'title: {json.dumps(post["title"], ensure_ascii=False)}',
        f'excerpt: {json.dumps(post["excerpt"], ensure_ascii=False)}',
        f'created_by: {json.dumps(post["created_by"], ensure_ascii=False)}',
        f'published_at: {json.dumps(post["published_at"], ensure_ascii=False)}',
        f'substack_url: {json.dumps(post["substack_url"], ensure_ascii=False)}',
        f'file: {json.dumps(post["file"], ensure_ascii=False)}',
        "---",
        "",
        str(post["content"]).strip(),
        "",
    ]
    return "\n".join(lines)


def write_articles(posts: list[dict[str, object]]) -> None:
    MAIN.SUBSTACK_ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    for post in posts:
        (MAIN.SUBSTACK_ARTICLES_DIR / str(post["file"])).write_text(
            render_post(post),
            encoding="utf-8",
        )


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        return {}, raw.strip()
    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, raw.strip()
    frontmatter, content = parts
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines()[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = json.loads(value.strip())
    return metadata, content.strip()


def load_articles_from_existing() -> list[dict[str, object]]:
    posts: list[dict[str, object]] = []
    for path in sorted(MAIN.SUBSTACK_ARTICLES_DIR.glob("*.md")):
        metadata, content = parse_frontmatter(path)
        if not metadata:
            continue
        metadata.setdefault("file", path.name)
        metadata.setdefault("excerpt", MAIN.build_excerpt(content))
        posts.append(metadata)
    posts.sort(key=lambda post: str(post.get("published_at", "")), reverse=True)
    return posts


def build_articles_payload(posts: list[dict[str, object]]) -> dict:
    return {
        "updated_at": MAIN.utc_now(),
        "path": f"vaults/{MAIN.VAULT_ID}/substack/articles/",
        "latest": posts[0]["id"] if posts else None,
        "count": len(posts),
        "items": [
            {
                "id": str(post.get("id", "")),
                "title": str(post.get("title", "")),
                "excerpt": str(post.get("excerpt", "")),
                "created_by": str(post.get("created_by", "")),
                "published_at": str(post.get("published_at", "")),
                "substack_url": str(post.get("substack_url", "")),
                "file": str(post.get("file", "")),
            }
            for post in posts
        ],
    }


def build_imgs_payload() -> dict:
    items = sorted(path.name for path in MAIN.SUBSTACK_IMGS_DIR.iterdir() if path.is_file())
    return {
        "updated_at": MAIN.utc_now(),
        "path": f"vaults/{MAIN.VAULT_ID}/substack/imgs/",
        "count": len(items),
        "items": [quote(item, safe="/") for item in items],
    }


def image_extension(url: str, content_type: str) -> str:
    suffix = Path(unquote(urlparse(url).path)).suffix.lower()
    if suffix in IMAGE_CONTENT_TYPES.values():
        return suffix
    content_type = content_type.split(";", 1)[0].strip().lower()
    if content_type in IMAGE_CONTENT_TYPES:
        return IMAGE_CONTENT_TYPES[content_type]
    raise ValueError(f"Unsupported image type for {url}: {content_type or 'unknown'}")


def image_filename_stem(post_slug: str, image_index: int) -> str:
    if image_index == 1:
        return f"{post_slug}-featured"
    return f"{post_slug}-{image_index - 1}"


def download_image(url: str, filename_stem: str) -> tuple[str, bytes]:
    request = Request(url, headers={"User-Agent": "burnout-vault-processor/1.0"})
    with urlopen(request) as response:
        content = response.read()
        extension = image_extension(url, response.headers.get_content_type())
    filename = f"{sanitize_filename(filename_stem)}{extension}"
    return filename, content


def sync_feed_images(posts: list[dict[str, object]]) -> None:
    MAIN.SUBSTACK_IMGS_DIR.mkdir(parents=True, exist_ok=True)
    desired: set[str] = set()
    reserved: set[str] = set()

    for post in posts:
        for index, image_url in enumerate(post.get("image_urls", []), start=1):
            filename, content = download_image(str(image_url), image_filename_stem(str(post["id"]), index))
            candidate = Path(filename)
            collision_index = 2
            while candidate.name in reserved:
                candidate = Path(f"{candidate.stem}-{collision_index}{candidate.suffix}")
                collision_index += 1
            (MAIN.SUBSTACK_IMGS_DIR / candidate.name).write_bytes(content)
            reserved.add(candidate.name)
            desired.add(candidate.name)

    for stale in MAIN.SUBSTACK_IMGS_DIR.iterdir():
        if stale.is_file() and stale.name not in desired:
            stale.unlink()


def main() -> None:
    MAIN.ensure_directories()
    use_existing = os.getenv("VAULT_USE_EXISTING_SUBSTACK") == "1"
    if use_existing:
        posts = load_articles_from_existing()
    else:
        posts = parse_feed(fetch_rss())
        write_articles(posts)
        sync_feed_images(posts)

    MAIN.write_json(MAIN.ARTICLES_JSON, build_articles_payload(posts))
    MAIN.write_json(MAIN.IMGS_JSON, build_imgs_payload())


if __name__ == "__main__":
    main()
