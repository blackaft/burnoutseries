# Burnout Series Knowledge Base

## Product Requirements Document (v1)

---

# Overview

The Burnout Series knowledge base is a GitHub-native publishing pipeline that compiles the Substack publication into structured assets consumable by a Custom GPT.

No backend, database or CMS is required. GitHub acts as both the source repository and the publishing platform.

The knowledge base is distributed as static files and accessed by the GPT through simple HTTP GET requests.

---

# Objectives

- Keep the GPT knowledge base automatically up to date.
- Compile new Substack posts into LLM-friendly Markdown.
- Preserve historical posts beyond the RSS feed window.
- Maintain an index of repository images.
- Run entirely from GitHub Actions.
- Keep the architecture reusable for future knowledge bases.

---

# Repository Structure

```text
.github/
├── scripts/
│   ├── imgs.py
│   └── rss.py
└── workflows/
    └── publish.yml

docs/
├── imgs.schema.json
├── posts.schema.json
└── rss.sample.txt

imgs/

about.txt
imgs.json
posts.json
posts.md

requirements.txt
README.md
```

---

# Knowledge Files

## about.txt

Maintained manually.

Contains stable project information including:

- project overview
- writing style
- GPT instructions
- permanent context

This file is never modified automatically.

---

## posts.md

Generated automatically.

Contains the complete publication corpus.

Each post contains minimal frontmatter.

```md
---
title: "..."
published: "..."
url: "..."
---

Article body...
```

Content is compiled into clean Markdown.

The compiler removes:

- images
- image captions
- subscription forms
- related post widgets

The compiler converts:

- HTML → Markdown
- YouTube embeds → Markdown links
- buttons → plain Markdown links

---

## posts.json

Generated automatically.

Provides lightweight metadata used for discovery.

```json
{
  "updated_at": "...",
  "latest": "...",
  "count": 12,
  "posts": [
    {
      "slug": "...",
      "title": "...",
      "creator": "...",
      "published": "...",
      "url": "..."
    }
  ]
}
```

---

## imgs.json

Generated automatically.

Indexes every supported image within the repository.

```json
{
  "updated_at": "...",
  "base_url": "...",
  "count": 14,
  "imgs": [
    "featured.png",
    "diagram.webp"
  ]
}
```

`base_url` is constructed using repository metadata supplied by GitHub Actions.

---

# RSS Compiler

`rss.py` performs the following process.

1. Read the RSS feed.
2. Parse publication metadata.
3. Read `content:encoded`.
4. Remove non-content HTML.
5. Remove images and captions.
6. Remove subscription widgets.
7. Remove related-post widgets.
8. Convert YouTube embeds into Markdown links.
9. Convert buttons into standard links.
10. Convert HTML into Markdown.
11. Normalize Markdown formatting.
12. Merge with previously stored posts.
13. Preserve historical posts.
14. Generate `posts.md`.
15. Generate `posts.json`.

For development, the compiler can consume a local RSS fixture.

```bash
python .github/scripts/rss.py --source docs/rss.sample.txt
```

---

# Image Compiler

`imgs.py` scans the repository image directory.

Supported formats include:

- PNG
- JPEG
- JPG
- WEBP
- GIF
- AVIF

The compiler generates `imgs.json` containing:

- update timestamp
- repository image base URL
- image count
- image filenames

---

# GitHub Actions

Publishing is performed entirely through GitHub Actions.

Workflow:

1. Checkout repository.
2. Install Python dependencies.
3. Execute `rss.py`.
4. Execute `imgs.py`.
5. Commit generated files if changes exist.
6. Push back to the triggering branch.

Repository owner, repository name and branch are provided through the GitHub Actions environment.

No branch names are hardcoded.

---

# Dependencies

```text
beautifulsoup4
markdownify
```

---

# Design Principles

- GitHub-first
- Backend-free
- Database-free
- Static knowledge only
- Human-readable outputs
- Fully reproducible
- LLM-optimised content
- Minimal generated artefacts

---

# Generated Outputs

| File | Source | Generated |
|------|--------|-----------|
| about.txt | Manual | No |
| posts.md | RSS compiler | Yes |
| posts.json | RSS compiler | Yes |
| imgs.json | Image compiler | Yes |

---

# Future Work

Potential future enhancements include:

- richer Markdown normalization
- audio/video normalization
- automatic excerpt generation
- semantic search indexes
- multiple publication support
- reusable compiler package for additional Substack-based knowledge bases