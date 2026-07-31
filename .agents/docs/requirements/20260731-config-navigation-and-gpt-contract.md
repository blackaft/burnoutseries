# Burnout Series — Config Navigation and GPT Contract Update

Date: 2026-07-31

## Purpose

Capture the July 31, 2026 decisions around moving guide-style navigation into `config.json` and tightening the GPT action contract for manifest retrieval.

## Final Decisions

### Config navigation

- `config.json` now exposes a structured `navigation` array.
- This replaces the older loose `links` placeholder.
- The navigation data should preserve descriptions, not just labels and URLs.
- The navigation structure is meant to help AI consumers understand:
  - what each channel is for
  - how it fits into the story or meta-story
  - which links are available now versus still coming soon
- `guide.md` remains a readable source document, but the repository-facing contract now lives in `config.json`.

### Navigation content rules

- Each navigation section should include a `title`.
- Each navigation section should include a `description`.
- When a section has entries, those entries should live under `items`.
- Each item should carry descriptive context, not only a channel name.
- Use `url` when a live link exists.
- Use `status` when the destination is not yet live, such as `coming soon`.
- Keep wording compact enough for AI consumption, but informative enough to preserve intent.

### Manifest exposure

- `manifest.json` should continue embedding `config` as-is.
- This means `config.navigation` becomes available to GPT actions and other AI consumers through `getManifest`.
- Schema samples should reflect this so downstream consumers can see the intended shape.

### GPT action contract

- The `getManifest` operation in `.agents/scripts/gpt.yml` must stay within the GPT action validator limits.
- The current `description` was shortened to stay under 300 characters.
- The shortened description must still preserve the manifest-first retrieval rule.
- The description should still make clear that:
  - the manifest is the first call for factual questions
  - `substack_url` should be used for post links
  - `base_url` plus `path` plus `file` is only for raw repository content

## Validation Notes

The following behaviors were verified during the session:

- `config.json` contains a structured `navigation` array.
- The manifest sample was updated to reflect `config.navigation`.
- The GPT action description for `getManifest` was reduced below the 300-character validator cap.

## Important Contracts For Future Sessions

- Do not collapse `config.navigation` back into a single freeform links field.
- Do not strip descriptions from navigation entries just to make the config shorter.
- Keep navigation useful for AI retrieval, not only for human reading.
- If `gpt.yml` descriptions are edited again, re-check validator limits before publishing.
- Keep `getManifest` focused on manifest-first orientation rather than turning it into a long endpoint explanation.
