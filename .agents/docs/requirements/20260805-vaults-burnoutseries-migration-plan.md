# Burnout Series Vault Relocation Plan

Date: 2026-08-05

## Purpose

Define the migration from the legacy knowledge-base location at `.agents/vaults/` to the new canonical vault root at `vaults/burnoutseries/`, while adopting the clearer internal structure already implied by the working tree.

## Current State Observations

### Legacy corpus still exists under `.agents/vaults/`

The repository currently contains populated legacy assets under `.agents/vaults/`, including:

- `manifest.json`
- `about.json`
- `posts.json`
- `imgs.json`
- `about/*.md`
- `posts/*.md`
- `imgs/*`
- `feed.rss`

This means the old path is still the only populated and usable corpus root today.

### New destination tree already exists, but only as a skeleton

The repository also contains a new tree under `vaults/burnoutseries/`:

- `about/`
- `substack/articles/`
- `substack/imgs/`
- `manifests/manifest.json`
- `manifests/about.json`
- `manifests/settings.json`
- `manifests/substack-articles.json`
- `manifests/substack-imgs.json`

These files currently exist as placeholders rather than live generated outputs.

### Repository documentation is out of sync with the intended direction

`README.md`, the active prompt instructions under `.agents/docs/prompts/`, and prior requirements documents still describe `.agents/vaults/` as the canonical retrieval surface.

This first iteration does not need to rewrite past progressive artifacts exhaustively. Human-facing and machine-facing fixed artifacts can be cleaned up more broadly in a second iteration as part of the later transformation into an AI-agent skill.

### Processing implementation should be created as part of this migration

The docs describe a processor architecture under `.agents/scripts/`, but that directory is not present in the current working tree.

For this migration, `.agents/scripts/` should be created as part of the implementation rather than treated as an external dependency.

## Target State

`vaults/burnoutseries/` becomes the canonical vault root for this repository.

The target structure should be:

```text
api/
  burnoutseries/
    about/
      project.json
      story.json
      creator.json
    substack/
      articles.json
      imgs.json
    index.json
vaults/
  burnoutseries/
    about/
    substack/
      articles/
      imgs/
    vault.json
```

## Structural Contract

### Vault identifier

- `burnoutseries` is the vault key for this repository.
- Future repositories should follow the same pattern: `vaults/<vault-id>/`.

### Content partitions

- `about/` holds durable markdown context files about the project, people, or framing.
- `substack/articles/` holds durable markdown generated from or aligned with Substack posts.
- `substack/imgs/` holds durable image assets associated with Substack/article content.
- `api/burnoutseries/` holds machine-readable JSON surfaces for AI consumers and tooling.
- `vault.json` holds vault-level metadata and settings.

### API naming

The new structure is more explicit if JSON surfaces are grouped by domain:

- `api/burnoutseries/index.json` as the top-level AI entrypoint
- `vault.json` for vault-level metadata and navigation/config
- `api/burnoutseries/about/project.json`, `story.json`, and `creator.json` for segmented about material
- `api/burnoutseries/substack/articles.json` for article metadata and content pointers
- `api/burnoutseries/substack/imgs.json` for image discovery

This makes the domain boundaries clearer than the flatter legacy names `posts.json`, `imgs.json`, and `manifest.json`.

## Migration Goals

1. Make `vaults/burnoutseries/` the only canonical retrieval surface.
2. Replace legacy `.agents/vaults/` references across active docs, prompts, and client contracts where needed for this iteration.
3. Align naming and directory boundaries with the new clearer vault structure.
4. Keep AI consumers on an index-first retrieval model.
5. Re-run the publication process after migration instead of preserving the current generated outputs verbatim.

## Proposed Migration Phases

### Phase 1: Lock the destination contract

Before moving files, confirm and document:

- whether `vault.json` fully replaces the old embedded `config` contract or continues to be embedded inside `api/burnoutseries/index.json`
- whether `substack/articles/` is the permanent replacement for legacy `posts/`
- whether `substack/imgs/` is the permanent replacement for legacy `imgs/`
- whether `api/about/project.json`, `story.json`, and `creator.json` are generated from distinct sources or split from a common source
- whether any `excerpts/` surface still exists in the future architecture or is now intentionally removed

Deliverable:

- this requirements document becomes the contract for the move

### Phase 2: Map legacy assets to new destinations

Create an explicit one-to-one mapping from legacy paths to new paths:

- `.agents/vaults/about/*.md` -> `vaults/burnoutseries/about/*.md`
- `.agents/vaults/posts/*.md` -> `vaults/burnoutseries/substack/articles/*.md`
- `.agents/vaults/imgs/*` -> `vaults/burnoutseries/substack/imgs/*`
- `.agents/vaults/about.json` -> split into `api/burnoutseries/about/project.json`, `story.json`, and `creator.json` as required by the new contract
- `.agents/vaults/posts.json` -> `api/burnoutseries/substack/articles.json`
- `.agents/vaults/imgs.json` -> `api/burnoutseries/substack/imgs.json`
- `.agents/vaults/manifest.json` -> `api/burnoutseries/index.json`
- legacy embedded config/settings -> `vaults/burnoutseries/vault.json`
- `.agents/vaults/feed.rss` -> either `vaults/burnoutseries/substack/feed.rss` or removal if RSS caching is no longer part of the published vault contract

