# Burnout Series GPT — Product Requirements Document

## Vision

The Burnout Series GPT is the primary interface through which readers explore the Burnout Series.

Rather than replacing the series, it complements it by helping readers navigate, connect and discuss the project's evolving story, meta and production process.

The GPT should feel like a knowledgeable companion—not a search engine or a chatbot.

---

## Product goals

- Ground every factual answer in the published Burnout Series knowledge base.
- Keep knowledge continuously synchronized with Substack.
- Encourage exploration rather than passive summarization.
- Preserve the project's spoiler philosophy.
- Require minimal maintenance.

---

## Architecture

```text
Substack
    │
feed.rss
    │
publish.sh
    │
───────────────
rss.py
imgs.py
───────────────
    │
posts.md
posts.json
imgs.json
about.txt
    │
GitHub
    │
GPT Actions
    │
Burnout Series GPT
```

---

## Knowledge sources

The GPT retrieves knowledge through repository-backed actions.

| Source | Purpose |
|---------|----------|
| posts.json | latest post discovery, metadata, navigation |
| posts.md | complete knowledge base |
| imgs.json | image discovery and metadata |
| about.txt | project background |

The repository is the authoritative source.

---

## Publishing workflow

Updating the GPT requires one command.

1. Replace `feed.rss`.
2. Add any new images to `imgs/`.
3. Run:

```bash
./publish.sh
```

The script:

- validates inputs
- regenerates knowledge
- creates/resumes a branch
- commits
- pushes
- opens/resumes a PR
- optionally merges
- restores a clean local repository

No GitHub Actions are required.

---

## GPT behaviour

The GPT should:

- retrieve knowledge before answering
- identify the latest post
- cite relevant posts
- remain conversational
- avoid spoilers
- explore ideas instead of merely summarizing
- clearly distinguish repository facts from reasoning

---

## Design principles

- Git is the database.
- Substack is the CMS.
- The repository is the knowledge base.
- AI retrieves knowledge rather than memorizing it.
- Publishing should be deterministic.
- Every generated artifact should be reproducible.
- Maintenance should require as little human effort as possible.

---

## Future roadmap

### Images

Improve image retrieval through richer metadata:

- descriptions
- captions
- tags
- related posts
- semantic context

### Visual reasoning

Allow the GPT to identify the most relevant project image before requesting visual inspection.

### Additional knowledge

Potential future indices:

- videos
- trailers
- excerpts
- timeline
- glossary
- behind-the-scenes references

---

## Success criteria

The system is considered successful if:

- updating knowledge requires a single command;
- the GPT always retrieves the latest published content;
- repository history remains auditable;
- the GPT never invents repository facts;
- readers experience the GPT as an extension of the series rather than a detached assistant.