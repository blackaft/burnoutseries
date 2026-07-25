Closes issue #8 on Github

# Vision & Objectives

Organise the repository in a more lean and robust manner, so that:

- .agents/ includes the engine in an AI friendly manner
- .humans/ remains the source of truth for any .txt and img files added by humans (to be processed as part of this knowledge base's logic)
- root only contains docs, including the PRIVACY.md for the Custom GPT 

# Architecture (.agents/)

Keep in mind structural changes have already been initiated on the local working branch.

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

# Technical Specifications

## Images

We need to change .agents/scripts/imgs.py:

- To look for image files under .humans/.
- After collecting them, to move (not copy) these images under .agents/vaults/imgs/.
- To update .agents/vaults/imgs.json with the new path to be exposed via Github's raw content service.
- Keep the rest of the functionality, including appending to imgs.json, as is.
- Consider changing the script's name from imgs.py to process-images.py for consistency.
- Update .agents/scripts/publish.sh to reflect path changes for the image script.

# Implementation Plan

To be edited by AI, as part of analysis phase.