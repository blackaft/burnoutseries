# Burnout Series — Manifest, Substack, and TXT Update

Date: 2026-07-30

## Purpose

Capture the product and implementation decisions made during the July 30, 2026 session so future agents can understand the current processor, manifest, and vault behavior without re-deriving it from diffs.

## Final Decisions

### TXT ingestion

- `.humans/*.txt` is now treated as about-material intake only.
- TXT source filenames no longer require `about-` or `excerpts-` prefixes.
- Processed TXT files are converted into `.md` files under `.agents/vaults/about/`.
- The output markdown filename uses the source stem as-is.
- Once the target markdown file is confirmed to exist, the original `.txt` file is deleted from `.humans/`.

### Excerpts deprecation

- `.agents/vaults/excerpts.json` is deprecated.
- The orchestrator no longer validates or requires `excerpts.json`.
- `manifest.json` no longer embeds an `excerpts` section.
- Existing `.agents/vaults/excerpts/` content may still exist on disk, but it is no longer part of the active generated JSON surface.

### Manifest simplification

- `manifest.json` should be a lean navigation index, not a duplicate of the full vault indexes.
- The top-level manifest still includes:
  - `config`
  - `updated_at`
  - `base_url`
- Embedded `posts`, `about`, and `imgs` sections now expose:
  - `path`
  - `items`
- Embedded section `base_url` values were replaced by `path` so consumers append `posts/`, `about/`, or `imgs/` to the manifest-level `base_url`.
- Embedded section metadata such as `updated_at`, `count`, and `latest` was removed from the manifest payload.

### Manifest item simplification

- Embedded `posts` items now expose only:
  - `excerpt`
  - `file`
- Embedded `about` items now expose only:
  - `excerpt`
  - `file`
- Embedded `imgs` items remain filename strings.
- The following fields are intentionally not exposed inside the embedded manifest items anymore:
  - `id`
  - `created_by`
  - `substack_url`
  - `title`
  - `published_at`

### Substack processor

- The active RSS processor was renamed from `rss.py` to `substack.py`.
- `substack.py` is now the processor responsible for:
  - fetching the Substack RSS feed
  - caching the feed under `.agents/vaults/feed.rss`
  - generating per-post markdown files under `.agents/vaults/posts/`
  - regenerating `posts.json`
  - discovering feed-linked images
  - downloading those images into `.agents/vaults/imgs/`
  - regenerating `imgs.json`
- `imgs.py` was removed from the active orchestrator path and is now deprecated.

### Feed image rules

- Feed image discovery should use Substack RSS item data plus the rendered post HTML in `content:encoded`.
- The processor should prefer canonical origin image URLs rather than treating different Substack CDN resize URLs as distinct images.
- The first distinct image for a post is saved as:
  - `{post-slug}-featured.{ext}`
- Additional distinct images for the same post are saved as:
  - `{post-slug}-1.{ext}`
  - `{post-slug}-2.{ext}`
  - and so on
- The image extension should prefer the canonical source URL suffix, not only the CDN response content type.
- This matters because Substack CDN may return `image/jpeg` while the underlying source asset is actually `.png` or `.webp`.

## Current Processor Architecture

- `.agents/scripts/main.py` orchestrates:
  - `substack.py`
  - `txt.py`
  - `manifest.py`
- There is no longer an active `imgs.py` step in `main.py`.

## Current Vault Behavior

- `posts.json` remains the fuller index for posts.
- `about.json` remains the fuller index for about material.
- `imgs.json` remains the fuller index for images.
- `manifest.json` is intentionally slimmer than those source indexes.
- `manifest.json` should be treated as the primary AI entrypoint.

## Validation Notes

The following behaviors were verified during the session:

- TXT processing writes markdown into `.agents/vaults/about/` and deletes the original `.txt` after successful creation.
- `main.py` runs without requiring `excerpts.json`.
- `manifest.json` now emits `path` instead of repeated section-level `base_url` values.
- `substack.py` downloads image files using source-based extensions such as `.png` and `.webp`.
- The duplicate `-featured` / `-1` issue was resolved by canonicalizing Substack CDN URLs to their underlying source asset URLs before deduplication.

## Important Contracts For Future Sessions

- Do not reintroduce prefix-based TXT routing unless the product direction explicitly changes.
- Do not reintroduce `excerpts.json` into the live pipeline unless the manifest, orchestrator, and companion surfaces are updated together.
- Keep `manifest.json` lean; avoid turning it back into a full mirror of the source indexes.
- Keep `substack.py` as the single source of truth for Substack posts and feed-derived images.
- If feed image handling changes again, dedupe must happen on canonical source assets, not on CDN resize URLs.
