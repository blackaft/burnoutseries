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
- .agents/scripts/
- .agents/vaults/ is the knowledge base to be exposed to tools like the series's Custom GPT
    - about
    - excerpts, from the series's chapters including prologue and epilogue
    - imgs, with img files moved from .humans/ to here
    - posts, from the series's meta-posts (not chapters)
- .agents/AGENT.md contains a high-level mapping of this repository for future AI sessions

## Organisation

- Consider moving all processing python scripts under .agents/scripts/processing/, i.e. .agents/scripts/processing/rss.py instead of naming the files process-rss.py

# Functional Specifications

## Change imgs.py

We need to change .agents/scripts/imgs.py:

- To look for image files under .humans/.
- After collecting them, to move (not copy) these images under .agents/vaults/imgs/.
- To update .agents/vaults/imgs.json with the new path to be exposed via Github's raw content service.
- Keep the rest of the functionality, including appending to imgs.json, as is.
- Consider changing the script's name from imgs.py to process-images.py for consistency.
- Update .agents/scripts/publish.sh to reflect path changes for the image script.

## Change rss.py

We need to change .agents/scripts/rss.py:

- To actually curl the Substack RSS raw source itself, since we're going to be running this locally and there have been no firewall blocking detections locally from Substack itself.
- Add a function to also collect and excerpt of the post (the first 240 characters of the post). We'll need to update .agents/schemas/posts.schema.json to reflect the change.
- Change the current behavior from updating the posts's content into a single posts.md file to multiple .md files under .agents/vaults/posts/ with the filename being the slug of the post prepended by the date (i.e. 20260724-github-now-available.md)
- Change the post schema to reflect the addition of the md file on Github's raw content service alongside the source URL from Substack.
- Keep the rest of the functionality as is, including continuing to update .agents/vaults/posts.json
- Consider changing the script's name from rss.py to process-rss.py for consistency.
- Update .agents/scripts/publish.sh to reflect path changes for the rss script.

## Add process-txt.py

We need to add a new .agents/scripts/process-txt.py script:

- It will look for .txt files under .humans/, convert them into AI-first .md files with bare minimum content changes from the original human source, put them under .agents/vaults/about/ or .agents/vaults/excerpts/ depending on the prefix of the human source file (i.e. about-sources.txt) and once confirmed, delete the human source.
- It will also update .agents/vaults/about.json and .agents/vaults/excerpts.json; we'll need to create and verify a .agents/schemas/about.schema.json and .agents/schemas/excerpts.schema.json first.
- Update .agents/scripts/publish.sh to reflect the addition of this new script.

# Implementation Plan

[TO BE EDITED BY AI - REPLACE THIS WITH THE IMPLEMENTATION PLAN]