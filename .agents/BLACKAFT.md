# Blackaft Agent Brief

This repository is the public knowledge base for **Burnout**, an experimental series by George Kary and Blackaft. It is built for humans who want to explore the series through AI companions, not for AI to replace the act of reading or watching the work.

The guiding idea is simple: the creative work remains human-authored, while AI helps with context retrieval, reflection, analysis, distribution, and post-consumption exploration.

## Vision

Burnout is both a story and a record of the thinking around the story. The repository exposes that material as a small, structured knowledge system so assistants can help audiences ask better questions, connect themes, inspect process notes, and navigate the available material without inventing context.

Treat the repo as an audience-facing corpus, not as a generic software package.

## Objective

Keep the knowledge base:

- easy for humans to update
- easy for AI agents to inspect
- stable for Custom GPT actions and raw GitHub retrieval
- conservative about factual claims
- explicit about provenance and generated artifacts

## Alignment Principles

- Human-authored content is the source. AI may process, organize, summarize, validate, and retrieve it.
- `.humans/` is an intake area, not the durable knowledge base.
- `.agents/vaults/` is the durable machine-readable corpus exposed to GPTs and other retrieval clients.
- Do not delete, move, or rewrite source material unless the processor behavior clearly requires it.
- Prefer manifest-first retrieval. `manifest.json` exists so agents do not need to ingest the entire repository.
- Keep generated JSON shapes consistent: top-level metadata, `base_url`, `count`, and `items` where applicable.
- Do not invent posts, dates, image references, authors, excerpts, or project claims.
- Preserve the Blackaft stance: human creative authorship, AI-assisted context and reflection.

## How It Works

The publish pipeline lives under `.agents/scripts/`.

Run `.agents/scripts/main.py` to orchestrate the processors:

- `processors/imgs.py` moves supported image files from `.humans/` into `.agents/vaults/imgs/` and regenerates `imgs.json`.
- `processors/rss.py` fetches the Substack RSS feed, stores it at `.agents/vaults/feed.rss`, generates per-post Markdown files, and regenerates `posts.json`.
- `processors/txt.py` scans existing Markdown files under `.agents/vaults/about/` and `.agents/vaults/excerpts/` and regenerates their JSON indexes.
- `processors/manifest.py` merges the generated vault indexes into `.agents/vaults/manifest.json`.

The Custom GPT action is defined in `.agents/scripts/gpt.yml`. It should use `manifest.json` as the first context call, then fetch post, about, or excerpt Markdown only when the conversation needs full content.

## File Map

| Path | Purpose | Agent Guidance |
| --- | --- | --- |
| `README.md` | Human-facing project overview and update instructions | Read for broad context and publishing commands |
| `.humans/` | Human intake folder for new text and image sources | Treat as staging; do not assume it contains the complete corpus |
| `.agents/docs/requirements/` | Product and implementation notes | Read the latest dated file before changing the pipeline |
| `.agents/docs/prompts/` | Custom GPT instruction drafts | Update when action behavior or companion stance changes |
| `.agents/schemas/` | JSON schema contracts for vault indexes | Keep aligned with generated JSON and samples |
| `.agents/scripts/main.py` | Orchestrator and shared constants | Put shared paths and common helpers here |
| `.agents/scripts/processors/` | Focused processors for each vault type | Keep processor-specific logic here; avoid duplicated path constants |
| `.agents/scripts/gpt.yml` | OpenAPI action spec for the Custom GPT | Keep manifest-first unless the retrieval model changes |
| `.agents/scripts/publish.sh` | Human-run publish workflow | Preserve existing flow unless explicitly asked to change it |
| `.agents/vaults/manifest.json` | Merged knowledge manifest | Primary AI entrypoint |
| `.agents/vaults/posts/` | Generated Markdown from Substack posts | Durable post content for retrieval |
| `.agents/vaults/about/` | Durable about/context Markdown | Use for project framing and philosophy |
| `.agents/vaults/excerpts/` | Durable story excerpt Markdown | Use for narrative and theme exploration |
| `.agents/vaults/imgs/` | Durable image assets | Use with `imgs.json` base URL to construct raw image links |

## Working Rules

Before making changes, inspect the latest requirements note and current generated JSON. When changing processors, run or mentally trace `main.py` end to end: images, RSS, text indexes, then manifest.

When in doubt, keep the durable vaults stable and update the indexes to reflect the vault contents. The goal is not to maximize automation; the goal is to keep the knowledge base trustworthy for audience-facing AI companions.
