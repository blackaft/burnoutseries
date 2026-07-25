# Burnout Series @Blackaft

![Target Audience](https://img.shields.io/badge/Target_Audience-Humans-FF5722?style=flat-square&logo=userpilot&logoColor=white)

This repository is a knowledge base meant for audiences using AI companions to consume content.

Ping [George Kary](https://github.com/geogkary) on Google Chat for help.

Follow on [X](https://x.com/blackaftx) for updates.

## A few words

**BURNOUT** is an experimental series about the bullshit lies we tell ourselves, spanning 3 parts and 19 chapters, complemented by videos, author's notes and behind-the-scenes content by George Kary. It was born out of a passion for exploring multi-disciplinary and cross-functional projects, and, of course, a love of storytelling.

A major aspect of the experiment is the use of AI in both the creation of the project (strictly for research, analysis and retrospectives) and the distribution of its knowledge base. Rather than asking audiences to navigate dozens of articles, the series publishes a structured, machine-readable corpus that can be explored through AI assistants, coding agents or any application capable of ingesting external context, whether through knowledge uploads, raw files or programmatic retrieval.

## Using this knowledge base

If you're looking to build your own AI setup, take a look or point your AI to `.agents/BLACKAFT.md`.

Ready to use:

- [ChatGPT](https://chatgpt.com/g/g-6a61ca759b788191babe096fc2c19e58-burnout-series) (Custom GPT)

## Updating it

Under `.humans/`, add any new

- Image, using filenames that match the relevant post or subject (for example, `process-of-experimentation-featured.png`).
- Text files, by prepending whether they're an about or excerpt item (i.e. `about-summary.txt`)

Publish the update:

<details>
    <summary>Run the command on the terminal yourself</summary>

```bash
chmod +x .agents/scripts/publish.sh
./.agents/scripts/publish.sh
```
</details>
<details>
    <summary>Prompt your AI to do it</summary>

```markdown
Publish this knowledge base update by running `./.agents/scripts/publish.sh` and following any prompts the script presents. If the script reports an error, stop and show me the complete output instead of trying to work around it.
```
</details>

## Links

### Substack

- [Home](https://burnoutseries.substack.com/)
- [Prologue](https://burnoutseries.substack.com/p/prologue)
- [Chapters](https://burnoutseries.substack.com/p/chapters)
    - [Part One: Dissonance](https://burnoutseries.substack.com/t/part-one)
    - [Part Two: Resonance](https://burnoutseries.substack.com/t/part-two)
    - [Part Three: Convergence](https://burnoutseries.substack.com/t/part-three)
    - [All chapters](https://burnoutseries.substack.com/t/chapters)
- [Meta](https://burnoutseries.substack.com/p/meta)
    - [Schedule updates on the series](https://burnoutseries.substack.com/t/update)
    - [Notes by George Kary](https://burnoutseries.substack.com/t/authors-notes)
    - [Behind the scenes with George Kary](https://burnoutseries.substack.com/t/behind-the-scenes)
    - [Materials and guides](https://burnoutseries.substack.com/t/materials-and-guides)
    - [Videos](https://burnoutseries.substack.com/t/videos)
    - [About](https://burnoutseries.substack.com/about)
- [RSS](https://burnoutseries.substack.com/feed.rss)

### George Kary

- [Substack](https://substack.com/@georgekary)
- [Instagram](https://www.instagram.com/georgekary_)
- [YouTube](https://www.youtube.com/@georgekary)

### Thanos Doumas

- [Substack](https://substack.com/@thanosd)
- [Instagram](https://www.instagram.com/thanos_do/)

---

*Created and maintained together with AI. This software is protected and distributed by the [PolyForm Shield License 1.0.0](LICENSE.md). Badges by [shields.io](https://github.com/badges/shields).*
