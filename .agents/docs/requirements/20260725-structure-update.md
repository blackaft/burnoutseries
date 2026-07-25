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

[TO BE EDITED BY AI]