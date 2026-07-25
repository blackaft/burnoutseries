# BLACKAFT Agent Guide

## Vision

Burnout Series is an experimental story and meta-project about the lies we tell ourselves, packaged as a structured, machine-readable knowledge base for humans and AI assistants.

This repository exists to make the project easy to explore, update, and distribute without turning the repo itself into a sprawling product surface.

## Objective

- Keep the published knowledge base synchronized with Substack.
- Preserve the story's spoiler philosophy and editorial tone.
- Make AI usage useful for retrieval, navigation, and context, not for inventing new project facts.
- Keep publishing deterministic and low-maintenance.

## Alignment Principles

- Treat the repository as the source of truth.
- Read the smallest useful set of files before making changes.
- Prefer factual updates over speculative rewrites.
- Preserve human-authored voice, structure, and intent.
- Do not expand the scope of the project unless the task explicitly asks for it.
- If a change affects publishing or content structure, verify the downstream impact on generated artifacts.

## How The Project Works

The project follows a simple pipeline:

1. Humans update `feed.rss` from Substack.
2. New images are added under `imgs/` when needed.
3. `publish.sh` regenerates the repository-backed knowledge outputs.
4. The generated artifacts are committed and pushed.
5. GPT Actions or other AI clients consume the repo as their knowledge source.

The key idea is that Substack publishes the content, and this repository organizes that content for reliable AI retrieval.

## What To Read First

| File | Purpose | When to open it |
|---|---|---|
| `README.md` | Project summary, publishing instructions, and external links | Start here for human context |
| `docs/PRD.md` | Product vision, architecture, and behavior rules | Before changing workflows or agent behavior |
| `manifest.json` | Canonical repo metadata and knowledge source mapping | Before working on AI setup or indexing |
| `posts.json` | Post index and latest-content pointer | Before discussing or modifying content discovery |
| `posts.md` | Canonical post corpus | Before making content-aware changes |
| `imgs.json` | Image index and base URL metadata | Before touching image discovery or references |
| `about.txt` | Background, narrative frame, and project summary | Before writing agent guidance or content summaries |
| `publish.sh` | Publishing workflow and validation logic | Before changing the update pipeline |

## Working Rules For Agents

- Do not load the entire repository unless the task truly needs it.
- Use the index files first, then open individual posts or assets only when required.
- Keep edits minimal and localized.
- If you add a new convention, document it here or in the nearest project doc.
- If a task involves publishing, confirm that generated files remain consistent with the repo’s metadata.

## File Map

| Path | Notes |
|---|---|
| `README.md` | User-facing entry point and update instructions |
| `about.txt` | Narrative summary and conceptual framing |
| `manifest.json` | Machine-readable project manifest |
| `posts.json` | Post discovery index |
| `posts.md` | Post corpus and readable content store |
| `imgs.json` | Image discovery index |
| `imgs/` | Source images referenced by the corpus |
| `feed.rss` | Substack feed snapshot used for regeneration |
| `docs/` | Product, schema, and policy docs |
| `scripts/` | Regeneration helpers for content indices |
| `publish.sh` | End-to-end publish workflow |

## Guardrails

- Avoid inventing repository facts.
- Avoid spoilers unless the user explicitly asks for them.
- Avoid broad refactors when a surgical change will do.
- Avoid changing generated outputs without understanding the source change.

