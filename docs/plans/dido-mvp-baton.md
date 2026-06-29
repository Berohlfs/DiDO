# Baton — dido-mvp

- milestone: MVP — Store Intelligently (Linear milestone `df3ce41c`, project DiDO)
- branch: ryan/dido-mvp
- namespace: dido-mvp
- posture: authoring  # gbrain validation gates are the verification, not unit tests
- validation target: docs/plans/dido-mvp-environment.md — isolated from shared/prod? **yes** (`GBRAIN_HOME="$HOME/.gbrain-dido"`, local pglite, NOT the shared Supabase)

## Run conventions (every gbrain command for 508–513)
- Prefix with `GBRAIN_HOME="$HOME/.gbrain-dido"` (else hits shared Supabase brain).
- `source ~/.zshrc` first in any non-interactive shell (PATH + ANTHROPIC_API_KEY + OPENAI_API_KEY).
- BLU-519 is the EXCEPTION: it targets the shared brain on purpose — do NOT set GBRAIN_HOME; still `source ~/.zshrc`.
- Verified at kickoff: gbrain 0.42.53.0; validation brain = 7 pages / 218 chunks / 218 embedded; both keys set.

## Tickets (the DAG / wave order)
- wave 1: BLU-508 — Author + activate `dido-engagement` schema pack (ontology)
- wave 2: BLU-510 — Capture, filing, and provenance (enrich step)
- wave 3: BLU-509 — Client lifecycle status (derived, with override)
- wave 4: BLU-511, BLU-512, BLU-513 — `dido-consulting` skillpack (logically parallel; run sequentially for clean per-ticket commits — 511 scaffolds the pack first)
- wave 5: BLU-519 — Promote pack + skillpack to the SHARED production brain (gated on 508–513 green)
- depends-on edges: 510→508; 509→{508,510}; 511→{508,510}; 512→{508,510}; 513→{508,510}; 519→{508,509,510,511,512,513}

## Slice-first directive (from execution plan §5 + user)
Prove the loop end-to-end before authoring breadth: 508 (ontology) → 510 files ONE artifact → 509 derives status → ONE skill (Client Brief, in 511) returns a grounded cited answer. Early checkpoint inside 508/510: confirm `frontmatter_links` edges materialize in the direction skills expect (each edge points the way its field points; reverse via backlinks) BEFORE authoring skills.

## Pointers
- execution plan: docs/mvp-execution-plan.md  (Run conventions block + §3 tables + §5)
- headline facts: docs/mvp-execution-plan.md §1 (5 facts) — carried into the brief
- proposal (templates): docs/consulting-brain-proposal.md (§7 ontology, §8 lifecycle, §10 decision template)
- environment runbook: docs/plans/dido-mvp-environment.md
- brief: docs/research/dido-mvp-brief.md  (DONE — reuse shapes + 5 verified facts + confirmed CLI flags)
- plan: docs/plans/dido-mvp-plan.md  (DONE — per-ticket gates + acceptance; 510 & 511 marked complex → thin spec)
- tracker: docs/plans/dido-mvp-tracker.md  (DONE)

## Decisions
- (none yet — ADRs accrue during execution)

## Phase log
- P0 Kickoff: done → this baton; branch ryan/dido-mvp cut; 7 tickets imported from Linear
- P1 Environment: done (pre-provisioned) → docs/plans/dido-mvp-environment.md (validation brain reachable + embedded, verified at kickoff)
- P3 Plan: done → docs/plans/dido-mvp-plan.md + tracker. Complex (thin spec): BLU-510, BLU-511. 509 build-time TODO: confirm exact filter-by-frontmatter path (`gbrain query` vs `search --types`).
- P2 Brief: done → docs/research/dido-mvp-brief.md. Key corrections for builders: `gbrain_min_version` 3/4-part (0.42 fails, use 0.42.0); `primitive` is closed 5-enum; pack `frontmatter_links` `{page_type,fields,link_type}` has NO inverse and NO direction (edge always declaring→referenced, reverse via backlinks); doctor needs BOTH `routing-eval.jsonl` (≥5) AND `evals/*.judge.json` (≥3); `type:` frontmatter beats slug prefix; `sync --apply` defaults to DRY-RUN (must pass --apply); CyclePhase is a closed 22-member union → 509 must be a skill. Edge-direction checkpoint: `gbrain graph engagements/<slug> --depth 1` + `gbrain backlinks clients/<slug>`.

## Ticket log (mirrors the tracker, kept terse)
- BLU-508: TODO  (wave 1, opus, authoring, has-new-ui: false)
- BLU-510: TODO  (wave 2, opus, authoring, has-new-ui: false)
- BLU-509: TODO  (wave 3, opus, authoring, has-new-ui: false)
- BLU-511: TODO  (wave 4, opus, authoring, has-new-ui: false)
- BLU-512: TODO  (wave 4, opus, authoring, has-new-ui: false)
- BLU-513: TODO  (wave 4, opus, authoring, has-new-ui: false)
- BLU-519: TODO  (wave 5, opus, authoring, has-new-ui: false) — targets SHARED brain, no GBRAIN_HOME

## Open questions / escalations
- (none)
