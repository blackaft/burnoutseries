from __future__ import annotations

import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as html_to_markdown

ROOT = Path(__file__).resolve().parents[2]
RSS_SOURCE = ROOT / "feed.rss"
POSTS_MD = ROOT / "posts.md"
POSTS_JSON = ROOT / "posts.json"
NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
START_MARKER = "<!-- post:{slug}:start -->"
END_MARKER = "<!-- post:{slug}:end -->"
POST_BLOCK_PATTERN = re.compile(
    r"<!-- post:(?P<slug>[a-z0-9-]+):start -->"
    r".*?"
    r"<!-- post:(?P=slug):end -->",
    re.DOTALL,
)

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

def read_source(path: Path) -> bytes:
    if not path.exists():
        raise FileNotFoundError(f"RSS source not found: {path}")

    data = path.read_bytes()

    if not data.strip():
        raise ValueError(f"RSS source is empty: {path}")

    # Remove UTF-8 BOM and any accidental whitespace before the XML declaration.
    data = data.lstrip(b"\xef\xbb\xbf \t\r\n")

    xml_start = data.find(b"<?xml")

    if xml_start > 0:
        data = data[xml_start:]

    preview = data[:100].lower()

    if preview.startswith(b"<!doctype html") or preview.startswith(b"<html"):
        raise ValueError(
            f"RSS source appears to be HTML, not RSS XML: {path}"
        )

    print(f"Reading RSS from {path.relative_to(ROOT)}")
    return data

def element_text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""

    return html.unescape(element.text.strip())

