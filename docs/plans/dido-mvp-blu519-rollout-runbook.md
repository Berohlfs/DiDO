# BLU-519 — Shared-brain rollout runbook (rollback included)

> **Status:** COMPLETE — flip executed 2026-06-29 with explicit user go-ahead. `dido-engagement` is the active pack on the shared brain; `dido-consulting` doctor 10/10; zero pages retyped, zero data loss. Rollback path below is verified-by-inspection and ready if needed.
> **Target:** the SHARED production brain (default `~/.gbrain`, Supabase sa-east-1). No `GBRAIN_HOME`. Every command here mutates or reads shared state.

## What the shared brain actually contains (verified read-only, 2026-06-29)
- 822 pages / 14,684 chunks (all embedded). Active pack: `gbrain-base-v2 v1.0.0` (15 types / 14 verbs).
- Typed pages are a demo/other corpus, NOT the ryan-data ABStudios slice: `companies/{acme-co,snackably,guizin-maladeza}`, `people/{acme-cto,hamburguer-joe}`, `meetings/2026-06-{19-ai-team-standup,20-acme-kickoff}`, `resources/andrej-karpathy-youtube`. Searching the brain for "ABStudios Sierra platform" returns nothing. The 813 `source` pages are not the local ryan-data files re-ingested.
- Implication: this is real shared state, not a disposable mirror of local files. Treat the flip as a genuine production change.

## Backup (the safety net) — DONE
- Full markdown export: `gbrain export --dir "$HOME/gbrain-prod-backup-2026-06-29"` (run with `unset GBRAIN_HOME`). 822 pages; slow over the remote pooler (~20+ min).
- Active pack recorded for rollback: **`gbrain-base-v2`** (`gbrain schema active` → `Active pack: gbrain-base-v2 v1.0.0`, source `home-config`).

## Safe diagnostics — DONE, GREEN
1. Installed the pack locally, non-activating: `cp packs/dido-engagement/dido-engagement.yaml ~/.gbrain/schema-packs/dido-engagement/pack.yaml`. `gbrain schema list` shows it under "Installed packs"; active pack stayed `gbrain-base-v2` (install does NOT activate — `schema use` is what writes `~/.gbrain/config.json`).
2. `gbrain schema validate dido-engagement` → ✓ valid manifest, 10 page types, 11 link verbs, exit 0.
3. `gbrain schema lint dido-engagement --with-db` → **exit 0, warnings only, no errors.** The only findings are 7 `extractable_empty_corpus` warnings (stakeholder/client/engagement/deliverable/decision/risk/opportunity match 0 pages in the DB today — expected, nothing is filed under the dido prefixes yet). No conflicts with the `gbrain-base-v2` corpus; the base-lineage mismatch (pack extends `gbrain-base`, prod runs `gbrain-base-v2`) produced no error.

## Blast-radius notes (read before flipping)
- `gbrain schema use dido-engagement` writes **local** `~/.gbrain/config.json` (`schema_pack`). It changes the active pack for THIS machine's view of the shared brain; it does not edit teammates' local configs. Reversible with `gbrain schema use gbrain-base-v2` (or `schema downgrade`).
- `gbrain schema sync --apply` mutates the **shared DB** `page.type` column across matching pages — this is the team-visible, irreversible-feeling change. Backed by the export above. Because the dido prefixes match 0 current pages, a backfill today would retype **0 pages** (the lint corpus check proves this), so the immediate effect on the existing Acme/Snackably corpus is null until consulting data is filed under the dido prefixes. Confirm with a dry-run first.

## Flip — DONE (2026-06-29), all green
- `gbrain schema use dido-engagement` → active pack = `dido-engagement v1.0.0` (wrote `~/.gbrain/config.json`).
- `gbrain schema sync` (dry-run) → `would_apply=0` for all 10 types (dido prefixes match 0 existing pages).
- `gbrain schema sync --apply` → `applied=0` (no-op, as predicted — existing corpus untouched).
- `gbrain schema review-orphans` → **0 orphans** (all 822 pages still resolve under the active pack, since dido-engagement extends gbrain-base's company/person/concept/source/note types).
- `gbrain whoknows "ai model selection"` → `[]` (expected: no `stakeholder`/`expertise` pages in the demo corpus; Expertise Mapper gap-flags this).
- `gbrain skillpack doctor packs/dido-consulting --quick` → ★ 10/10 [endorsed].
- `gbrain stats` → Pages 822 / Chunks 14684 (unchanged — zero data loss).

## Reference: the steps as run (kept for re-run / audit)
```sh
source ~/.zshrc
unset GBRAIN_HOME                      # target the SHARED brain on purpose

# 4. Activate (local config; reversible)
gbrain schema use dido-engagement
gbrain schema active                  # expect: Active pack: dido-engagement v1.0.0

# 5. Dry-run the backfill FIRST (no --apply = DRY-RUN), inspect the plan
gbrain schema sync                     # shows would_apply counts; expect ~0 given empty corpus
# 6. Apply only if the dry-run is as expected
gbrain schema sync --apply

# 7. Spot-check nothing regressed
gbrain schema review-orphans
gbrain whoknows "ai model selection"
# (Client Brief etc. will gap-flag until real consulting data is filed)

# 8. Enable the skillpack on the shared brain, confirm doctor green
gbrain skillpack doctor packs/dido-consulting --quick   # expect 10/10
```

## Rollback
NOTE: `gbrain schema use gbrain-base-v2` is NOT reliable — `gbrain-base-v2` is the prod active pack via home-config but is NOT a name-resolvable pack on this install (`schema list` shows only gbrain-base + gbrain-recommended; `schema show gbrain-base-v2` → "Unknown pack"). Its source lives in the fork at `gbrain/src/core/schema-pack/base/gbrain-base-v2.yaml` but the installed CLI does not expose it to `use`/`show`/`extends`.
Use one of these instead, in order of preference:
```sh
unset GBRAIN_HOME
gbrain schema downgrade                  # restores the PREVIOUS active pack (the intended rollback)
gbrain schema active                     # confirm gbrain-base-v2 restored

# Fallback if downgrade can't resolve it: restore the config string directly.
# The resolver loaded "gbrain-base-v2" from config before the flip, so re-writing it reverts the lens.
#   edit ~/.gbrain/config.json: "schema_pack": "dido-engagement" -> "gbrain-base-v2"

# Data rollback is almost certainly unnecessary: sync --apply retyped 0 pages.
# Only if pages were ever retyped: gbrain export --restore-only --repo "$HOME/gbrain-prod-backup-2026-06-29"
```
To fully un-install the local pack: `rm -rf ~/.gbrain/schema-packs/dido-engagement`.

## Follow-ups surfaced
- The shared brain runs `gbrain-base-v2`; `dido-engagement` extends `gbrain-base`. Lint is clean today, but before the team relies on it, consider re-basing the pack on `gbrain-base-v2` so the two ontologies' shared types (person, company, meeting, concept) resolve identically. Capture as a follow-up ticket if the flip proceeds.
- The skillpack/pack source lives in the DiDO repo (`packs/`); activation only writes local config + the DB backfill. No `gbrain/src` change.
