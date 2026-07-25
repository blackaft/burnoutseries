Closes issue #8 on Github

# Vision & Objectives

Organise the repository in a more lean and robust manner, so that:

- .agents/ includes the engine in an AI friendly manner
- .humans/ remains the source of truth for any .txt and img files added by humans (to be processed as part of this knowledge base's logic)
- root only contains docs, including the PRIVACY.md for the Custom GPT 

# Non-functional Specifications

## Architecture (.agents/)

Keep in mind structural changes have already been initiated on the local working branch (and committed locally).

- .agents/docs/ contains requirements and samples
    - requirements, with the former PRD.md moved here
    - samples, for reference
- .agents/schemas/ contains references/samples of schemas for .agents/vaults/
- .agents/scripts/ contains the processing and publish entrypoints
- .agents/vaults/ is the knowledge base to be exposed to tools like the series's Custom GPT
    - about
    - excerpts, from the series's chapters including prologue and epilogue
    - imgs, with img files moved from .humans/ to here
    - posts, from the series's meta-posts (not chapters)
- .agents/AGENT.md contains a high-level mapping of this repository for future AI sessions

## Organisation

- Consider moving all processing python scripts under `.agents/scripts/processing/`, i.e. `.agents/scripts/processing/rss.py` instead of naming the files `process-rss.py`

# Functional Specifications

## Change imgs.py

We need to change `.agents/scripts/imgs.py`:

- To look for image files under .humans/.
- After collecting them, to move (not copy) these images under .agents/vaults/imgs/.
- To update `.agents/vaults/imgs.json` with the new path to be exposed via GitHub's raw content service.
- Keep the rest of the functionality, including appending to imgs.json, as is.
- Consider changing the script's name from `imgs.py` to `process-images.py` for consistency.
- Update `.agents/scripts/publish.sh` to reflect path changes for the image script.

## Change rss.py

We need to change `.agents/scripts/rss.py`:

- To actually curl the Substack RSS raw source itself, since we're going to be running this locally and there have been no firewall blocking detections locally from Substack itself.
- Add a function to also collect an excerpt of the post (the first 240 characters of the post). We'll need to update `.agents/schemas/posts.schema.json` to reflect the change.
- Change the current behavior from updating the post's content into a single `posts.md` file to multiple `.md` files under `.agents/vaults/posts/` with the filename being the slug of the post prepended by the date (i.e. `20260724-github-now-available.md`).
- Change the post schema to reflect the addition of the `.md` file on GitHub's raw content service alongside the source URL from Substack.
- Keep the rest of the functionality as is, including continuing to update `.agents/vaults/posts.json`.
- Consider changing the script's name from `rss.py` to `process-rss.py` for consistency.
- Update `.agents/scripts/publish.sh` to reflect path changes for the RSS script.

## Add process-txt.py

We need to add a new `.agents/scripts/process-txt.py` script:

- It will look for `.txt` files under `.humans/`, convert them into AI-first `.md` files with bare minimum content changes from the original human source, put them under `.agents/vaults/about/` or `.agents/vaults/excerpts/` depending on the prefix of the human source file (i.e. `about-sources.txt`) and once confirmed, delete the human source.
- It will also update `.agents/vaults/about.json` and `.agents/vaults/excerpts.json`; we'll need to create and verify `.agents/schemas/about.schema.json` and `.agents/schemas/excerpts.schema.json` first.
- Update `.agents/scripts/publish.sh` to reflect the addition of this new script.

# Implementation Plan

## Phase 1: Lock the new layout contract

1. Confirm the canonical directories and naming:
   - `.agents/` for agent-facing docs, schemas, scripts, and vaults
   - `.humans/` for human-authored source inputs only
   - `.agents/vaults/` for generated knowledge assets exposed through raw GitHub content
2. Add or update `.agents/AGENT.md` to explain the repository map, read order, and file ownership rules.
3. Update `README.md` so every publish instruction, file reference, and human-facing path matches the new structure.
4. Keep root-level content minimal and document-only where possible.

## Phase 2: Define the schema layer

1. Update `.agents/schemas/posts.schema.json` for the new post excerpt field and per-post markdown artifact reference.
2. Create `.agents/schemas/about.schema.json` and `.agents/schemas/excerpts.schema.json`.
3. Verify the schemas describe the generated vault outputs rather than the human source files.
4. Preserve backward-compatible metadata where it still helps downstream consumers.

## Phase 3: Rework image processing

1. Update `.agents/scripts/imgs.py` so it reads image sources from `.humans/`.
2. Move image files into `.agents/vaults/imgs/` as part of processing, rather than copying them.
3. Regenerate `.agents/vaults/imgs.json` so it points at the GitHub raw-content paths for the vault copies.
4. Preserve existing image discovery behavior and any current index fields that remain valid.
5. Rename the script only if the rest of the pipeline is updated in the same change set.

## Phase 4: Rework RSS processing

1. Update `.agents/scripts/rss.py` so it fetches the Substack RSS source directly.
2. Generate one markdown file per post under `.agents/vaults/posts/`, using `YYYYMMDD-slug.md` filenames.
3. Add a short excerpt field for each post, based on the first 240 characters of the post content.
4. Continue updating `.agents/vaults/posts.json` as the primary navigation index.
5. Update any repository references so the new per-post markdown files are discoverable and stable.

## Phase 5: Add TXT processing

1. Add `.agents/scripts/process-txt.py` for human-authored `.txt` sources under `.humans/`.
2. Route `about-*` sources into `.agents/vaults/about/` and `excerpts-*` sources into `.agents/vaults/excerpts/`.
3. Convert each source into an AI-first `.md` artifact with minimal content changes.
4. Update `.agents/vaults/about.json` and `.agents/vaults/excerpts.json`.
5. Only delete the original `.humans/` source after the generated vault artifact and index update are confirmed.

## Phase 6: Orchestrate the publish flow

1. Update `.agents/scripts/publish.sh` to run the image, RSS, and TXT processors in the correct order.
2. Keep the publish script deterministic and safe to rerun.
3. Ensure the script validates source presence before destructive moves or deletes.
4. Keep the current branch/commit/push workflow intact unless the new layout explicitly changes it.

## Phase 7: Verify and clean up

1. Run the publish flow against the populated `.humans/` inputs.
2. Check that generated vault files, schemas, and indexes are internally consistent.
3. Confirm the root README and all `.agents/` references point at the new paths.
4. Remove any obsolete references to the old root-level scripts or flat corpus files once the new structure is proven stable.

# Retrospective (incl. notes on QA/UAT iterations)

## Session Summary

Issue #8 became a broader product and engineering pass over the repository's agent-facing structure. The work started as a folder reorganization and grew into a more explicit knowledge-base architecture for Burnout's audience-facing AI companion.

The final direction was to treat the repository as a structured corpus rather than a collection of loose files. Human inputs can still enter through `.humans/`, but the durable retrieval surface now lives under `.agents/vaults/`, with `manifest.json` as the primary context entrypoint for GPT actions and future AI agents.

## Product Decisions

The repository should support a Custom GPT and other AI clients that help audiences explore Burnout, not merely summarize it. That changed the shape of the deliverable:

- The corpus needs to be navigable without ingesting the whole repository.
- The manifest should provide enough metadata for first-pass orientation.
- Full Markdown content should be fetched only when the conversation needs it.
- Image references matter as part of the series' authored context, not as decorative attachments.
- The project framing needs to stay explicit: human-authored creative work, AI-assisted retrieval, reflection, and distribution.

The Custom GPT prompt was rewritten around this stance. It now describes the GPT as an AI companion for audiences exploring their thoughts through the series, with manifest-first retrieval, selective drill-down, and conversational responses that mention post links and relevant image references when posts are referenced.

## Final Architecture

The accepted layout is:

- `.humans/` for human intake files.
- `.agents/docs/` for requirements, prompts, and samples.
- `.agents/schemas/` for JSON schemas and schema samples.
- `.agents/scripts/` for the orchestrator, processors, OpenAPI spec, and publish workflow.
- `.agents/vaults/` for durable knowledge artifacts exposed through raw GitHub URLs.

The processor architecture is now:

- `.agents/scripts/main.py` owns shared constants, paths, raw GitHub URL helpers, validation, and processor orchestration.
- `.agents/scripts/processors/imgs.py` handles image relocation from `.humans/` to `.agents/vaults/imgs/` and regenerates `imgs.json`.
- `.agents/scripts/processors/rss.py` fetches Substack RSS, caches it under `.agents/vaults/feed.rss`, generates post Markdown files, and regenerates `posts.json`.
- `.agents/scripts/processors/txt.py` scans `.agents/vaults/about/` and `.agents/vaults/excerpts/` Markdown files to regenerate `about.json` and `excerpts.json`.
- `.agents/scripts/processors/manifest.py` merges the generated JSON indexes into `.agents/vaults/manifest.json`.

The key architectural correction near the end of the session was changing TXT indexing to scan the durable vault Markdown files, not only `.humans/`. This prevents `about.json`, `excerpts.json`, and `manifest.json` from losing entries when the original human intake `.txt` files are removed after conversion.

## Schema and JSON Decisions

The vault JSON outputs were aligned around a consistent shape:

- `updated_at`
- `base_url`
- `count`
- `items`

`posts.json` additionally includes `latest`. Post item metadata now includes:

- `id`
- `title`
- `excerpt`
- `created_by`
- `published_at`
- `substack_url`
- `file`

`about.json` and `excerpts.json` item metadata includes:

- `id`
- `excerpt`
- `published_at`
- `file`

`imgs.json` exposes:

- `updated_at`
- `base_url`
- `count`
- `items`

`manifest.json` merges:

- `posts`
- `about`
- `excerpts`
- `imgs`

Schema samples under `.agents/schemas/samples/` were treated as the truth source for JSON shape. The schemas and processors were updated to match those samples.

## OpenAPI and Custom GPT Decisions

The GPT action spec moved from many index calls to a manifest-first model:

- `getManifest` retrieves `.agents/vaults/manifest.json`.
- `getPostsContent` retrieves individual post Markdown.
- `getSeriesAbout` retrieves individual about Markdown.
- `getExcerptContent` retrieves individual excerpt Markdown.

Standalone JSON index endpoints for posts, about, excerpts, and images were deprecated from `gpt.yml`, but the schema definitions remain because the manifest schema references them.

The OpenAPI metadata was rewritten to make the action purpose clearer: this is an AI companion knowledge base for Burnout audiences. It retrieves about material, story excerpts, image assets, and Substack post metadata from the Burnout GitHub repository for context-aware conversation and analysis.

## Publish Flow Decisions

The original `publish.sh` flow was intentionally preserved where possible. The script should remain familiar and human-runnable, with path updates and Python entrypoint updates rather than an unnecessary rewrite.

Important changes and fixes:

- The Python entrypoint now runs the orchestrator rather than individual legacy scripts.
- Root-level `feed.rss` is no longer required.
- RSS is fetched directly by `rss.py` with `curl -v -fsSL`.
- The fetched RSS source is stored under `.agents/vaults/feed.rss`.
- Publish validation paths were corrected to account for the script running from `.agents/scripts/`.
- JSON review now validates vault paths such as `../vaults/posts.json`, not root-level `posts.json`.

The PR body and merge-message work was partially explored. A deterministic publish summary was added to `publish.sh`, but Copilot-driven prose generation was deferred because `gh copilot` is currently a shell-assistant CLI surface rather than a reliable PR-description prose generator for this workflow.

## QA and UAT Notes

Running `main.py` directly confirmed the orchestrator and processor import flow, but the Codex sandbox initially hit a local filesystem write restriction while moving images into `.agents/vaults/imgs/`. Running the same command from the user's terminal succeeded, which confirmed the code path was valid and the earlier failure was environment-level.

During publish testing, several stale root-relative assumptions surfaced:

- `publish.sh` still expected `feed.rss` at the repository root.
- `publish.sh` still validated `posts.json` and `imgs.json` as root-level files.
- After updating the validation paths to `.agents/vaults/...`, the script still failed because it runs from `.agents/scripts/`, making those paths incorrect at runtime.

Those were corrected by removing the root feed validation and using paths relative to `.agents/scripts/` for generated vault JSON validation.

Another UAT issue appeared after `.humans/about-*` and `.humans/excerpts-*` files were removed. The generated about and excerpts indexes no longer included existing vault Markdown. This exposed a flawed assumption in `txt.py`: it was indexing intake sources instead of durable vault content. The processor was changed to scan `.agents/vaults/about/*.md` and `.agents/vaults/excerpts/*.md` directly.

## Important Behavioral Contracts

Future agents should preserve these behaviors unless the product direction changes:

- `manifest.json` is the primary AI entrypoint.
- Vault Markdown files are durable corpus artifacts.
- `.humans/` is an intake area, not the canonical index source.
- `main.py` owns shared paths and common helpers.
- Processors should call `MAIN.*` constants directly rather than redefining path aliases.
- `rss.py` should fetch and cache RSS under `.agents/vaults/feed.rss`.
- The GPT prompt should instruct the companion to include post links and relevant image references whenever it references a post.
- Raw GitHub URLs should resolve against the default branch, currently expected to be `dev`.

## Follow-Up Considerations

Possible future improvements:

- Add validation for `about.json`, `excerpts.json`, `posts.json`, `imgs.json`, and `manifest.json` against the schemas during publish.
- Add a richer image-to-post mapping instead of relying on filename inference or prompt behavior.
- Add explicit `images` metadata to post items when a reliable association rule exists.
- Add a generated `latest_post` convenience object to `manifest.json`.
- Revisit Copilot-assisted PR copy if GitHub exposes a stable non-interactive prose-generation surface suitable for shell automation.
- Decide whether `.agents/BLACKAFT.md` should replace or coexist with any older `.agents/AGENT.md` naming convention.
