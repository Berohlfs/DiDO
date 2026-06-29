# DiDO MVP — Local validation brain (environment runbook)

> **Purpose:** the isolated brain that BLU-508–513 validation gates run against. Isolated from the shared Supabase so destructive gates (`schema use`, `sync --apply`, backfills) never touch shared state.
> **Status:** stood up 2026-06-29. Structural layer ready (keyless). Embedding + enrich pending API keys.

## What this is

A local `pglite` (embedded Postgres) gbrain brain living under a dedicated `GBRAIN_HOME`, seeded with a thin real slice of `ryan-data`. It is the verification target for the MVP milestone, run via the `lean-project` skill's Environment phase.

| | Shared brain (default) | Local validation brain |
|---|---|---|
| Home | `~/.gbrain` | `~/.gbrain-dido/.gbrain` |
| Engine | `postgres` (Supabase) | `pglite` (local file) |
| Selected by | no env var | `export GBRAIN_HOME="$HOME/.gbrain-dido"` |
| Data | team's 822 pages | 7 seed pages (ABStudios slice) |

**Isolation rule:** every command against the validation brain must be prefixed with `GBRAIN_HOME="$HOME/.gbrain-dido"`. Without it, gbrain falls back to `~/.gbrain` and the shared Supabase. Gates that mutate state must never run without this env var set.

## Reproduce from scratch

```sh
export GBRAIN_HOME="$HOME/.gbrain-dido"

# 1. Init the isolated local brain (creates ~/.gbrain-dido/.gbrain/brain.pglite)
gbrain init --pglite

# 2. Build the curated seed slice (one real client thread: ABStudios)
SEED="$HOME/.gbrain-dido/seed-sources"
mkdir -p "$SEED"
# copy a chronological spread of ABStudios meetings + a couple Cowork sessions from
# /Users/rr/dev/hackathon-dido/ryan-data, preserving <YYYY-MM-DD>/<title>.md layout
# (5 fellow-transcripts/*/0630-abstudios-sierra.md + 2 cowork/2026-03-17/*.md were used)

# 3. gbrain sync requires the source dir to be a git repo
( cd "$SEED" && git init -q && git add -A && git commit -q -m "seed: ABStudios slice + cowork" )

# 4. Register + import the source. --no-embed defers embeddings (no OpenAI key needed yet)
gbrain sources add abstudios-seed --path "$SEED" --name "ABStudios seed slice"
gbrain sync --source abstudios-seed --no-embed

# 5. Confirm
gbrain stats          # Pages: 7, Chunks: 218, Embedded: 0, By type: note: 7
```

## Current state (2026-06-29)

- 7 pages, 218 chunks. All typed `note` — the gbrain-base-v2 default, expected **before** BLU-508 applies the `dido-engagement` ontology.
- Embedded: 0 — deferred. Search and skill answers need embeddings.
- Seed source: `abstudios-seed` (isolated, non-federated) → `~/.gbrain-dido/seed-sources`.

## What still needs API keys

The structural layer (init, sync, and **all of BLU-508's schema gates** — `schema validate` / `lint --with-db` / `use` / `sync --apply`) is keyless and ready now. These need keys exported in the shell running gbrain:

| Capability | Key | Used by |
|---|---|---|
| Embeddings (`gbrain embed --stale`) | `OPENAI_API_KEY` | search; every skill that retrieves (BLU-511–513) |
| Enrich / typing / facts / `think` | `ANTHROPIC_API_KEY` | BLU-510 enrich step, BLU-509 derivation answers, skill outputs |

Once both are set: `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain embed --stale` to embed the seed, then the BLU-510 enrich step can file the `note` pages into typed `client`/`engagement`/`decision` pages.

## Gate cheat-sheet (point gates here)

```sh
source ~/.zshrc                           # non-interactive shells: load PATH + API keys
export GBRAIN_HOME="$HOME/.gbrain-dido"    # ALWAYS, for every gate
gbrain schema validate
gbrain schema lint --with-db
gbrain schema use dido-engagement
gbrain schema sync --apply
gbrain stats
```

API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) live in `~/.zshrc`; a non-interactive tool shell must `source ~/.zshrc` before gbrain, or enrich/embedding/skill commands fail with no key. Posture is authoring: gbrain gates are the verification, not unit tests.
