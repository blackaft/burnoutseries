# Publishing Brief

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

The publish pipeline is deterministic, agent-agnostic, and idempotent. It treats Git as the database and Substack as the CMS.

```
Substack (content source)
    ↓
.humans/ (human-added files: images, .txt)
    ↓
.agents/scripts/main.py (orchestrator)
    ↓
Processors (imgs.py, rss.py, txt.py, manifest.py)
    ↓
.agents/vaults/ (durable indexed corpus)
    ↓
GitHub raw URLs → Custom GPT + retrieval clients
```

### The Orchestrator

Run `.agents/scripts/main.py` to orchestrate the processors:

- `processors/imgs.py` moves supported image files from `.humans/` into `.agents/vaults/imgs/` and regenerates `imgs.json`.
- `processors/rss.py` fetches the Substack RSS feed, stores it at `.agents/vaults/feed.rss`, generates per-post Markdown files, and regenerates `posts.json`.
- `processors/txt.py` scans existing Markdown files under `.agents/vaults/about/` and `.agents/vaults/excerpts/` and regenerates their JSON indexes.
- `processors/manifest.py` merges the generated vault indexes into `.agents/vaults/manifest.json`.

Each processor is isolated, reads from specific inputs, writes to specific outputs, and updates one or two JSON files. Processors import path constants from `main.py` rather than duplicating them.

### The Publishing Workflow

User runs `./publish.sh`:
1. Validates environment (Git, Python 3, GitHub CLI auth)
2. Creates or resumes a git branch for the update
3. Runs Python orchestrator (`main.py`)
4. Validates generated JSON
5. Commits, pushes, opens or resumes PR
6. Optionally merges and cleans up

No GitHub Actions. No external state. All logic is local and replayable.

### Audience-Facing Companions

Two AI companions are available for audiences to explore Burnout:

**Custom GPT** (OpenAI, persistent)
- Defined in `.agents/scripts/gpt.yml` (OpenAPI spec)
- Uses GPT Actions to call the repository-backed API
- Retrieves `manifest.json` first, then fetches post, about, or excerpt Markdown on demand
- Hosted in OpenAI's GPT store; requires no local setup
- Ideal for: User-facing, discoverable, persistent companion

**AI Companion** (Agent-agnostic, flexible)
- Defined in **.agents/COMPANION.md**
- Fetches the knowledge base directly from GitHub raw URLs during conversation
- Retrieves `manifest.json` first, then fetches content files on demand
- Works with any AI agent (Claude, Gemini, Codex, etc.)
- Ideal for: Developer workflows, experimentation, local use, integration with various AI platforms
- Setup: Copy the prompt from COMPANION.md into an AI conversation, then ask your first question

Both companions follow the same retrieval-first, manifest-focused approach. They differ only in platform and integration method.

## File Map

| Path | Purpose | Agent Guidance |
| --- | --- | --- |
| `README.md` | Human-facing project overview and update instructions | Read for broad context and publishing commands |
| `.agents/COMPANION.md` | AI companion behavior and retrieval rules | Copy to any AI conversation to enable the companion |
| `.humans/` | Human intake folder for new text and image sources | Treat as staging; do not assume it contains the complete corpus |
| `.agents/docs/requirements/` | Product and implementation notes | Read the latest dated file before changing the pipeline |
| `.agents/docs/prompts/20260725-custom-gpt.md` | Custom GPT behavior and retrieval rules | Update when GPT action or companion stance changes |
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

## Key Patterns and Contracts

### Processor Pattern
Each processor:
- Imports `MAIN` constants from `main.py`
- Reads from `.humans/` or vault sources
- Writes JSON + Markdown to `.agents/vaults/`
- Returns exit code 0 on success
- Can be extended or refactored; never hardcode paths

### Durable Vaults
Once content exists in `.agents/vaults/`, it is canonical:
- `.agents/vaults/posts/` contains generated Markdown from Substack
- `.agents/vaults/about/` and `.agents/vaults/excerpts/` contain durable story and context material
- `.agents/vaults/imgs/` contains image assets
- `.humans/` is an intake area; processors decide whether to copy or move

### Manifest-First Retrieval
`manifest.json` is the primary entrypoint for all retrieval clients:
- External tools (Custom GPT) read manifest first
- They then fetch full Markdown or images only when needed
- This keeps bandwidth and inference cost low
- Agents should never need to ingest the entire repository

### Validation
All vault outputs must pass validation:
- JSON files are valid (`python -m json.tool`)
- Required paths exist before and after processing
- No stale files left behind
- Schema compliance is checked before commit

## Agent Checklist

When starting work on this repo:

- [ ] Read this brief (PUBLISHER.md)
- [ ] Skim the latest `.agents/docs/requirements/` file
- [ ] Understand the specific task
- [ ] Check current state: `git status`, review relevant JSON, inspect vault files
- [ ] Make changes (edit files, run processors, update schemas as needed)
- [ ] Validate outputs (JSON, paths, end-to-end if instructed)
- [ ] Offer to run `publish.sh` when ready, or let the human decide

## Common Pitfalls to Avoid

- **Don't assume .humans/ is complete.** It's an intake area. The canonical corpus is in `.agents/vaults/`.
- **Don't hardcode paths.** Import from `main.py` or ask the user.
- **Don't delete vault files without reason.** If a post exists in `.agents/vaults/posts/`, it stays until explicitly removed.
- **Don't modify publish.sh unless you understand the full flow.** It orchestrates Git, Python, and validation in sequence; changes can break the pipeline.
- **Don't invent content.** Strictly process and retrieve; never hallucinate posts, dates, images, or claims.

## Tool Compatibility

This repo is designed for **agent-agnostic use**. It will work identically with:

- Codex + VS Code + Cline
- Gemini + VS Code + Cline
- Claude (via file tools, shell commands, and Python execution)
- Any other agent with file I/O and shell access

The system has no tool-specific state or dependencies. All logic is file-based, shell-based, and Python-based—portable across any capable agent environment.

---

## See Also

- **COMPANION.md** — Copy-paste prompt for using any AI as the Burnout companion
- **README.md** — Human-facing project overview