Deliverable:

- a migration matrix checked into docs or embedded in implementation notes

### Phase 3: Redefine the API contract

Update the JSON contract so that retrieval clients no longer depend on `.agents/vaults/` semantics.

Minimum expectations:

- `api/burnoutseries/index.json` remains the first read for AI clients
- index paths point into `vaults/burnoutseries/`
- item references use the new directory layout
- raw content URLs are derived from the new root, not the legacy one

Key design decision:

- prefer storing logical `path` values like `about/` and `substack/articles/` instead of hardcoded full URLs inside every section, then derive public raw URLs consistently from repository metadata

### Phase 4: Move content and regenerate API outputs

Once the contract is fixed:

- move markdown and image assets into the new tree
- regenerate `api/burnoutseries/about/*.json`, `api/burnoutseries/substack/articles.json`, `api/burnoutseries/substack/imgs.json`, `api/burnoutseries/index.json`, and `vault.json`
- validate that every legacy file has an equivalent new location
- confirm that counts and item identifiers match or intentionally differ with documented reasons

Important rule:

- do not leave the new vault partially populated while consumers still point to the old one

### Phase 5: Update retrieval and publishing surfaces

Every retrieval-facing or maintenance-facing surface must be updated:

- `README.md`
- active prompt docs under `.agents/docs/prompts/`
- active requirements docs that still describe `.agents/vaults/` as canonical
- active prompt docs or GPT contracts that reference raw GitHub paths
- any OpenAPI or action schema files that currently point at `.agents/vaults/...`

This phase must also include:

- creating `.agents/scripts/`
- adding or restoring the publish/generation scripts needed for the new vault structure
- updating those scripts to emit into `vaults/burnoutseries/`

### Phase 6: Introduce a compatibility window

For a short migration window, allow one of these strategies:

- keep `.agents/vaults/` as a deprecated mirror generated from the new vault, or
- switch all clients atomically and remove the old path immediately

Recommended approach:

- use a short-lived compatibility mirror only if active external consumers already depend on `.agents/vaults/` and cannot be updated in one release

If no active external consumer depends on the old paths, skip the mirror and cut over directly.

### Phase 7: Remove legacy assumptions

After cutover:

- remove or archive `.agents/vaults/`
- remove stale references from active docs
- remove any fields that only existed for old path compatibility
- ensure future requirements docs treat `vaults/<vault-id>/` as the only valid architecture

## Acceptance Criteria

The migration is complete when all of the following are true:

1. `api/burnoutseries/index.json` is the canonical AI entrypoint.
2. Durable markdown and image assets are generated under `vaults/burnoutseries/` by the new publication flow.
3. No primary documentation still instructs users or tools to read from `.agents/vaults/`.
4. Any generation or publish flow writes to `vaults/burnoutseries/`, not `.agents/vaults/`.
5. Raw GitHub URLs and API pointers resolve correctly from the new structure.
6. Legacy `.agents/vaults/` is either removed or clearly marked deprecated and non-canonical.

## Risks

### Implementation bootstrap risk

The current checkout does not contain the `.agents/scripts/` architecture described by the docs. Because this migration now includes creating that layer, the risk is not missing discovery but making incorrect assumptions about the intended generation workflow while bootstrapping it.

### Contract drift

The repo currently has documented contracts for `posts.json`, `imgs.json`, and `.agents/vaults/manifest.json`. Replacing these with `api/burnoutseries/substack/articles.json`, `api/burnoutseries/substack/imgs.json`, and `api/burnoutseries/index.json` will break clients unless all active retrieval surfaces are updated together.

### Partial migration risk

Because the new vault currently exists only as placeholders, there is a risk of moving docs first, content second, and generation code later. That would leave the repository in a misleading state. The cutover should be atomic at the contract level.

## Open Questions

1. Should `vault.json` be embedded into `api/burnoutseries/index.json`, or fetched separately by clients?
2. Should `feed.rss` remain a tracked artifact in the new vault structure?
3. Is `excerpts/` intentionally removed from the future architecture, or simply not created yet under `vaults/burnoutseries/`?
4. What is the intended source split for `api/about/project.json`, `story.json`, and `creator.json`?

## Recommended Execution Order

1. Resolve the open questions above.
2. Finalize the new API and `vault.json` contract.
3. Create `.agents/scripts/` and the publication flow for the new structure.
4. Move durable assets into `vaults/burnoutseries/`.
5. Regenerate API outputs.
6. Update active documentation and GPT/action contracts.
7. Remove or deprecate `.agents/vaults/`.

## Recommendation

Treat this change as a contract migration, not a folder move. The repository already shows three distinct states at once:

- legacy populated vault under `.agents/vaults/`
- new empty vault skeleton under `vaults/burnoutseries/`
- documentation still pointing to the legacy contract

The safest path is to first lock the new `api/` and `vault.json` contract, then build the publication layer, then migrate content and generation together, and only then remove the legacy path.