def normalize_date(value: str) -> str:
    parsed = parsedate_to_datetime(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return (
        parsed.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

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

        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

        return None

    if host not in {
        "youtube.com",
        "youtube-nocookie.com",
    }:
        return None

    parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if len(parts) >= 2 and parts[0] in {
        "embed",
        "shorts",
        "live",
    }:
        return f"https://www.youtube.com/watch?v={parts[1]}"

    video_id = parse_qs(parsed.query).get("v", [""])[0]

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    return None

def replace_youtube_embeds(soup: BeautifulSoup) -> None:
    for iframe in soup.find_all("iframe"):
        source_url = str(iframe.get("src", "")).strip()
        canonical_url = youtube_url(source_url)

        if not canonical_url:
            iframe.decompose()
            continue

        link = soup.new_tag(
            "a",
            href=canonical_url,
        )
        link.string = "Watch on YouTube"

        iframe.replace_with(link)

def remove_subscription_content(
    soup: BeautifulSoup,
) -> None:
    for form in soup.find_all("form"):
        form.decompose()

    selectors = (
        ".subscription-widget",
        ".subscribe-widget",
        ".subscribe-dialog",
        ".subscribe-cta",
        ".subscription-form",
        ".email-signup",
        ".email-signup-container",
        ".subscriber-only",
        "[data-component-name*='Subscribe']",
        "[data-component-name*='subscribe']",
        "[data-testid*='subscribe']",
        "[class*='subscription-widget']",
        "[class*='subscribe-widget']",
    )

    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()

def remove_related_posts(
    soup: BeautifulSoup,
) -> None:
    selectors = (
        ".related-posts",
        ".related-post",
        ".recommended-posts",
        ".recommendation-widget",
        ".post-preview",
        ".post-embed",
        "[data-component-name*='RelatedPost']",
        "[data-component-name*='related-post']",
        "[data-component-name*='PostPreview']",
        "[data-component-name*='post-preview']",
        "[data-testid*='related-post']",
        "[class*='related-post']",
        "[class*='recommended-post']",
    )

    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()

def remove_images(soup: BeautifulSoup) -> None:
    # Figures are treated as image content, including captions.
    for figure in soup.find_all("figure"):
        figure.decompose()

    selectors = (
        ".captioned-image-container",
        ".image2-inset",
        ".image-link-expand",
        ".image-container",
        ".image-caption",
        ".caption",
        "[class*='captioned-image']",
        "[class*='image-container']",
    )

    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()

    for element in soup.find_all(
        ["img", "picture", "source"]
    ):
        element.decompose()

    # Remove image links left empty after image removal.
    for anchor in soup.select("a.image-link"):
        if anchor.get_text(" ", strip=True):
            anchor.unwrap()
        else:
            anchor.decompose()

def flatten_buttons(soup: BeautifulSoup) -> None:
    for button in soup.find_all("button"):
        label = button.get_text(" ", strip=True)
        parent = button.parent

        if isinstance(parent, Tag) and parent.name == "a":
            if label:
                parent.clear()
                parent.string = label
            else:
                parent.decompose()

            continue

        href = str(
            button.get("href")
            or button.get("data-href")
            or button.get("data-url")
            or ""
        ).strip()

        if href and label:
            link = soup.new_tag("a", href=href)
            link.string = label
            button.replace_with(link)
        else:
            button.decompose()

def remove_non_content_elements(
    soup: BeautifulSoup,
) -> None:
    for element in soup.find_all(
        [
            "script",
            "style",
            "svg",
            "noscript",
            "template",
        ]
    ):
        element.decompose()

def normalize_markdown(value: str) -> str:
    value = value.replace("\xa0", " ")

    lines = [
        line.rstrip()
        for line in value.splitlines()
    ]
    value = "\n".join(lines)

    # Remove empty links occasionally left by removed embeds.
    value = re.sub(
        r"\[\s*\]\([^)]*\)",
        "",
        value,
    )

    # Remove lines containing only whitespace.
    value = re.sub(
        r"\n[ \t]+\n",
        "\n\n",
        value,
    )

    # Limit consecutive blank lines.
    value = re.sub(
        r"\n{3,}",
        "\n\n",
        value,
    )

    return value.strip()

def html_to_clean_markdown(content: str) -> str:
    soup = BeautifulSoup(
        content,
        "html.parser",
    )

    remove_non_content_elements(soup)

    # YouTube must be converted before generic iframe removal.
    replace_youtube_embeds(soup)

    remove_subscription_content(soup)
    remove_related_posts(soup)
    remove_images(soup)
    flatten_buttons(soup)

    markdown = html_to_markdown(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=[
            "iframe",
            "input",
            "textarea",
            "select",
        ],
    )

    return normalize_markdown(markdown)

def parse_feed(
    xml_data: bytes,
) -> list[dict[str, str]]:
    root = ET.fromstring(xml_data)
    channel = root.find("channel")

    if channel is None:
        raise ValueError(
            "RSS feed is missing its channel element"
        )

    posts: list[dict[str, str]] = []

    for item in channel.findall("item"):
        title = element_text(
            item.find("title")
        )
        description = element_text(
            item.find("description")
        )
        url = element_text(
            item.find("link")
        )
        creator = element_text(
            item.find("dc:creator", NAMESPACES)
        )
        published_raw = element_text(
            item.find("pubDate")
        )
        content_html = element_text(
            item.find("content:encoded", NAMESPACES)
        )

        if not title or not url or not published_raw:
            print(
                "Skipping RSS item missing title, "
                "URL or publication date",
                file=sys.stderr,
            )
            continue

        try:
            published = normalize_date(published_raw)
            slug = slug_from_url(url)
        except (TypeError, ValueError) as error:
            print(
                f"Skipping invalid RSS item: {error}",
                file=sys.stderr,
            )
            continue

        posts.append(
            {
                "slug": slug,
                "title": title,
                "description": description,
                "creator": creator,
                "published": published,
                "url": url,
                "content": html_to_clean_markdown(
                    content_html
                ),
            }
        )

    posts.sort(
        key=lambda post: post["published"],
        reverse=True,
    )

    return posts

def empty_posts_index() -> dict[str, Any]:
    return {
        "updated_at": None,
        "latest": None,
        "count": 0,
        "posts": [],
    }

def load_existing_posts_json() -> dict[str, Any]:
    if not POSTS_JSON.exists():
        return empty_posts_index()

    try:
        raw = POSTS_JSON.read_text(encoding="utf-8").strip()

        if not raw:
            return empty_posts_index()

        payload = json.loads(raw)

    except (json.JSONDecodeError, OSError) as error:
        print(
            f"Could not read existing posts.json: {error}",
            file=sys.stderr,
        )
        return empty_posts_index()

    if not isinstance(payload, dict):
        print(
            "Existing posts.json is not a JSON object; rebuilding",
            file=sys.stderr,
        )
        return empty_posts_index()

    return payload

def load_existing_markdown_blocks() -> dict[str, str]:
    if not POSTS_MD.exists():
        return {}

    try:
        content = POSTS_MD.read_text(
            encoding="utf-8"
        )
    except OSError as error:
        print(
            f"Could not read existing posts.md: {error}",
            file=sys.stderr,
        )
        return {}

    blocks: dict[str, str] = {}

    for match in POST_BLOCK_PATTERN.finditer(content):
        blocks[match.group("slug")] = (
            match.group(0).strip()
        )

    return blocks

def quote_frontmatter(value: str) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
    )

def render_post(post: dict[str, str]) -> str:
    slug = post["slug"]

    lines = [
        START_MARKER.format(slug=slug),
        "---",
        (
            "title: "
            f"{quote_frontmatter(post['title'])}"
        ),
        (
            "published: "
            f"{quote_frontmatter(post['published'])}"
        ),
        (
            "url: "
            f"{quote_frontmatter(post['url'])}"
        ),
        "---",
        "",
        post["content"],
        "",
        END_MARKER.format(slug=slug),
    ]

    return "\n".join(lines).strip()

def merge_metadata(
    existing_index: dict[str, Any],
    feed_posts: list[dict[str, str]],
) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}

    existing_posts = existing_index.get(
        "posts",
        [],
    )

    if isinstance(existing_posts, list):
        for post in existing_posts:
            if not isinstance(post, dict):
                continue

            slug = str(
                post.get("slug", "")
            ).strip()

            if not slug:
                continue

            merged[slug] = {
                "slug": slug,
                "title": str(
                    post.get("title", "")
                ),
                "creator": str(
                    post.get("creator", "")
                ),
                "published": str(
                    post.get("published", "")
                ),
                "url": str(
                    post.get("url", "")
                ),
            }

    for post in feed_posts:
        merged[post["slug"]] = {
            "slug": post["slug"],
            "title": post["title"],
            "creator": post["creator"],
            "published": post["published"],
            "url": post["url"],
        }

    return sorted(
        merged.values(),
        key=lambda post: post["published"],
        reverse=True,
    )

