---
id: "github-now-available"
title: "Github, now available"
excerpt: "BURNOUT embraces AI strictly for analysis, distribution in some parts and post-consumption, not consumption. Put your ass down and read, like humans used to before 2023. That means, the series does not use AI to generate any kind of content"
created_by: "George Kary"
published_at: "2026-07-24T18:26:08Z"
substack_url: "https://burnoutseries.substack.com/p/github-now-available"
file: "20260724-github-now-available.md"
---

BURNOUT embraces AI strictly for analysis, distribution in some parts and post-consumption, not consumption. Put your ass down and read, like humans used to before 2023. That means, the series does not use AI to generate any kind of content for the series itself, including scripts, multimedia and posts on Substack. Those are made by humans, for humans. But, in this day and age, using AI to interact with any kind of material absolutely makes sense.

So, let’s distribute context for AI next to content for humans.

Follow the experiment.

Subscribe now

The new repository is agnostic, in terms of AI setups. While it’s currently working for the series’s Custom GPT in strictly production terms, the repository was tested with isolated ChatGPT sessions, Codex, Claude and a BYOK setup including VS Code + Cline for the agentic management.

That means, if you don’t prefer GPT, you can use the repository’s manifest - and even the repository itself by forking it - to set up your own stream for the series.

It’s essentially a workflow, with a very rudimentary advent of RAG principles.

This is, of course, in alignment with Blackaft’s principle of distributing content from and to AI, acknowledging that humans use AI to consume, anyway.

Feel free to fork the repo on Github and experiment yourself.

Whereas the workflow so far for the series’s custom GPT included manually updating relevant files on the GPT, the new workflow is programmatic.

Now, the process is much more simple:

Humans publish on Substack and append the updated RSS feed, including any additional images or contextual changes to the repository

Humans or their AIs can run a robust publishing script

All done - Custom GPT and all AIs hooking to the series’s stream have the new context, using Github’s own raw content service

A deterministic publishing workflow on a BYOK setup, ft. VS Code and Cline.

Why is the first step still manual?

We ran into firewall issues with Substack, since their images are served via CDN to avoid violent scrapes, and the RSS is, we gathered, blocked programmatically.

A natural solution to that would be to use Apify’s built-in Substack scrapers.

But hey, we ain’t gonna pay that much for a measly experiment!

Continue with the project’s preloaded ChatGPT.

Explore your thoughts

Huh?
