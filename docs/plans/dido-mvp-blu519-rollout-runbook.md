# BLU-519 — Shared-brain rollout runbook (rollback included)

> **Status:** SAFE-PREP COMPLETE, STOPPED before the flip (per user decision 2026-06-29).
> The reversible diagnostics ran green; the two mutating steps (`schema use`, `schema sync --apply`) are NOT yet run and need an explicit human go-ahead.
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

## Remaining steps — NOT YET RUN (need explicit go-ahead)
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
```sh
unset GBRAIN_HOME
gbrain schema use gbrain-base-v2        # restore the previous active pack (or: gbrain schema downgrade)
gbrain schema active                    # confirm gbrain-base-v2 restored
# If sync --apply had retyped pages, restore them from the export:
gbrain export --restore-only --repo "$HOME/gbrain-prod-backup-2026-06-29"
```
To fully un-install the local pack: `rm -rf ~/.gbrain/schema-packs/dido-engagement`.

## Follow-ups surfaced
- The shared brain runs `gbrain-base-v2`; `dido-engagement` extends `gbrain-base`. Lint is clean today, but before the team relies on it, consider re-basing the pack on `gbrain-base-v2` so the two ontologies' shared types (person, company, meeting, concept) resolve identically. Capture as a follow-up ticket if the flip proceeds.
- The skillpack/pack source lives in the DiDO repo (`packs/`); activation only writes local config + the DB backfill. No `gbrain/src` change.