def build_posts_markdown(
    metadata: list[dict[str, str]],
    feed_posts: list[dict[str, str]],
    existing_blocks: dict[str, str],
) -> str:
    feed_by_slug = {
        post["slug"]: post
        for post in feed_posts
    }

    blocks: list[str] = []

    for item in metadata:
        slug = item["slug"]

        if slug in feed_by_slug:
            blocks.append(
                render_post(feed_by_slug[slug])
            )
            continue

        if slug in existing_blocks:
            blocks.append(
                existing_blocks[slug]
            )
            continue

        print(
            "Skipping historical post without "
            f"stored content: {slug}",
            file=sys.stderr,
        )

    header = "\n".join(
        [
            "# Burnout Series Posts",
            "",
            (
                "_Automatically generated from "
                f"[the publication RSS feed]({RSS_SOURCE})._"
            ),
        ]
    )

    if not blocks:
        return header + "\n"

    return (
        header
        + "\n\n"
        + "\n\n---\n\n".join(blocks)
        + "\n"
    )

def build_posts_json(
    metadata: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "updated_at": utc_now(),
        "latest": (
            metadata[0]["slug"]
            if metadata
            else None
        ),
        "count": len(metadata),
        "posts": metadata,
    }

def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

def main() -> None:
    existing_index = load_existing_posts_json()
    existing_blocks = (
        load_existing_markdown_blocks()
    )

    xml_data = read_source(RSS_SOURCE)
    feed_posts = parse_feed(xml_data)

    metadata = merge_metadata(
        existing_index,
        feed_posts,
    )

    markdown = build_posts_markdown(
        metadata,
        feed_posts,
        existing_blocks,
    )

    POSTS_MD.write_text(
        markdown,
        encoding="utf-8",
    )

    write_json(
        POSTS_JSON,
        build_posts_json(metadata),
    )

    print(
        f"Processed {len(feed_posts)} RSS item(s); "
        f"indexed {len(metadata)} total post(s)"
    )

if __name__ == "__main__":
    main()